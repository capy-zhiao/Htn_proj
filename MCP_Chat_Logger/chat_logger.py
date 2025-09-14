from typing import List, Dict, Any, Optional, Tuple
import os
import json
import uuid
import re
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
from pydantic import BaseModel

# Local helpers (assumed correct per your note)
from process import (
    get_type_from_tag,
    extract_functions,
    extract_bug_fixes,
    extract_tags,
    format_code_changes,
)

# ---------------------------------------------------------------------
# env & server
# ---------------------------------------------------------------------
load_dotenv(find_dotenv())
mcp = FastMCP("chat_logger")

# ---------------------------------------------------------------------
# models
# ---------------------------------------------------------------------
class ChatMessage(BaseModel):
    content: str
    timestamp: str
    type: str                       # keep LLM type: "code-change" | "question" | "clarification" | "discussion" | ...
    tags: List[str]
    ai_model: str
    code_changes: Optional[str] = None
    before_code: Optional[str] = None
    after_code: Optional[str] = None

class ConversationSummary(BaseModel):
    id: str
    project_name: str
    title: str
    summary: str
    messages: List[ChatMessage]
    message_count: int

# ---------------------------------------------------------------------
# utils
# ---------------------------------------------------------------------
def ensure_logs_directory() -> None:
    if not os.path.exists("chat_logs"):
        os.makedirs("chat_logs")

# message-type (LLM) -> helper tag used by process.py
_TYPE_TO_TAG = {
    "code-change": "function modify",
    "question": "question",
    "clarification": "discussion",
    "discussion": "discussion",
    "unknown": "other",
    "parsing-failed": "other",
    "error": "other",
}

_ALLOWED_LLM_TYPES = {"code-change", "question", "clarification", "discussion"}

# ---------------------------------------------------------------------
# Gemini summarizer (conversation-level)
# ---------------------------------------------------------------------
def summarize_conversation_with_gemini(messages: List[Dict[str, Any]]) -> Dict[str, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"title": "Could not retrieve title", "summary": "Gemini API key not configured"}

    genai.configure(api_key=api_key)

    # Flatten conversation (content only is OK for a concise summary)
    conversation_text = "\n".join(f"{msg.get('content', '')}" for msg in messages)

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

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.3")),
                "max_output_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "800")),
            },
        )
        text = getattr(response, "text", "") or ""
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        return {"title": "Analysis Failed", "summary": "Could not parse AI response."}
    except Exception as e:
        return {"title": "Analysis Error", "summary": f"An exception occurred: {e}"}

