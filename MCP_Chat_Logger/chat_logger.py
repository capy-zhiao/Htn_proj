from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
import uuid
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from process import (
    get_type_from_tag,
    extract_functions,
    extract_bug_fixes,
    extract_tags,
    format_code_changes,
)
import uuid

# Load environment variables from .env file
load_dotenv()
# Initialize FastMCP server
mcp = FastMCP("chat_logger")

# This model remains the same
class ChatMessage(BaseModel):
    content: str
    timestamp: str
    type: str
    tags: List[str]
    ai_model: str
    
# This is the updated model for the final, enriched data
class ConversationSummary(BaseModel):
    id: str
    project_name: str
    title: str
    summary: str
    messages: List[ChatMessage]
    message_count: int

def ensure_logs_directory():
    """Ensure the logs directory exists"""
    if not os.path.exists("chat_logs"):
        os.makedirs("chat_logs")

def summarize_conversation_with_gemini(messages: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Uses Gemini to generate a high-level title and summary for a conversation.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return {"title": "Chat Conversation", "summary": "Gemini API key not configured"}
    
    genai.configure(api_key=api_key)
    
    try:
        # 1. Simplified conversation formatting
        conversation_text = "\n".join(
            f"<{msg.get('role', 'unknown').upper()}> {msg.get('content', '')}"
            for msg in messages
        )

        # 2. Improved and focused prompt
        prompt = f"""
You are an expert technical summarizer. Your task is to analyze a programming conversation and generate a concise title and a detailed summary.

Analyze the conversation enclosed in the <CONVERSATION> tags.

<CONVERSATION>
{conversation_text}
</CONVERSATION>

Respond with ONLY a valid JSON object with the following keys:
- "title": A short, descriptive title for the entire conversation (5-10 words).
- "summary": A detailed paragraph summarizing the key problems, solutions, and outcomes.

Example Response:
{{
  "title": "Debugging a Null Pointer Exception in the User Authentication Module",
  "summary": "The conversation focused on resolving a persistent null pointer exception that occurred when users tried to log in with invalid credentials. The issue was traced to an uninitialized user profile object. The final solution involved adding a null check before accessing the object's properties, which stabilized the authentication flow."
}}
"""
        
        # 3. Call the model
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.3")),
                max_output_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "800"))
            )
        )
        
        # 4. Cleaned-up response parsing
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"⚠️ Warning: Could not parse JSON from Gemini response. Response was:\n{response.text}")
            return {"title": "Analysis Failed", "summary": "Could not parse AI response."}
            
    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        return {"title": "Analysis Error", "summary": f"An exception occurred: {e}"}


def to_chat_message_models(data) -> List[ChatMessage]:
    msgs = []
    for m in data.get("messages", []) or []:
        msgs.append(ChatMessage(
            content   = m.get("content", "") or "",
            timestamp = m.get("timestamp", "") or "",
            type      = m.get("type", "unknown") or "unknown",
            tags      = m.get("tags") or [],
            ai_model  = m.get("ai_model") or m.get("aiModel") or "N/A",
        ))
    return msgs

# map per-message LLM type -> your higher-level tag vocabulary
_TYPE_TO_TAG = {
    "code-change": "function modify",
    "question": "question",
    "clarification": "discussion",
    "discussion": "discussion",
    "unknown": "other",
    "parsing-failed": "other",
    "error": "other",
}


