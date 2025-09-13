#!/usr/bin/env python3
"""
Test manual before/after code input
"""
import asyncio
from chat_logger import save_chat_history

async def test_manual_code():
    """Test manual before/after code input"""
    
    print("=== Testing Manual Before/After Code Input ===\n")
    
    # Sample conversation
    messages = [
        {
            "role": "user",
            "content": "I need to fix the save_chat_history function to properly handle before_code and after_code parameters",
            "timestamp": "2025-09-13T14:20:00Z"
        },
        {
            "role": "assistant",
            "content": "I'll help you fix the save_chat_history function. Let me show you the current implementation and the improved version.",
            "timestamp": "2025-09-13T14:20:15Z"
        }
    ]
    
    # Before code (current implementation)
    before_code = '''@mcp.tool()
async def save_chat_history(messages: List[Dict[str, Any]], conversation_id: str = None) -> str:
    """
    Save chat history as a Markdown file
    """
    ensure_logs_directory()
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_logs/chat_{conversation_id}_{timestamp}.md" if conversation_id else f"chat_logs/chat_{timestamp}.md"
    
    # Format all messages
    formatted_content = "# Chat History\\n\\n"
    for message in messages:
        formatted_content += format_message(message)
    
    # Save file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(formatted_content)
    
    return f"Chat history has been saved to file: {filename}"'''
    
    # After code (improved implementation)
    after_code = '''@mcp.tool()
async def save_chat_history(messages: List[Dict[str, Any]], conversation_id: str = None, title: str = None, summary: str = None, 
                           project_name: str = "MCP_Chat_Logger", tag: str = None, description: str = "",
                           before_code: str = None, after_code: str = None, save_to_db: bool = False, save_to_file: bool = True, 
                           use_ai_summary: bool = True) -> str:
    """
    Save chat history as JSON format and optionally to DynamoDB
    
    Args:
        messages: List of chat messages, each containing role and content
        conversation_id: Optional conversation ID for file naming
        title: Optional title for the conversation
        summary: Optional summary of the conversation
        project_name: Project name (default: MCP_Chat_Logger)
        tag: Tag for the change (bug fixed/function added/function modify)
        description: Description of the changes
        before_code: Code before the change
        after_code: Code after the change
        save_to_db: Whether to save to DynamoDB (default: False)
        save_to_file: Whether to save to local JSON file (default: True)
        use_ai_summary: Whether to use AI to generate summary fields (default: True)
    """
    # Use AI summary if requested and available
    if use_ai_summary:
        # Ensure API key is set for MCP environment
        if not config.OPENAI_API_KEY:
            config.OPENAI_API_KEY = "your-api-key-here"
        
        summarizer = get_ai_summarizer()
        if summarizer.is_available():
            print("🤖 Using AI to analyze conversation...")
            ai_analysis = summarizer.analyze_conversation(messages)
        
            # Override with AI analysis if not manually provided
            title = title or ai_analysis.get("title", "")
            summary = summary or ai_analysis.get("summary", "")
            tag = tag or ai_analysis.get("tag", "other")
            description = description or ai_analysis.get("description", "")
            before_code = before_code or ai_analysis.get("before_code")
            after_code = after_code or ai_analysis.get("after_code")
            
            print(f"✅ AI Analysis: {tag} - {description[:50]}...")
        else:
            print("⚠️  AI summary requested but OpenAI API not available. Using manual values.")
    
    # Use default values if not provided
    tag = tag or "other"
    description = description or "No description provided"
    title = title or "Chat Conversation"
    summary = summary or "No summary provided"
    
    # Create conversation summary
    conversation = create_conversation_summary(messages, conversation_id, title, summary, 
                                             project_name, tag, description, before_code, after_code)
    
    results = []
    
    # Save to DynamoDB if requested
    if save_to_db:
        if save_to_dynamodb(conversation):
            results.append(f"✅ Conversation saved to DynamoDB table: {db_config.table_name}")
        else:
            results.append("❌ Failed to save to DynamoDB")
    
    # Save to JSON file if requested
    if save_to_file:
        filename = save_to_json_file(conversation)
        results.append(f"✅ Conversation saved to JSON file: {filename}")
    
    return "\\n".join(results)'''
    
    print("Testing with manual before/after code...")
    result = await save_chat_history(
        messages=messages,
        conversation_id="manual-code-test-001",
        project_name="MCP_Chat_Logger",
        title="Enhanced save_chat_history Function",
        tag="function modify",
        description="Added support for before_code and after_code parameters to save_chat_history function",
        before_code=before_code,
        after_code=after_code,
        use_ai_summary=False,  # Use manual values instead of AI
        save_to_db=False,
        save_to_file=True
    )
    print(result)
    print()
    
    print("✅ Manual code testing completed!")
    print("Check the 'chat_logs' directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_manual_code())
