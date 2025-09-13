#!/usr/bin/env python3
"""
Script to create DynamoDB table for chat conversations
"""
import boto3
from botocore.exceptions import ClientError
from config import config

def create_dynamodb_table():
    """Create DynamoDB table for chat conversations"""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=config.DYNAMODB_REGION)
        
        # Check if table already exists
        try:
            table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)
            table.load()
            print(f"Table {config.DYNAMODB_TABLE_NAME} already exists!")
            return table
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create table
        table = dynamodb.create_table(
            TableName=config.DYNAMODB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'conversation_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'conversation_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'created_at-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        
        print(f"Creating table {config.DYNAMODB_TABLE_NAME}...")
        print("Waiting for table to be created...")
        table.wait_until_exists()
        print(f"Table {config.DYNAMODB_TABLE_NAME} created successfully!")
        
        return table
        
    except ClientError as e:
        print(f"Error creating table: {e}")
        return None

def add_ttl_attribute():
    """Add TTL attribute to the table"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=config.DYNAMODB_REGION)
        table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)
        
        # Enable TTL on the 'ttl' attribute
        response = table.update_time_to_live(
            TimeToLiveSpecification={
                'AttributeName': 'ttl',
                'Enabled': True
            }
        )
        
        print("TTL enabled on 'ttl' attribute")
        return True
        
    except ClientError as e:
        print(f"Error enabling TTL: {e}")
        return False

if __name__ == "__main__":
    print("Creating DynamoDB table for chat conversations...")
    print(f"Table name: {config.DYNAMODB_TABLE_NAME}")
    print(f"Region: {config.DYNAMODB_REGION}")
    
    table = create_dynamodb_table()
    if table:
        add_ttl_attribute()
        print("\nSetup complete!")
        print("\nNext steps:")
        print("1. Configure your AWS credentials")
        print("2. Update the config.py file with your preferred settings")
        print("3. Run the MCP server")
    else:
        print("Failed to create table. Please check your AWS credentials and permissions.")
