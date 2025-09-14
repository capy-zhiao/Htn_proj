from typing import List, Dict, Any, Optional, Tuple
import os
import json
import re
import uuid
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from mcp.server.fastmcp import FastMCP
from process import (
    get_type_from_tag,
    extract_functions,
    extract_bug_fixes,
    normalize_llm_type,
)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_THIS_DIR, ".env"))
mcp = FastMCP("chat_logger")


class ChatMessage(BaseModel):
    content: str
    timestamp: str
    type: str
    tags: List[str]
    ai_model: str
    before_code: str
    after_code: str

class ConversationSummary(BaseModel):
    id: str
    project_name: str
    title: str
    summary: str
    messages: List[ChatMessage]
    message_count: int

def ensure_logs_directory() -> None:
    out_dir = os.path.join(_THIS_DIR, "chat_logs")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
def require_gemini() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Put it in MCP_Chat_Logger/.env or export it in your shell."
        )
    genai.configure(api_key=api_key)
    return api_key

def summarize_conversation_with_gemini(messages: List[Dict[str, Any]]) -> Dict[str, str]:
    api_key = os.getenv("GEMINI_API_KEY").strip()
    if not api_key:
        return {"title": "Analysis Failed", "summary": "GEMINI_API_KEY not configured"}

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    conversation_text = "\n".join(f"{m.get('content','')}" for m in messages).strip()
    if not conversation_text:
        return {"title": "Empty Conversation", "summary": "No content to summarize."}


    prompt = f"""
        You are an expert technical summarizer. Analyze the programming conversation inside <CONVERSATION> and output JSON.

        <CONVERSATION>
        {conversation_text}
        </CONVERSATION>

        Respond with ONLY valid JSON:
        {{
        "title": "max 8 words capturing the main theme",
        "summary": "2-4 sentences; use **bold** for actions (modified/added/fixed/updated/created) and for key files/functions; focus on concrete outcomes"
        }}
    """.strip()

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.3")),
            "max_output_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "800")),
        },
    )
    text = getattr(response, "text", "")
    m = parse_json_payload(text)
    if not m:
        return {"title": "Analysis Failed", "summary": "Could not parse AI response."}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"title": "Analysis Failed", "summary": "Invalid JSON from model."}

def parse_json_payload(raw: str):
    import json, re
    for pattern in [
        r"```json\s*([\s\S]*?)```",
        r"```\s*([\s\S]*?)```",
        r"\{[\s\S]*?\}",
    ]:
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1) if "```" in pattern else m.group(0))
            except Exception:
                continue
    return None

