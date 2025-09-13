#!/usr/bin/env python3
"""
Example usage of the MCP Chat Logger
"""
import asyncio
from chat_logger import save_chat_history, save_chat_history_markdown

async def main():
    """Example usage of the chat logger"""
    
    # Sample conversation data
    sample_messages = [
        {
            "role": "user",
            "content": "Hello, I need help with my Python project.",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant", 
            "content": "I'd be happy to help you with your Python project! Could you tell me more about what specific issues you're facing?",
            "timestamp": "2024-01-15T10:30:15Z"
        },
        {
            "role": "user",
            "content": "I'm having trouble with data processing and want to store the results in a database.",
            "timestamp": "2024-01-15T10:31:00Z"
        },
        {
            "role": "assistant",
            "content": "For data processing and database storage, I'd recommend using pandas for data manipulation and SQLAlchemy or Django ORM for database operations. What type of data are you working with?",
            "timestamp": "2024-01-15T10:31:30Z"
        }
    ]
    
    print("=== MCP Chat Logger Example ===\n")
    
    # Example 1: Save with new JSON format (function modification)
    print("1. Saving conversation with function modification details...")
    result = await save_chat_history(
        messages=sample_messages,
        conversation_id="example-conversation-001",
        title="Chat Logger Upgrade",
        summary="Upgraded chat logger from Markdown to JSON format with DynamoDB support",
        project_name="MCP_Chat_Logger",
        tag="function modify",
        description="Modified chat_logger.py to support JSON output format and DynamoDB storage instead of just Markdown files",
        before_code="def save_chat_history(messages, conversation_id=None):\n    # Save as Markdown file\n    with open(filename, 'w') as f:\n        f.write(markdown_content)",
        after_code="def save_chat_history(messages, conversation_id=None, project_name='MCP_Chat_Logger', tag='function modify', description='', before_code=None, after_code=None):\n    # Save as JSON with structured data\n    conversation = create_conversation_summary(...)\n    with open(filename, 'w') as f:\n        json.dump(conversation_dict, f, indent=2)",
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Example 2: Save with bug fix tag
    print("2. Saving conversation with bug fix details...")
    result = await save_chat_history(
        messages=sample_messages,
        conversation_id="example-conversation-002", 
        title="Fixed Import Error",
        summary="Fixed import error in chat_logger.py",
        project_name="MCP_Chat_Logger",
        tag="bug fixed",
        description="Fixed missing import statement for boto3 that was causing runtime errors",
        before_code="import os\nfrom datetime import datetime\nfrom mcp.server.fastmcp import FastMCP",
        after_code="import os\nimport json\nimport uuid\nfrom datetime import datetime\nfrom mcp.server.fastmcp import FastMCP\nimport boto3\nfrom botocore.exceptions import ClientError, NoCredentialsError",
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Example 3: Save with function added tag
    print("3. Saving conversation with new function added...")
    result = await save_chat_history(
        messages=sample_messages,
        conversation_id="example-conversation-003",
        title="Added DynamoDB Support",
        summary="Added new function to save conversations to DynamoDB",
        project_name="MCP_Chat_Logger", 
        tag="function added",
        description="Added save_to_dynamodb() function to enable cloud storage of chat conversations",
        before_code="",
        after_code="def save_to_dynamodb(conversation: ConversationSummary) -> bool:\n    \"\"\"Save conversation to DynamoDB\"\"\"\n    if not db_config.initialize():\n        return False\n    try:\n        item = conversation.model_dump()\n        db_config.table.put_item(Item=item)\n        return True\n    except ClientError as e:\n        print(f\"Error saving to DynamoDB: {e}\")\n        return False",
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    # Example 4: Save to Markdown (original functionality)
    print("4. Saving conversation to Markdown file...")
    result = await save_chat_history_markdown(
        messages=sample_messages,
        conversation_id="example-conversation-003"
    )
    print(result)
    print()
    
    print("Example completed! Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(main())
