#!/usr/bin/env python3
"""
Test script for AI summary functionality
"""
import asyncio
import os
from chat_logger import save_chat_history

async def test_ai_summary():
    """Test AI summary functionality"""
    
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = "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"
    
    # Also set it in the config
    from config import config
    config.OPENAI_API_KEY = "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"
    
    # Sample conversation with code changes
    sample_messages = [
        {
            "role": "user",
            "content": "I need to fix a bug in my Python function. The function is not handling None values correctly.",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant", 
            "content": "I can help you fix that bug! Can you show me the current function code?",
            "timestamp": "2024-01-15T10:30:15Z"
        },
        {
            "role": "user",
            "content": "Here's the current code:\n```python\ndef process_data(data):\n    result = data.upper()\n    return result\n```\nThe issue is that when data is None, it throws an AttributeError.",
            "timestamp": "2024-01-15T10:31:00Z"
        },
        {
            "role": "assistant",
            "content": "I see the problem! You need to add a None check. Here's the fixed version:\n```python\ndef process_data(data):\n    if data is None:\n        return None\n    result = data.upper()\n    return result\n```\nThis will handle None values gracefully by returning None instead of throwing an error.",
            "timestamp": "2024-01-15T10:31:30Z"
        },
        {
            "role": "user",
            "content": "Perfect! That fixes the bug. Thanks for the help!",
            "timestamp": "2024-01-15T10:32:00Z"
        }
    ]
    
    print("=== Testing AI Summary Functionality ===\n")
    
    # Test 1: AI summary enabled
    print("1. Testing with AI summary enabled...")
    result = await save_chat_history(
        messages=sample_messages,
        conversation_id="ai-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Test 2: AI summary disabled (manual values)
    print("2. Testing with AI summary disabled...")
    result = await save_chat_history(
        messages=sample_messages,
        conversation_id="ai-test-002",
        project_name="MCP_Chat_Logger",
        title="Manual Test",
        tag="bug fixed",
        description="Manual description",
        use_ai_summary=False,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ AI summary testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_ai_summary())