def _parse_json_payload(raw: str) -> Optional[Dict[str, Any]]:
    # try fenced ```json
    m = re.search(r"```json\s*([\s\S]*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # try generic ```
    m = re.search(r"```\s*([\s\S]*?)```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # try first (non-greedy) {...}
    m = re.search(r"\{[\s\S]*?\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # direct parse last
    try:
        return json.loads(raw)
    except Exception:
        return None

def _extract_code_blocks(txt: str) -> Tuple[str, str]:
    """
    Returns (before_code, after_code) as STRINGS (possibly "")
    so that a non-Optional Pydantic model won't fail.
    """
    # collect all fenced code blocks
    blocks = re.findall(r"```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```", txt, re.DOTALL)
    blocks = [b.strip() for b in blocks if b.strip()]
    all_code = "\n\n".join(blocks) if blocks else ""

    before_code, after_code = "", ""

    # explicit before/after markers near code fences
    before_matches = re.findall(
        r"(?:^|\b)(?:before|old|original|current)\s*[:\-]*\s*```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```",
        txt, flags=re.IGNORECASE
    )
    after_matches = re.findall(
        r"(?:^|\b)(?:after|new|updated|changed|fixed)\s*[:\-]*\s*```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```",
        txt, flags=re.IGNORECASE
    )
    if before_matches:
        before_code = before_matches[0].strip()
    if after_matches:
        after_code = after_matches[0].strip()

    # heuristic: exactly two blocks + change-y words -> treat as before/after
    if len(blocks) == 2 and not before_code and not after_code:
        if any(k in txt.lower() for k in ["before", "after", "change", "update", "modify", "fix", "replace", "refactor"]):
            before_code, after_code = blocks[0], blocks[1]

    # search_replace old/new hints
    if not before_code and not after_code:
        old_match = re.search(r'old_string["\']?\s*[:=]\s*["\']?([\s\S]*?)["\']?(?:\s*,|\s*})', txt, re.IGNORECASE)
        new_match = re.search(r'new_string["\']?\s*[:=]\s*["\']?([\s\S]*?)["\']?(?:\s*,|\s*})', txt, re.IGNORECASE)
        if old_match:
            before_code = (old_match.group(1) or "").strip()
        if new_match:
            after_code = (new_match.group(1) or "").strip()

    # final safety: ensure strings
    return before_code or "", after_code or ""

# ----------------------------
# Semantic tags & type (no keywords)
# ----------------------------
def _semantic_tags_and_type(content: str) -> Tuple[List[str], str, List[str], List[str]]:
    """
    Use local semantic extractors to infer tags and a fallback 'type'.
    Returns (tags, fallback_type, feature_sentences, bugfix_sentences).
    """
    data_for_helpers = {
        "messages": [{"content": content}],
        "tag": "other",
        "description": content[:240],
    }
    feature_sentences = []
    bugfix_sentences = []
    try:
        feature_sentences = extract_functions(data_for_helpers, concept="feature_development") or []
    except Exception:
        pass
    try:
        bugfix_sentences = extract_bug_fixes(data_for_helpers, concept="bug_fix") or []
    except Exception:
        pass

    tags: List[str] = []
    if feature_sentences:
        tags.append("function modify")  # conservative default
    if bugfix_sentences:
        tags.append("bug fixed")

    # add conversational tag if strongly looks like a question/clarification
    lc = content.strip().lower()
    if not tags:
        if lc.endswith("?") or lc.startswith(("how ", "what ", "why ", "can ", "does ", "do ", "is ", "are ")):
            tags.append("question")
        else:
            tags.append("discussion")

    # derive fallback type (LLM may override)
    if "bug fixed" in tags:
        fallback_type = "code-change"
    elif "function modify" in tags:
        fallback_type = "code-change"
    elif "question" in tags:
        fallback_type = "question"
    else:
        fallback_type = "discussion"

    return tags, fallback_type, feature_sentences, bugfix_sentences


def analyze_individual_message_with_gemini(
    message: Dict[str, Any],
    *,
    use_llm: bool = True,
    prefer_semantics: bool = True,
) -> Dict[str, Any]:
    """
    Semantic-first message analyzer with optional Gemini assist.
    Always returns:
    {
      "content": str,
      "timestamp": str,
      "type": "code-change" | "question" | "clarification" | "discussion" | "parsing-failed" | "error" | "unknown",
      "tags": List[str],
      "before_code": str,
      "after_code": str,
      "ai_model": str,
      "enrichment": {
         "conventional_type": str,
         "feature_sentences": List[str],
         "bugfix_sentences": List[str],
         "keywords": List[str],               # uses semantic tags here (no KeyBERT)
      }
    }
    """
    content = str(message.get("content", "") or "")
    ts = str(message.get("timestamp", "") or "")

    # semantic pass (primary)
    sem_tags, sem_type, feature_sents, bugfix_sents = _semantic_tags_and_type(content)

    # code extraction from the message text
    before_code, after_code = _extract_code_blocks(content)

    # base result
    result: Dict[str, Any] = {
        "content": content,
        "timestamp": ts,
        "type": sem_type,               # semantic fallback; may be overridden by LLM below
        "tags": sem_tags[:],            # semantic tags are primary
        "before_code": before_code,
        "after_code": after_code,
        "ai_model": "N/A",
        "enrichment": {
            "conventional_type": get_type_from_tag(sem_tags[0] if sem_tags else "other"),
            "feature_sentences": feature_sents,
            "bugfix_sentences": bugfix_sents,
            "keywords": sem_tags[:],  # keep semantic tags as "keywords"
        },
    }

    # optional LLM assist
    if not use_llm:
        return result

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # no key -> keep purely semantic result
        return result

    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)

        prompt = f"""
You are a precise code analysis assistant. Analyze <MESSAGE_CONTENT> and return ONLY JSON with keys:
- "type": one of "code-change", "question", "clarification", "discussion"
- "tags": list of 0-3 short technical keywords
- "before_code": raw code for pre-change state if present
- "after_code": raw code for post-change state if present

<MESSAGE_CONTENT>
{content}
</MESSAGE_CONTENT>
""".strip()

        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 500},
        )

        # read text robustly
        text = getattr(response, "text", "") or ""
        if not text and getattr(response, "candidates", None):
            parts: List[str] = []
            for cand in response.candidates or []:
                cobj = getattr(cand, "content", None) or {}
                plist = getattr(cobj, "parts", None) or cobj.get("parts", []) or []
                for p in plist:
                    maybe = (p.get("text") if isinstance(p, dict) else getattr(p, "text", None))
                    if isinstance(maybe, str):
                        parts.append(maybe)
            text = "\n".join(parts).strip()

        if not text:
            # LLM gave nothing; keep semantic result
            return result

        parsed = _parse_json_payload(text)
        if not parsed:
            # unparseable; keep semantic result but mark type for visibility
            result["type"] = "parsing-failed"
            return result

        # merge LLM outputs
        llm_type = normalize_llm_type(parsed.get("type", result["type"]))
        llm_tags = parsed.get("tags", [])
        if not isinstance(llm_tags, list):
            llm_tags = []

        # prefer semantic tags; optionally union with LLM tags (dedup, length-bounded)
        if prefer_semantics:
            merged_tags = list(dict.fromkeys((result["tags"] or []) + [str(t) for t in llm_tags if t]))
        else:
            merged_tags = list(dict.fromkeys([str(t) for t in llm_tags if t] + (result["tags"] or [])))
        merged_tags = merged_tags[:6]  # cap

        # fill codes if LLM produced something better
        llm_before = parsed.get("before_code")
        llm_after = parsed.get("after_code")

        before_code_final = str((llm_before if llm_before is not None else result["before_code"]) or "")
        after_code_final = str((llm_after if llm_after is not None else result["after_code"]) or "")

        result.update({
            "type": llm_type or result["type"],
            "tags": merged_tags,
            "before_code": before_code_final,
            "after_code": after_code_final,
            "ai_model": model_name,
        })

        # refresh enrichment formatting if code changed
        result["enrichment"]["conventional_type"] = get_type_from_tag(
            merged_tags[0] if merged_tags else "other"
        )
        result["enrichment"]["keywords"] = merged_tags[:]
        return result

    except Exception as e:
        # keep semantic result, mark type for visibility
        result["type"] = "error"
        return result

