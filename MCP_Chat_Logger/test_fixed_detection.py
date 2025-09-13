#!/usr/bin/env python3
"""
Test fixed code detection functionality
"""
import asyncio
from chat_logger import save_chat_history_with_cursor_changes

async def test_fixed_detection():
    """Test fixed code detection functionality"""
    
    print("=== Testing Fixed Code Detection ===\n")
    
    # Sample conversation with code changes (like our actual conversation)
    messages = [
        {
            "role": "user",
            "content": "你不能通过看cursor帮我修改了哪些代码自动手机before and after code吗",
            "timestamp": "2025-09-13T14:30:00Z"
        },
        {
            "role": "assistant",
            "content": "您说得对！我理解您的意思了。您希望我能够检测到在这次对话中我帮您修改了哪些代码，然后自动提取before和after代码。这确实是一个更实用的功能。\n\n让我修改代码检测器，让它能够检测当前对话中提到的代码变更，而不是依赖git：\n\n```python\nclass CursorCodeDetector:\n    \"\"\"Detects code changes from Cursor editor and conversation context\"\"\"\n    \n    def __init__(self, workspace_path: str = None):\n        self.workspace_path = workspace_path or os.getcwd()\n        self.git_path = os.path.join(self.workspace_path, '.git')\n```\n\n现在让我添加一个新的方法来检测对话中的代码变更：\n\n```python\ndef detect_conversation_code_changes(self, messages: List[Dict[str, any]]) -> Dict[str, any]:\n    \"\"\"Detect code changes from conversation messages\"\"\"\n    changes = {}\n    all_code_blocks = []\n    \n    # Collect all code blocks from the conversation\n    for message in messages:\n        content = message.get(\"content\", \"\")\n        role = message.get(\"role\", \"\")\n        \n        # Look for code blocks in the conversation\n        import re\n        code_blocks = re.findall(r'```(?:python|py|javascript|js|typescript|ts|java|cpp|c|html|css|sql|bash|sh)?\\n(.*?)```', content, re.DOTALL)\n        \n        for code_block in code_blocks:\n            code_block = code_block.strip()\n            if len(code_block) > 50:  # Only consider substantial code blocks\n                all_code_blocks.append({\n                    \"code\": code_block,\n                    \"role\": role,\n                    \"content\": content\n                })\n    \n    # Smart assignment of before/after code\n    if len(all_code_blocks) >= 2:\n        # If we have 2+ code blocks, use first as before, last as after\n        changes[\"before_code\"] = all_code_blocks[0][\"code\"]\n        changes[\"after_code\"] = all_code_blocks[-1][\"code\"]\n    elif len(all_code_blocks) == 1:\n        # If only one code block, check context to determine if it's before or after\n        code_block = all_code_blocks[0]\n        content = code_block[\"content\"].lower()\n        \n        # Look for keywords that suggest this is \"after\" code\n        after_keywords = [\"new\", \"updated\", \"modified\", \"fixed\", \"improved\", \"enhanced\", \"added\", \"created\"]\n        before_keywords = [\"old\", \"previous\", \"original\", \"before\", \"replaced\"]\n        \n        has_after_keywords = any(keyword in content for keyword in after_keywords)\n        has_before_keywords = any(keyword in content for keyword in before_keywords)\n        \n        if has_after_keywords and not has_before_keywords:\n            changes[\"after_code\"] = code_block[\"code\"]\n        elif has_before_keywords and not has_after_keywords:\n            changes[\"before_code\"] = code_block[\"code\"]\n        else:\n            # Default: treat as after_code (new implementation)\n            changes[\"after_code\"] = code_block[\"code\"]\n    \n    return changes\n```",
            "timestamp": "2025-09-13T14:30:15Z"
        }
    ]
    
    print("Testing with fixed code detection...")
    result = await save_chat_history_with_cursor_changes(
        messages=messages,
        conversation_id="fixed-detection-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Fixed detection testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_fixed_detection())
