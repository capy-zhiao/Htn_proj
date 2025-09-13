#!/usr/bin/env python3
"""
Test MCP AI summary functionality
"""
import asyncio
from chat_logger import save_chat_history

async def test_mcp_ai():
    """Test MCP AI summary functionality"""
    
    print("=== Testing MCP AI Summary Functionality ===\n")
    
    # Test conversation about code improvement
    test_messages = [
        {
            "role": "user",
            "content": "这个目前的chat_logger.py并没有保存before and aftercode",
            "timestamp": "2025-09-13T14:18:24Z"
        },
        {
            "role": "assistant",
            "content": "您说得对！我查看了刚才保存的JSON文件，确实没有保存before_code和after_code。这是因为当前的AI总结功能只在对话中包含代码块时才会提取，而简单的\"save\"对话没有代码内容。\n\n让我检查一下当前的实现并改进它：",
            "timestamp": "2025-09-13T14:18:25Z"
        },
        {
            "role": "user",
            "content": "save",
            "timestamp": "2025-09-13T14:18:26Z"
        }
    ]
    
    print("Testing MCP AI summary with code improvement discussion...")
    result = await save_chat_history(
        messages=test_messages,
        conversation_id="mcp-ai-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ MCP AI summary testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_mcp_ai())
