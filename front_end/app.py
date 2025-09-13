from flask import Flask, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_type_from_tag(tag):
    """Convert tag to type"""
    tag_map = {
        'bug fixed': 'Security Update',
        'function added': 'Feature Development', 
        'function modify': 'Feature Development',
        'question': 'Discussion',
        'discussion': 'Discussion',
        'other': 'Other'
    }
    return tag_map.get(tag, 'Other')

def extract_functions(data):
    """Extract function-related content from conversation"""
    functions = []
    messages = data.get('messages', [])
    
    for msg in messages:
        content = msg.get('content', '')
        # Look for function-related keywords
        if any(keyword in content.lower() for keyword in ['function', 'method', 'added', 'implemented', 'create', 'add', 'implement']):
            # Extract possible function descriptions
            sentences = content.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in ['function', 'method', 'added', 'implemented', 'create', 'add', 'implement']):
                    if sentence.strip():
                        functions.append(sentence.strip())
    
    return functions[:5]  # Limit to 5 functions

def extract_bug_fixes(data):
    """Extract bug fix related content from conversation"""
    bug_fixes = []
    messages = data.get('messages', [])
    
    for msg in messages:
        content = msg.get('content', '')
        # Look for bug-related keywords
        if any(keyword in content.lower() for keyword in ['bug', 'fix', 'error', 'issue', 'repair', 'problem']):
            sentences = content.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in ['bug', 'fix', 'error', 'issue', 'repair', 'problem']):
                    if sentence.strip():
                        bug_fixes.append(sentence.strip())
    
    return bug_fixes[:5]  # Limit to 5 bug fixes

def extract_tags(data):
    """Extract tags"""
    tags = []
    tag = data.get('tag', '')
    description = data.get('description', '')
    
    # Add tag
    if tag and tag != 'other':
        tags.append(tag.replace(' ', '-'))
    
    # Extract keywords from description
    keywords = description.lower().split(' ')
    for keyword in keywords:
        if len(keyword) > 3 and keyword not in tags:
            tags.append(keyword)
    
    return tags[:6]  # Limit to 6 tags

def format_code_changes(before_code, after_code):
    """Format code changes"""
    if not before_code and not after_code:
        return '// No code changes detected'
    
    result = ''
    
    if before_code:
        result += '// Before:\n'
        result += before_code + '\n\n'
    
    if after_code:
        result += '// After:\n'
        result += after_code
    
    return result

def generate_impact_description(tag, description):
    """Generate impact description"""
    impact_map = {
        'bug fixed': 'Improved system stability and user experience',
        'function added': 'Enhanced functionality and user capabilities',
        'function modify': 'Optimized existing features and performance',
        'question': 'Clarified requirements and improved understanding',
        'discussion': 'Promoted knowledge sharing and collaboration',
        'other': 'Had a positive impact on project development'
    }
    
    return impact_map.get(tag, 'Had a positive impact on project development')

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/projects')
def get_projects():
    """Get project data API"""
    try:
        chat_logs_dir = os.path.join(os.path.dirname(__file__), '..', 'MCP_Chat_Logger', 'chat_logs')
        
        # Check if chat_logs directory exists
        if not os.path.exists(chat_logs_dir):
            return jsonify({'projects': [], 'projectSummaries': []})
        
        # Read all JSON files
        files = [f for f in os.listdir(chat_logs_dir) if f.endswith('.json')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(chat_logs_dir, x)), reverse=True)  # Sort by modification time descending
        
        print(f"Found {len(files)} JSON files: {files}")  # Debug info
        
        project_summaries = []
        project_map = {}
        
        for file in files:
            try:
                file_path = os.path.join(chat_logs_dir, file)
                print(f"Processing file: {file}")  # Debug info
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract project information
                project_name = data.get('project_name', 'Unknown Project')
                tag = data.get('tag', 'other')
                description = data.get('description', '')
                before_code = data.get('before_code', '')
                after_code = data.get('after_code', '')
                title = data.get('title', f'Update {len(project_summaries) + 1}')
                summary = data.get('summary', description)
                timestamp = data.get('created_at', datetime.now().isoformat())
                message_count = data.get('message_count', 0)
                participants = data.get('participants', [])
                
                # Create project summary object
                project_summary = {
                    'id': data.get('conversation_id', f'project-{len(project_summaries) + 1}'),
                    'projectName': project_name,
                    'title': title,
                    'summary': summary,
                    'type': get_type_from_tag(tag),
                    'timestamp': timestamp,
                    'aiModel': 'OpenAI GPT-3.5',
                    'functions': extract_functions(data),
                    'bugFixes': extract_bug_fixes(data),
                    'tags': extract_tags(data),
                    'codeChanges': format_code_changes(before_code, after_code),
                    'impact': generate_impact_description(tag, description),
                    'messageCount': message_count,
                    'participants': participants
                }
                
                project_summaries.append(project_summary)
                
                # Track project statistics
                if project_name in project_map:
                    project_map[project_name]['updates'] += 1
                else:
                    project_map[project_name] = {
                        'name': project_name,
                        'updates': 1,
                        'status': 'Active'
                    }
                    
            except Exception as e:
                print(f'Error reading file {file}: {e}')
                continue
        
        # Convert project map to array
        projects = list(project_map.values())
        
        return jsonify({
            'projects': projects,
            'projectSummaries': project_summaries
        })
        
    except Exception as e:
        print(f'Error reading project data: {e}')
        return jsonify({'error': 'Failed to read project data'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
