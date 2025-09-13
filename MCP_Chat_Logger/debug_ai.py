#!/usr/bin/env python3
"""
Debug AI summarizer initialization
"""
import os
from config import config
from chat_logger import ai_summarizer

# Set API key
api_key = "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"

print("=== Debug AI Summarizer ===")
print(f"Config OPENAI_API_KEY: {config.OPENAI_API_KEY}")
print(f"Environment OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

# Set both
os.environ["OPENAI_API_KEY"] = api_key
config.OPENAI_API_KEY = api_key

print(f"After setting - Config: {config.OPENAI_API_KEY}")
print(f"After setting - Environment: {os.getenv('OPENAI_API_KEY')}")

# Recreate summarizer
from chat_logger import AISummarizer
new_summarizer = AISummarizer()

print(f"AI Summarizer available: {new_summarizer.is_available()}")
print(f"AI Summarizer client: {new_summarizer.client}")

# Test a simple analysis
if new_summarizer.is_available():
    print("\nTesting AI analysis...")
    test_messages = [
        {"role": "user", "content": "I need to fix a bug in my code"},
        {"role": "assistant", "content": "I can help you fix that bug!"}
    ]
    
    try:
        result = new_summarizer.analyze_conversation(test_messages)
        print(f"AI Analysis Result: {result}")
    except Exception as e:
        print(f"Error in AI analysis: {e}")
else:
    print("AI Summarizer not available")