@mcp.tool()
async def save_chat_history(
    messages: List[Dict[str, Any]],
    conversation_id: Optional[str] = None,
    project_name: str = "MCP_Chat_Logger",
    use_ai_analysis: bool = True,
) -> str:
    ensure_logs_directory()
    require_gemini()  # hard fail fast

    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # summarize conversation
    ai_analysis = summarize_conversation_with_gemini(messages)
    title = ai_analysis.get("title")
    summary = ai_analysis.get("summary")

    classified: List[ChatMessage] = []
    for raw in messages:
        analyzed = analyze_individual_message_with_gemini(raw)
        classified.append(ChatMessage(
            content=analyzed.get("content", ""),
            timestamp=analyzed.get("timestamp", ""),
            type=analyzed.get("type", "unknown"),
            tags=analyzed.get("tags", []) or [],
            ai_model=analyzed.get("ai_model", "N/A"),
            before_code=analyzed.get("before_code"),
            after_code=analyzed.get("after_code"),
        ))

    convo = ConversationSummary(
        id=conversation_id,
        project_name=project_name,
        title=title,
        summary=summary,
        messages=classified,
        message_count=len(classified),
    )

    # Save (include both 'id' and 'conversation_id' for frontend compatibility)
    payload = convo.model_dump()
    payload["conversation_id"] = payload["id"]
    out_path = os.path.join(_THIS_DIR, "chat_logs", f"conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return f"Conversation saved and fully processed to: {out_path}"

# ---- Entry ----
if __name__ == "__main__":
    mcp.run(transport="stdio")
