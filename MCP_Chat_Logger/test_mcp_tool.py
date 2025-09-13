#!/usr/bin/env python3
"""
Test MCP tool directly
"""
import asyncio
from simple_chat_logger import save_chat_history

async def test_mcp_tool():
    """Test the MCP tool directly"""
    
    # Sample conversation
    messages = [
        {
            "role": "user",
            "content": "为什么MCP不工作"
        },
        {
            "role": "assistant",
            "content": "让我检查一下MCP配置和工具的问题。问题可能是：1. MCP服务器没有正确启动 2. 工具名称不匹配 3. 依赖问题"
        }
    ]
    
    try:
        result = await save_chat_history(
            messages=messages,
            conversation_id="mcp-debug-test",
            project_name="HackTheNorth",
            use_ai_analysis=True
        )
        print("✅ MCP Tool Test Result:")
        print(result)
        return True
    except Exception as e:
        print(f"❌ MCP Tool Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_tool())
    if success:
        print("\n🎉 MCP tool is working correctly!")
    else:
        print("\n💥 MCP tool has issues!")

