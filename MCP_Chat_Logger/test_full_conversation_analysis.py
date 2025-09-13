#!/usr/bin/env python3
"""
Test full conversation analysis functionality
"""
import asyncio
from chat_logger import save_chat_history_with_cursor_changes

async def test_full_conversation_analysis():
    """Test full conversation analysis functionality"""
    
    print("=== Testing Full Conversation Analysis ===\n")
    
    # Simulate a full conversation with multiple code changes over time
    messages = [
        {
            "role": "user",
            "content": "我需要修改chat_logger.py来添加新功能",
            "timestamp": "2025-09-13T14:30:00Z"
        },
        {
            "role": "assistant",
            "content": "好的！让我先看看当前的实现：\n\n```python\nclass ChatLogger:\n    def __init__(self):\n        self.messages = []\n    \n    def add_message(self, message):\n        self.messages.append(message)\n```\n\n这是当前的实现，您想要添加什么功能？",
            "timestamp": "2025-09-13T14:30:15Z"
        },
        {
            "role": "user",
            "content": "我想添加AI总结功能",
            "timestamp": "2025-09-13T14:30:30Z"
        },
        {
            "role": "assistant",
            "content": "好的！我来为您添加AI总结功能。这是修改后的代码：\n\n```python\nclass ChatLogger:\n    def __init__(self):\n        self.messages = []\n        self.ai_summarizer = AISummarizer()\n    \n    def add_message(self, message):\n        self.messages.append(message)\n    \n    def generate_summary(self):\n        return self.ai_summarizer.analyze(self.messages)\n    \n    def save_with_ai_summary(self):\n        summary = self.generate_summary()\n        return self.save_to_json(summary)\n```\n\n现在ChatLogger支持AI总结了！",
            "timestamp": "2025-09-13T14:30:45Z"
        },
        {
            "role": "user",
            "content": "很好！现在我还想添加代码变更检测功能",
            "timestamp": "2025-09-13T14:31:00Z"
        },
        {
            "role": "assistant",
            "content": "好的！让我添加代码变更检测功能：\n\n```python\nclass ChatLogger:\n    def __init__(self):\n        self.messages = []\n        self.ai_summarizer = AISummarizer()\n        self.code_detector = CodeDetector()\n    \n    def add_message(self, message):\n        self.messages.append(message)\n    \n    def generate_summary(self):\n        return self.ai_summarizer.analyze(self.messages)\n    \n    def detect_code_changes(self):\n        return self.code_detector.analyze_conversation(self.messages)\n    \n    def save_with_ai_summary(self):\n        summary = self.generate_summary()\n        code_changes = self.detect_code_changes()\n        return self.save_to_json(summary, code_changes)\n```\n\n现在ChatLogger支持AI总结和代码变更检测了！",
            "timestamp": "2025-09-13T14:31:15Z"
        }
    ]
    
    print("Testing with full conversation analysis...")
    result = await save_chat_history_with_cursor_changes(
        messages=messages,
        conversation_id="full-conversation-analysis-test-001",
        project_name="MCP_Chat_Logger",
        use_ai_summary=True,
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Full conversation analysis testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_full_conversation_analysis())
