#!/usr/bin/env python3
"""
Cursor Code Change Detector
Automatically detects code changes in Cursor and extracts before/after code
"""
import os
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class CursorCodeDetector:
    """Detects code changes from Cursor editor and conversation context"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.git_path = os.path.join(self.workspace_path, '.git')
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        return os.path.exists(self.git_path)
    
    def get_git_status(self) -> Dict[str, List[str]]:
        """Get git status of modified files"""
        if not self.is_git_repo():
            return {"modified": [], "added": [], "deleted": []}
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            modified = []
            added = []
            deleted = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]
                
                if status[0] == 'M':  # Modified
                    modified.append(filename)
                elif status[0] == 'A':  # Added
                    added.append(filename)
                elif status[0] == 'D':  # Deleted
                    deleted.append(filename)
            
            return {
                "modified": modified,
                "added": added,
                "deleted": deleted
            }
        except Exception as e:
            print(f"Error getting git status: {e}")
            return {"modified": [], "added": [], "deleted": []}
    
    def get_file_diff(self, filename: str) -> Optional[Tuple[str, str]]:
        """Get before and after code for a modified file"""
        if not self.is_git_repo():
            return None
        
        try:
            # Get the current version (after changes)
            with open(os.path.join(self.workspace_path, filename), 'r', encoding='utf-8') as f:
                after_code = f.read()
            
            # Get the previous version (before changes) from git
            result = subprocess.run(
                ['git', 'show', f'HEAD:{filename}'],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                before_code = result.stdout
            else:
                # If file doesn't exist in HEAD, it's a new file
                before_code = ""
            
            return before_code, after_code
            
        except Exception as e:
            print(f"Error getting diff for {filename}: {e}")
            return None
    
    def detect_code_changes(self) -> Dict[str, Dict[str, str]]:
        """Detect all code changes in the workspace"""
        changes = {}
        git_status = self.get_git_status()
        
        # Process modified files
        for filename in git_status["modified"]:
            if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs')):
                diff_result = self.get_file_diff(filename)
                if diff_result:
                    before_code, after_code = diff_result
                    changes[filename] = {
                        "before_code": before_code,
                        "after_code": after_code,
                        "change_type": "modified"
                    }
        
        # Process added files
        for filename in git_status["added"]:
            if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs')):
                try:
                    with open(os.path.join(self.workspace_path, filename), 'r', encoding='utf-8') as f:
                        after_code = f.read()
                    changes[filename] = {
                        "before_code": "",
                        "after_code": after_code,
                        "change_type": "added"
                    }
                except Exception as e:
                    print(f"Error reading added file {filename}: {e}")
        
        return changes
    
    def detect_conversation_code_changes(self, messages: List[Dict[str, any]]) -> Dict[str, any]:
        """Detect code changes from conversation messages by analyzing the entire conversation history"""
        changes = {}
        all_code_blocks = []
        
        # Collect all code blocks from the entire conversation
        for i, message in enumerate(messages):
            content = message.get("content", "")
            role = message.get("role", "")
            
            # Look for code blocks in the conversation
            import re
            code_blocks = re.findall(r'```(?:python|py|javascript|js|typescript|ts|java|cpp|c|html|css|sql|bash|sh)?\n(.*?)```', content, re.DOTALL)
            
            for code_block in code_blocks:
                code_block = code_block.strip()
                if len(code_block) > 50:  # Only consider substantial code blocks
                    all_code_blocks.append({
                        "code": code_block,
                        "role": role,
                        "content": content,
                        "message_index": i,
                        "timestamp": message.get("timestamp", "")
                    })
        
        # Analyze the conversation flow to determine before/after code
        if len(all_code_blocks) >= 2:
            # Sort by message index to get chronological order
            all_code_blocks.sort(key=lambda x: x["message_index"])
            
            # Look for patterns that indicate before/after relationship
            before_code = None
            after_code = None
            
            for i, code_block in enumerate(all_code_blocks):
                content = code_block["content"].lower()
                
                # Check for keywords that indicate this is "before" code
                before_indicators = [
                    "old", "previous", "original", "before", "replaced", 
                    "current implementation", "existing code", "old version",
                    "修改前", "原来的", "之前的", "现有代码"
                ]
                
                # Check for keywords that indicate this is "after" code  
                after_indicators = [
                    "new", "updated", "modified", "fixed", "improved", 
                    "enhanced", "added", "created", "new implementation",
                    "修改后", "新的", "更新后", "改进后", "修复后"
                ]
                
                has_before_indicators = any(indicator in content for indicator in before_indicators)
                has_after_indicators = any(indicator in content for indicator in after_indicators)
                
                if has_before_indicators and not has_after_indicators:
                    before_code = code_block["code"]
                elif has_after_indicators and not has_before_indicators:
                    after_code = code_block["code"]
                elif not before_code and not after_code:
                    # If no clear indicators, use chronological order
                    if i == 0:
                        before_code = code_block["code"]
                    else:
                        after_code = code_block["code"]
                elif before_code and not after_code:
                    after_code = code_block["code"]
                elif not before_code and after_code:
                    before_code = code_block["code"]
            
            # If we still don't have both, use the first and last
            if not before_code and not after_code:
                before_code = all_code_blocks[0]["code"]
                after_code = all_code_blocks[-1]["code"]
            elif not before_code:
                before_code = all_code_blocks[0]["code"]
            elif not after_code:
                after_code = all_code_blocks[-1]["code"]
            
            changes["before_code"] = before_code
            changes["after_code"] = after_code
            
        elif len(all_code_blocks) == 1:
            # If only one code block, check context to determine if it's before or after
            code_block = all_code_blocks[0]
            content = code_block["content"].lower()
            
            # Look for keywords that suggest this is "after" code
            after_keywords = ["new", "updated", "modified", "fixed", "improved", "enhanced", "added", "created"]
            before_keywords = ["old", "previous", "original", "before", "replaced"]
            
            has_after_keywords = any(keyword in content for keyword in after_keywords)
            has_before_keywords = any(keyword in content for keyword in before_keywords)
            
            if has_after_keywords and not has_before_keywords:
                changes["after_code"] = code_block["code"]
            elif has_before_keywords and not has_after_keywords:
                changes["before_code"] = code_block["code"]
            else:
                # Default: treat as after_code (new implementation)
                changes["after_code"] = code_block["code"]
        
        return changes
    
    def get_change_summary(self, messages: List[Dict[str, any]] = None) -> Dict[str, any]:
        """Get a summary of all changes (git + conversation)"""
        # First try to detect from conversation
        conversation_changes = {}
        if messages:
            conversation_changes = self.detect_conversation_code_changes(messages)
        
        # Then try git changes
        git_changes = self.detect_code_changes()
        
        # Combine both sources
        all_changes = {}
        
        # Add conversation changes
        if conversation_changes:
            all_changes["conversation"] = {
                "before_code": conversation_changes.get("before_code", ""),
                "after_code": conversation_changes.get("after_code", ""),
                "change_type": "conversation"
            }
        
        # Add git changes
        all_changes.update(git_changes)
        
        if not all_changes:
            return {
                "has_changes": False,
                "message": "No code changes detected",
                "files_changed": 0,
                "changes": {}
            }
        
        # Determine the overall change type
        change_types = [change["change_type"] for change in all_changes.values()]
        if "conversation" in change_types:
            overall_type = "function modify"  # Conversation usually means modification
        elif "added" in change_types and "modified" in change_types:
            overall_type = "mixed"
        elif "added" in change_types:
            overall_type = "function added"
        elif "modified" in change_types:
            overall_type = "function modify"
        else:
            overall_type = "other"
        
        return {
            "has_changes": True,
            "overall_type": overall_type,
            "files_changed": len(all_changes),
            "changes": all_changes,
            "message": f"Detected {len(all_changes)} source(s) with changes: {', '.join(all_changes.keys())}"
        }

def detect_cursor_changes(workspace_path: str = None, messages: List[Dict[str, any]] = None) -> Dict[str, any]:
    """Main function to detect Cursor code changes"""
    detector = CursorCodeDetector(workspace_path)
    return detector.get_change_summary(messages)

if __name__ == "__main__":
    # Test the detector
    result = detect_cursor_changes()
    print("=== Cursor Code Change Detection ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
