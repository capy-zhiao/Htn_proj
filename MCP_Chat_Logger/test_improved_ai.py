#!/usr/bin/env python3
"""
Test improved AI summary functionality
"""
import asyncio
import os
from chat_logger import save_chat_history

async def test_improved_ai():
    """Test improved AI summary functionality"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = "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"
    
    # Also set it in the config
    from config import config
    config.OPENAI_API_KEY = "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"
    
    print("=== Testing Improved AI Summary Functionality ===\n")
    
    # Test 1: Simple save request (no code)
    print("1. Testing simple save request (no code)...")
    simple_messages = [
        {"role": "user", "content": "save", "timestamp": "2025-09-13T14:16:33Z"},
        {"role": "assistant", "content": "我来使用MCP Chat Logger保存当前的对话：", "timestamp": "2025-09-13T14:16:34Z"}
    ]
    
    result = await save_chat_history(
        messages=simple_messages,
        conversation_id="improved-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Test 2: Code modification conversation
    print("2. Testing code modification conversation...")
    code_messages = [
        {"role": "user", "content": "I need to fix this function:\n```python\ndef old_function():\n    return None\n```", "timestamp": "2025-09-13T14:17:00Z"},
        {"role": "assistant", "content": "Here's the fixed version:\n```python\ndef new_function():\n    return 'Hello World'\n```", "timestamp": "2025-09-13T14:17:15Z"}
    ]
    
    result = await save_chat_history(
        messages=code_messages,
        conversation_id="improved-test-002",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Test 3: Question and discussion
    print("3. Testing question and discussion...")
    question_messages = [
        {"role": "user", "content": "What is the best way to handle errors in Python?", "timestamp": "2025-09-13T14:18:00Z"},
        {"role": "assistant", "content": "There are several ways to handle errors in Python. You can use try-except blocks, raise custom exceptions, or use logging for error tracking.", "timestamp": "2025-09-13T14:18:15Z"}
    ]
    
    result = await save_chat_history(
        messages=question_messages,
        conversation_id="improved-test-003",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Improved AI summary testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_improved_ai())
