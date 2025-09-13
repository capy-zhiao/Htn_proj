#!/usr/bin/env python3
"""
Test conversation code detection functionality
"""
import asyncio
from chat_logger import save_chat_history_with_cursor_changes

async def test_conversation_detection():
    """Test conversation code detection functionality"""
    
    print("=== Testing Conversation Code Detection ===\n")
    
    # Sample conversation with code changes (like our actual conversation)
    messages = [
        {
            "role": "user",
            "content": "你不能通过看cursor帮我修改了哪些代码自动手机before and after code吗",
            "timestamp": "2025-09-13T14:30:00Z"
        },
        {
            "role": "assistant",
            "content": "您说得对！这是一个很好的想法。我可以创建一个功能来自动检测Cursor中的代码变更，并自动提取before和after代码。让我实现这个功能：\n\n```python\nclass CursorCodeDetector:\n    \"\"\"Detects code changes from Cursor editor\"\"\"\n    \n    def __init__(self, workspace_path: str = None):\n        self.workspace_path = workspace_path or os.getcwd()\n        self.git_path = os.path.join(self.workspace_path, '.git')\n```\n\n现在让我修改chat_logger.py，集成Cursor代码检测功能：\n\n```python\n@mcp.tool()\nasync def save_chat_history_with_cursor_changes(messages: List[Dict[str, Any]], conversation_id: str = None, \n                                               title: str = None, summary: str = None, \n                                               project_name: str = \"MCP_Chat_Logger\", tag: str = None, \n                                               description: str = \"\", save_to_db: bool = False, \n                                               save_to_file: bool = True, use_ai_summary: bool = True) -> str:\n    \"\"\"\n    Save chat history with automatic detection of Cursor code changes\n    \"\"\"\n    print(\"🔍 Detecting Cursor code changes...\")\n    \n    # Detect code changes from Cursor\n    cursor_changes = detect_cursor_changes()\n```",
            "timestamp": "2025-09-13T14:30:15Z"
        }
    ]
    
    print("Testing with conversation code detection...")
    result = await save_chat_history_with_cursor_changes(
        messages=messages,
        conversation_id="conversation-detection-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Conversation detection testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_conversation_detection())
