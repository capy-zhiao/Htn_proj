#!/usr/bin/env python3
"""
Check MCP server status
"""
import subprocess
import json
import time

def check_mcp_status():
    """Check if MCP server is running"""
    try:
        # Check if the process is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'simple_chat_logger.py' in result.stdout:
            print("✅ MCP server process is running")
            return True
        else:
            print("❌ MCP server process is not running")
            return False
    except Exception as e:
        print(f"❌ Error checking MCP status: {e}")
        return False

def test_mcp_connection():
    """Test MCP connection"""
    try:
        # Try to start MCP server and send a test message
        process = subprocess.Popen(
            ['uv', 'run', 'simple_chat_logger.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send MCP initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server started successfully")
            process.terminate()
            return True
        else:
            print("❌ MCP server failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MCP connection: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking MCP Status...")
    print("=" * 50)
    
    # Check if process is running
    process_running = check_mcp_status()
    
    # Test MCP connection
    connection_ok = test_mcp_connection()
    
    print("=" * 50)
    if process_running and connection_ok:
        print("🎉 MCP is working correctly!")
    else:
        print("💥 MCP has issues!")
        print("\n建议:")
        print("1. 重启Cursor")
        print("2. 检查MCP配置文件")
        print("3. 确保依赖已安装")

