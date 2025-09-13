#!/usr/bin/env python3
"""
Test script for the simple chat logger
"""
import asyncio
import os
from simple_chat_logger import save_chat_history

# Set OpenAI API key (you need to set this in your environment)
os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"

async def test_simple_chat_logger():
    """Test the simple chat logger with our conversation"""
    
    # Sample conversation from our index.html translation
    messages = [
        {
            "role": "user",
            "content": "把index.html整个界面改成英文的"
        },
        {
            "role": "assistant", 
            "content": "I'll help you translate the entire index.html interface from Chinese to English. Let me first read the current file to see what needs to be translated."
        },
        {
            "role": "assistant",
            "content": "I have successfully translated the entire index.html interface from Chinese to English. Here are the key changes made:\n\n### ✅ Completed Tasks:\n\n1. **HTML Language Attribute**: Changed from `zh-CN` to `en`\n2. **Page Title**: \"项目摘要仪表板\" → \"Project Summary Dashboard\"\n3. **UI Text Translation**:\n   - Search placeholder: \"搜索项目更新...\" → \"Search project updates...\"\n   - Filter options: \"所有项目\" → \"All Projects\", \"所有类型\" → \"All Types\"\n   - Button labels: \"添加更新摘要\" → \"Add Update Summary\", \"导出报告\" → \"Export Report\"\n   - Section headers: \"活跃项目\" → \"Active Projects\", \"更新\" → \"Updates\"\n   - Placeholder text: \"选择一个项目更新来查看详情\" → \"Select a project update to view details\"\n\n4. **JavaScript Comments**: All Chinese comments translated to English\n5. **JavaScript Strings**: All user-facing messages and console logs translated\n6. **Detail View Content**:\n   - \"摘要\" → \"Summary\"\n   - \"新功能和特性\" → \"New Features and Capabilities\"\n   - \"Bug修复\" → \"Bug Fixes\"\n   - \"影响和结果\" → \"Impact and Results\"\n   - \"关键代码变更\" → \"Key Code Changes\"\n   - \"对话详情\" → \"Conversation Details\"\n   - \"消息数\" → \"Message Count\"\n   - \"参与者\" → \"Participants\"\n\n7. **Date Formatting**: Changed from Chinese locale (`zh-CN`) to English locale (`en-US`)\n\nThe interface is now fully in English while maintaining all the original functionality and styling."
        },
        {
            "role": "user",
            "content": "remove这两个东西"
        },
        {
            "role": "assistant",
            "content": "I can see you want to remove the two buttons shown in the image - \"Add Update Summary\" and \"Export Report\". Let me remove these buttons from the interface."
        },
        {
            "role": "assistant",
            "content": "Perfect! I've successfully removed both the \"Add Update Summary\" and \"Export Report\" buttons from the interface. The Quick Actions section has been completely removed, which will clean up the sidebar and remove those two buttons you wanted to eliminate.\n\nThe interface now has a cleaner look without those action buttons in the sidebar."
        }
    ]
    
    # Test the simple chat logger
    result = await save_chat_history(
        messages=messages,
        conversation_id="index-html-translation-test",
        project_name="HackTheNorth"
    )
    
    print(result)
    print("\n✅ Test completed! Check the chat_logs directory for the generated JSON file.")

if __name__ == "__main__":
    asyncio.run(test_simple_chat_logger())