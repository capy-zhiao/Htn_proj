#!/usr/bin/env python3
"""
Setup script for MCP Chat Logger with DynamoDB support
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "boto3", "pydantic"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("Checking AWS credentials...")
    try:
        import boto3
        sts = boto3.client('sts')
        sts.get_caller_identity()
        print("✅ AWS credentials are configured!")
        return True
    except Exception as e:
        print(f"⚠️  AWS credentials not found: {e}")
        print("Please configure AWS credentials using 'aws configure' or environment variables")
        return False

def create_dynamodb_table():
    """Create DynamoDB table"""
    print("Creating DynamoDB table...")
    try:
        from create_dynamodb_table import create_dynamodb_table, add_ttl_attribute
        table = create_dynamodb_table()
        if table:
            add_ttl_attribute()
            print("✅ DynamoDB table created successfully!")
            return True
        else:
            print("❌ Failed to create DynamoDB table")
            return False
    except Exception as e:
        print(f"❌ Error creating DynamoDB table: {e}")
        return False

def main():
    """Main setup function"""
    print("=== MCP Chat Logger Setup ===\n")
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("Setup failed at dependency installation")
        return False
    
    # Step 2: Check AWS credentials
    aws_configured = check_aws_credentials()
    
    # Step 3: Create DynamoDB table (only if AWS is configured)
    if aws_configured:
        if not create_dynamodb_table():
            print("Setup completed with warnings - DynamoDB table creation failed")
            return False
    else:
        print("⚠️  Skipping DynamoDB table creation - AWS not configured")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Configure your AWS credentials if not already done")
    print("2. Run 'python example_usage.py' to test the functionality")
    print("3. Use the MCP server in your application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
