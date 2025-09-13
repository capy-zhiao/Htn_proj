from typing import List, Dict, Any
import os
import json
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("ultra_simple_chat_logger")

def ensure_logs_directory():
    """Ensure the logs directory exists"""
    if not os.path.exists("chat_logs"):
        os.makedirs("chat_logs")

def extract_code_changes_from_conversation(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract code changes from conversation using simple pattern matching"""
    
    # Collect all code blocks from the conversation
    code_blocks = []
    file_mentions = set()
    
    for message in messages:
        content = message.get("content", "")
        role = message.get("role", "")
        
        # Look for file mentions
        file_patterns = [
            r'`([^`]+\.(html|js|py|ts|css|json|md))`',
            r'([a-zA-Z0-9_/]+\.(html|js|py|ts|css|json|md))',
            r'index\.html',
            r'app\.py',
            r'package\.json'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    file_mentions.add(match[0])
                else:
                    file_mentions.add(match)
        
        # Look for code blocks
        code_block_pattern = r'```(?:python|py|javascript|js|typescript|ts|html|css|json|bash|sh)?\n(.*?)```'
        code_matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        for code in code_matches:
            if len(code.strip()) > 20:  # Only consider substantial code blocks
                code_blocks.append({
                    "code": code.strip(),
                    "role": role,
                    "content": content[:100] + "..." if len(content) > 100 else content
                })
    
    # Analyze conversation for changes
    conversation_text = " ".join([msg.get("content", "") for msg in messages])
    
    # Determine change type
    change_type = "other"
    if "translate" in conversation_text.lower() or "翻译" in conversation_text:
        change_type = "function modify"
    elif "add" in conversation_text.lower() or "添加" in conversation_text:
        change_type = "function added"
    elif "remove" in conversation_text.lower() or "删除" in conversation_text or "remove" in conversation_text:
        change_type = "function modify"
    elif "fix" in conversation_text.lower() or "修复" in conversation_text:
        change_type = "bug fixed"
    
    # Generate title and description
    title = "Code Changes Detected"
    description = "Code modifications identified in conversation"
    
    if "index.html" in conversation_text.lower():
        if "translate" in conversation_text.lower() or "翻译" in conversation_text:
            title = "HTML Interface Translation"
            description = "Translated HTML interface from Chinese to English"
        elif "remove" in conversation_text.lower():
            title = "HTML Interface Cleanup"
            description = "Removed buttons and cleaned up HTML interface"
    
    # Extract before/after code if available
    before_code = ""
    after_code = ""
    
    if code_blocks:
        # Use the first substantial code block as after_code
        after_code = code_blocks[0]["code"]
        if len(code_blocks) > 1:
            before_code = code_blocks[1]["code"]
    
    # Generate summary
    summary = f"Conversation involved {change_type.replace('_', ' ')} with {len(file_mentions)} file(s) mentioned: {', '.join(list(file_mentions)[:3])}"
    if len(file_mentions) > 3:
        summary += f" and {len(file_mentions) - 3} more"
    
    return {
        "title": title,
        "description": description,
        "tag": change_type,
        "before_code": before_code,
        "after_code": after_code,
        "summary": summary,
        "files_mentioned": list(file_mentions),
        "code_blocks_found": len(code_blocks)
    }

@mcp.tool()
async def save_chat_history(messages: List[Dict[str, Any]], conversation_id: str = None, project_name: str = "MCP_Chat_Logger") -> str:
    """
    Save chat history with simple code change analysis
    
    Args:
        messages: List of chat messages, each containing role and content
        conversation_id: Optional conversation ID for file naming
        project_name: Project name for the conversation
    """
    ensure_logs_directory()
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_logs/conversation_{conversation_id}_{timestamp}.json" if conversation_id else f"chat_logs/conversation_{timestamp}.json"
    
    # Analyze the conversation
    analysis = extract_code_changes_from_conversation(messages)
    
    # Create conversation summary
    conversation_summary = {
        "conversation_id": conversation_id or f"conversation_{timestamp}",
        "project_name": project_name,
        "tag": analysis.get("tag", "other"),
        "description": analysis.get("description", ""),
        "before_code": analysis.get("before_code", ""),
        "after_code": analysis.get("after_code", ""),
        "title": analysis.get("title", ""),
        "summary": analysis.get("summary", ""),
        "message_count": len(messages),
        "participants": list(set([msg.get("role", "unknown") for msg in messages])),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "files_mentioned": analysis.get("files_mentioned", []),
        "code_blocks_found": analysis.get("code_blocks_found", 0),
        "messages": messages
    }
    
    # Save to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(conversation_summary, f, indent=2, ensure_ascii=False)
    
    return f"✅ Conversation saved to JSON file: {filename}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