# ---------------------------------------------------------------------
# Gemini analyzer (message-level)
# ---------------------------------------------------------------------
def analyze_individual_message_with_gemini(
    message: Dict[str, Any],
    *,
    do_enrichment: bool = True,
) -> Dict[str, Any]:
    """
    Returns:
    {
      "content": str,
      "timestamp": str,
      "type": "code-change" | "question" | "clarification" | "discussion" | "parsing-failed" | "error" | "unknown",
      "tags": List[str],
      "code_changes": Optional[str],
      "before_code": Optional[str],
      "after_code": Optional[str],
      "ai_model": str,
      "enrichment": {...}   # conventional_type, feature_sentences, bugfix_sentences, keywords, formatted_code_changes
    }
    """
    content: str = str(message.get("content", "") or "")
    ts: str = str(message.get("timestamp", "") or "")
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    result: Dict[str, Any] = {
        "content": content,
        "timestamp": ts,
        "type": "unknown",
        "tags": [],
        "code_changes": None,
        "before_code": None,
        "after_code": None,
        "ai_model": model_name if api_key else "N/A",
        "enrichment": {
            "conventional_type": "Other",
            "feature_sentences": [],
            "bugfix_sentences": [],
            "keywords": [],
            "formatted_code_changes": "// No code changes detected",
        },
    }

    def _extract_code_blocks(txt: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        # Gather all fenced blocks
        blocks = re.findall(r"```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```", txt, re.DOTALL)
        blocks = [b.strip() for b in blocks if b and b.strip()]
        if not blocks:
            return None, None, None

        all_code = "\n\n".join(blocks)
        before_code = None
        after_code = None

        # explicit before/after labels
        before_matches = re.findall(
            r"(?:^|\b)(?:before|old|original|current)\s*[:\-]*\s*```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```",
            txt,
            flags=re.IGNORECASE,
        )
        after_matches = re.findall(
            r"(?:^|\b)(?:after|new|updated|changed|fixed)\s*[:\-]*\s*```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```",
            txt,
            flags=re.IGNORECASE,
        )
        if before_matches:
            before_code = before_matches[0].strip()
        if after_matches:
            after_code = after_matches[0].strip()

        # exactly-two heuristic + change keywords
        if len(blocks) == 2 and not before_code and not after_code:
            if any(k in txt.lower() for k in ["before", "after", "change", "update", "modify", "fix", "replace", "refactor"]):
                before_code, after_code = blocks[0], blocks[1]

        # tool pattern (search_replace old/new)
        if not before_code and not after_code:
            old_match = re.search(r'old_string["\']?\s*[:=]\s*["\']?([\s\S]*?)["\']?(?:\s*,|\s*})', txt, re.IGNORECASE)
            new_match = re.search(r'new_string["\']?\s*[:=]\s*["\']?([\s\S]*?)["\']?(?:\s*,|\s*})', txt, re.IGNORECASE)
            if old_match:
                before_code = old_match.group(1).strip()
            if new_match:
                after_code = new_match.group(1).strip()

        return all_code, before_code, after_code

    def _parse_json_payload(raw: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw)
        except Exception:
            pass
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m = re.search(r"\{[\s\S]*?\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return None

    def _normalize_llm_type(v: Any) -> str:
        t = str(v or "").strip().lower().replace("_", "-")
        t = t.replace("code change", "code-change")
        return t if t in _ALLOWED_LLM_TYPES else "discussion"

    # No API key → still do local code extraction + enrichment
    if not api_key:
        code_changes, before_code, after_code = _extract_code_blocks(content)
        result.update({"code_changes": code_changes, "before_code": before_code, "after_code": after_code})
        return _attach_enrichment(result, content, result["type"], code_changes, before_code, after_code)

    # With API key → call Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = f"""
You are a precise code analysis assistant. Analyze the single message inside <MESSAGE_CONTENT> and output JSON.

<MESSAGE_CONTENT>
{content}
</MESSAGE_CONTENT>

Return ONLY JSON with keys:
- "type": one of "code-change", "question", "clarification", "discussion"
- "tags": list of 0-3 short technical keywords
- "code_changes": raw code (string) if any code blocks exist
- "before_code": raw code that represents the 'before' state if present
- "after_code": raw code that represents the 'after' state if present
""".strip()

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 500},
        )
        text = getattr(response, "text", "") or ""
        if not text:
            # stitch from candidates if needed
            parts: List[str] = []
            for cand in getattr(response, "candidates", []) or []:
                cobj = getattr(cand, "content", None) or {}
                plist = getattr(cobj, "parts", None) or cobj.get("parts", []) or []
                for p in plist:
                    maybe = (p.get("text") if isinstance(p, dict) else getattr(p, "text", None))
                    if isinstance(maybe, str):
                        parts.append(maybe)
            text = "\n".join(parts).strip()

        if not text:
            result["type"] = "parsing-failed"
            code_changes, before_code, after_code = _extract_code_blocks(content)
            result.update({"code_changes": code_changes, "before_code": before_code, "after_code": after_code})
            return _attach_enrichment(result, content, result["type"], code_changes, before_code, after_code)

        parsed = _parse_json_payload(text)
        if not parsed:
            result["type"] = "parsing-failed"
            code_changes, before_code, after_code = _extract_code_blocks(content)
            result.update({"code_changes": code_changes, "before_code": before_code, "after_code": after_code})
            return _attach_enrichment(result, content, result["type"], code_changes, before_code, after_code)

        msg_type = _normalize_llm_type(parsed.get("type", "discussion"))
        tags = parsed.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(t) for t in tags[:3] if t is not None]

        code_changes = parsed.get("code_changes")
        before_code = parsed.get("before_code")
        after_code = parsed.get("after_code")

        # Fallback extraction when LLM omitted code
        if not isinstance(code_changes, str) or not code_changes.strip() or (before_code is None and after_code is None):
            ext_all, ext_before, ext_after = _extract_code_blocks(content)
            if not code_changes:
                code_changes = ext_all
            if before_code is None:
                before_code = ext_before
            if after_code is None:
                after_code = ext_after

        result.update({
            "type": msg_type,
            "tags": tags,
            "code_changes": code_changes,
            "before_code": before_code,
            "after_code": after_code,
            "ai_model": model_name,
        })
        return _attach_enrichment(result, content, msg_type, code_changes, before_code, after_code)

    except Exception as e:
        result.update({
            "type": "error",
            "tags": [],
            "code_changes": f"An exception occurred: {e}",
            "before_code": None,
            "after_code": None,
        })
        return _attach_enrichment(result, content, "error", None, None, None)

# ---------------------------------------------------------------------
# enrichment
# ---------------------------------------------------------------------
def _attach_enrichment(
    base: Dict[str, Any],
    content: str,
    msg_type: str,
    code_changes: Optional[str],
    before_code: Optional[str],
    after_code: Optional[str],
) -> Dict[str, Any]:
    # choose a helper tag from the LLM-facing type
    tag_for_helpers = _TYPE_TO_TAG.get(msg_type, "other")
    conventional = get_type_from_tag(tag_for_helpers)  # -> 'feat' | 'fix' | 'chore' | 'security' | 'Other'

    data_for_helpers = {
        "messages": [{"content": content}],
        "tag": tag_for_helpers,
        "description": content[:280],
    }

    try:
        feature_sentences = extract_functions(data_for_helpers, concept="feature_development")
    except Exception:
        feature_sentences = []

    try:
        bugfix_sentences = extract_bug_fixes(data_for_helpers, concept="bug_fix")
    except Exception:
        bugfix_sentences = []

    try:
        keywords = extract_tags(data_for_helpers, top_n=6)
    except Exception:
        keywords = []

    try:
        formatted_cc = (
            format_code_changes(before_code, after_code)
            if (before_code or after_code)
            else (format_code_changes(None, code_changes) if code_changes else "// No code changes detected")
        )
    except Exception:
        formatted_cc = "// No code changes detected"

    base["enrichment"] = {
        "conventional_type": conventional,
        "feature_sentences": feature_sentences,
        "bugfix_sentences": bugfix_sentences,
        "keywords": keywords,
        "formatted_code_changes": formatted_cc,
    }
    return base

# ---------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------
@mcp.tool()
async def save_chat_history(
    messages: List[Dict[str, Any]],
    conversation_id: Optional[str] = None,
    project_name: str = "MCP_Chat_Logger",
    use_ai_analysis: bool = True,
) -> str:
    """
    Save chat history with AI analysis (summary + per-message classification).
    """
    ensure_logs_directory()

    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    ai_analysis = summarize_conversation_with_gemini(messages) if use_ai_analysis else {"title": "Chat Conversation", "summary": ""}

    title = ai_analysis.get("title") or "Chat Conversation"
    summary = ai_analysis.get("summary") or ""

    # classify each message
    classified: List[ChatMessage] = []
    for raw in messages:
        analyzed = analyze_individual_message_with_gemini(raw)

        # Build ChatMessage (strict shape)
        cm = ChatMessage(
            content=analyzed.get("content", ""),
            timestamp=analyzed.get("timestamp", ""),
            type=analyzed.get("type", "unknown"),
            tags=analyzed.get("tags", []) or [],
            ai_model=analyzed.get("ai_model", "N/A"),
            code_changes=analyzed.get("code_changes"),
            before_code=analyzed.get("before_code"),
            after_code=analyzed.get("after_code"),
        )
        classified.append(cm)

    conversation = ConversationSummary(
        id=conversation_id,
        project_name=project_name,
        title=title,
        summary=summary,
        messages=classified,
        message_count=len(classified),
    )

    filename = f"chat_logs/conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(conversation.model_dump_json(indent=2))

    return f"Conversation saved and fully processed to: {filename}"

# ---------------------------------------------------------------------
# server entry
# ---------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
