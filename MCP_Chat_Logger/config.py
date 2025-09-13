"""
Configuration file for MCP Chat Logger
"""
import os
from typing import Optional

class Config:
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "chat_conversations")
    DYNAMODB_REGION: str = os.getenv("DYNAMODB_REGION", "us-east-1")
    
    # AWS Credentials (will be automatically detected from environment or AWS config)
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: Optional[str] = os.getenv("AWS_SESSION_TOKEN")
    
    # File Storage Configuration
    LOGS_DIRECTORY: str = os.getenv("LOGS_DIRECTORY", "chat_logs")
    
    # TTL Configuration (in days)
    DEFAULT_TTL_DAYS: int = int(os.getenv("DEFAULT_TTL_DAYS", "30"))
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Global config instance
config = Config()