def analyze_individual_message_with_gemini(
    message: Dict[str, Any],
    *,
    do_enrichment: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a single chat message with Gemini and classify it, then enrich
    the result using local semantic helpers from `process`.

    Always returns this shape (plus an `enrichment` field):
    {
      "content": str,
      "timestamp": str,
      "type": "code-change" | "question" | "clarification" | "discussion" | "parsing-failed" | "error" | "unknown",
      "tags": List[str],
      "code_changes": Optional[str],
      "ai_model": str,
      "enrichment": {
          "conventional_type": str,
          "feature_sentences": List[str],
          "bugfix_sentences": List[str],
          "keywords": List[str],
          "formatted_code_changes": str
      }
    }
    """
    # ----- Inputs & defaults -----
    content: str = str(message.get("content", "") or "")
    ts: str = str(message.get("timestamp", "") or "")
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    allowed_types = {"code-change", "question", "clarification", "discussion"}

    # Base result
    result: Dict[str, Any] = {
        "content": content,
        "timestamp": ts,
        "type": "unknown",
        "tags": [],
        "code_changes": None,
        "ai_model": model_name if api_key else "N/A",
        "enrichment": {
            "conventional_type": "Other",
            "feature_sentences": [],
            "bugfix_sentences": [],
            "keywords": [],
            "formatted_code_changes": "// No code changes detected",
        },
    }

    # ---------- helpers ----------
    def _extract_code_blocks(txt: str) -> Optional[str]:
        """Join any fenced code blocks found in the text."""
        blocks = re.findall(r"```[a-zA-Z0-9_+\-#.\s]*\n([\s\S]*?)```", txt, re.DOTALL)
        blocks = [b.strip() for b in blocks if b and b.strip()]
        return "\n\n".join(blocks) if blocks else None

    def _parse_json_payload(raw: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from raw text, handling fenced ```json blocks."""
        # 1) direct
        try:
            return json.loads(raw)
        except Exception:
            pass
        # 2) fenced ```json ... ```
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # 3) first JSON-looking object (non-greedy)
        m = re.search(r"\{[\s\S]*?\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return None

    def _normalize_type(v: Any) -> str:
        """Normalize model-provided type into allowed set (default 'discussion')."""
        t = str(v or "").strip().lower()
        t = t.replace("_", "-").replace("code change", "code-change")
        return t if t in allowed_types else "discussion"

    # ----- If no API key: skip LLM but still do local enrichment -----
    if not api_key:
        msg_type = "unknown"
        code_changes = _extract_code_blocks(content)
        return _attach_enrichment(result, content, msg_type, code_changes)

    # ----- Configure Gemini -----
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    try:
        prompt = f"""
You are a precise code analysis assistant. Your task is to analyze a single chat message and classify it.

Analyze the message content enclosed in the <MESSAGE_CONTENT> tags.

<MESSAGE_CONTENT>
{content}
</MESSAGE_CONTENT>

Respond with ONLY a valid JSON object with the following keys:
- "type": Classify the message type. Must be one of: "code-change", "question", "clarification", "discussion".
- "tags": A JSON list of 1-3 relevant technical keywords or concepts from the message. If none, return an empty list.
- "code_changes": If a code block in any programming language is present, extract the raw code as a string.

Example Response:
{{
  "type": "code-change",
  "tags": ["python", "list comprehension", "refactor"],
  "code_changes": "before_code = [x for x in range(10)]\\nafter_code = [x*x for x in range(10)]"
}}
""".strip()

        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 500},
        )

        # Prefer .text; if missing (blocked/structured), assemble from candidates.
        text = getattr(response, "text", None)
        if not text:
            try:
                parts: List[str] = []
                for cand in getattr(response, "candidates", []) or []:
                    content_obj = getattr(cand, "content", None) or {}
                    parts_list = getattr(content_obj, "parts", None) or content_obj.get("parts", []) or []
                    for p in parts_list:
                        if isinstance(p, dict) and "text" in p:
                            parts.append(p["text"])
                        else:
                            maybe = getattr(p, "text", None)
                            if isinstance(maybe, str):
                                parts.append(maybe)
                text = "\n".join(parts).strip() if parts else ""
            except Exception:
                text = ""

        # Parse or fall back
        if not text:
            msg_type = "parsing-failed"
            code_changes = _extract_code_blocks(content)
            return _attach_enrichment(result, content, msg_type, code_changes)

        parsed = _parse_json_payload(text)
        if not parsed:
            msg_type = "parsing-failed"
            code_changes = _extract_code_blocks(content)
            return _attach_enrichment(result, content, msg_type, code_changes)

        # Normalize fields
        msg_type = _normalize_type(parsed.get("type", "discussion"))

        tags = parsed.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(t) for t in tags[:3] if t is not None]

        code_changes = parsed.get("code_changes")
        if not isinstance(code_changes, str) or not code_changes.strip():
            code_changes = _extract_code_blocks(content)

        result.update({
            "type": msg_type,
            "tags": tags,
            "code_changes": code_changes,
            "ai_model": model_name,
        })
        return _attach_enrichment(result, content, msg_type, code_changes)

    except Exception as e:
        result.update({
            "type": "error",
            "tags": [],
            "code_changes": f"An exception occurred: {e}",
        })
        return _attach_enrichment(result, content, "error", None)

def _attach_enrichment(
    base: Dict[str, Any],
    content: str,
    msg_type: str,
    code_changes: Optional[str],
) -> Dict[str, Any]:
    """
    Compute local semantic enrichment using your `process` helpers and
    attach it under base['enrichment'] without breaking core shape.
    """
    # Map per-message type -> your tag vocab (then to conventional type)
    tag_for_helpers = _TYPE_TO_TAG.get(msg_type, "other")
    conventional = get_type_from_tag(tag_for_helpers)

    # Build a minimal conversation-shaped payload for the helpers
    data = {
        "messages": [{"content": content}],
        "tag": tag_for_helpers,
        "description": content[:280],  # short description for keyword extraction
    }

    try:
        feature_sentences = extract_functions(data, concept="feature_development")
    except Exception:
        feature_sentences = []

    try:
        bugfix_sentences = extract_bug_fixes(data, concept="bug_fix")
    except Exception:
        bugfix_sentences = []

    try:
        keywords = extract_tags(data, top_n=6)
    except Exception:
        keywords = []

    try:
        formatted_cc = format_code_changes(None, code_changes) if code_changes else "// No code changes detected"
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


@mcp.tool()
async def save_chat_history(messages: List[Dict[str, Any]], conversation_id: str = None, 
                           project_name: str = "MCP_Chat_Logger", use_ai_analysis: bool = True) -> str:
    """
    Save chat history with AI analysis of the entire conversation
    """
    ensure_logs_directory()
    ai_analysis = summarize_conversation_with_gemini(messages)
    
    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    title = ai_analysis.get("title")
    summary = ai_analysis.get("summary")

    chat_messages = []
    for msg in messages:
        msg = analyze_individual_message_with_gemini(msg)
        chat_messages.append(ChatMessage(
            content=msg.get("content"),
            timestamp=msg.get("timestamp"),
            code_changes=msg.get("code_changes"),
            type=msg.get("type"),
            tags=msg.get("tags"),
            ai_model=msg.get("ai_model")
        ))
    
    # This now only contains high-level summary info
    conversation = ConversationSummary(
        id=conversation_id,
        project_name=project_name,
        title=title,
        summary=summary,
        messages=chat_messages,
        message_count=len(chat_messages),
    )
    
    # Save to JSON file
    filename = f"chat_logs/conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(conversation.model_dump_json(indent=2))
    
    return f"Conversation saved and fully processed to: {filename}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')