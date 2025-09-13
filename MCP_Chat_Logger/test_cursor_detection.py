#!/usr/bin/env python3
"""
Test Cursor code detection functionality
"""
import asyncio
from chat_logger import save_chat_history_with_cursor_changes

async def test_cursor_detection():
    """Test Cursor code detection functionality"""
    
    print("=== Testing Cursor Code Detection ===\n")
    
    # Sample conversation
    messages = [
        {
            "role": "user",
            "content": "I just modified the chat_logger.py file to add Cursor code detection functionality",
            "timestamp": "2025-09-13T14:25:00Z"
        },
        {
            "role": "assistant",
            "content": "Great! I can see you've added the cursor_code_detector.py file and integrated it into chat_logger.py. This will automatically detect code changes from Cursor and extract before/after code.",
            "timestamp": "2025-09-13T14:25:15Z"
        }
    ]
    
    print("Testing with Cursor code detection...")
    result = await save_chat_history_with_cursor_changes(
        messages=messages,
        conversation_id="cursor-detection-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Cursor detection testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_cursor_detection())
