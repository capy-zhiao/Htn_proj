from flask import Flask, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['CHAT_LOGS_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'MCP_Chat_Logger', 'chat_logs')
cache = {
    'data': None,
    'expiry': datetime.min
}

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

def process_log_files(log_dir):
    """Reads all log files and processes them into project and summary data."""
    if not os.path.exists(log_dir):
        return {'projects': [], 'projectSummaries': []}

    files = [f for f in os.listdir(log_dir) if f.endswith('.json')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
    
    project_summaries = []
    for file in files:
        try:
            with open(os.path.join(log_dir, file), 'r', encoding='utf-8') as f:
                data = json.load(f)

            project_summary = {
                'id': data.get('conversation_id'),
                'projectName': data.get('project_name'),
                'title': data.get('title'),
                'summary': data.get('summary'),
                'codeChanges': data.get('code_changes'),
                'type': data.get('type'),
                'tags': data.get('tags'),
                'timestamp': data.get('timestamp'),
                'messageCount': data.get('message_count'),
                'participants': data.get('participants'),
                'aiModel': data.get('ai_model')
            }
            project_summaries.append(project_summary)
        except Exception as e:
            print(f'Error reading file {file}: {e}')
            continue
        
    # Aggregate projects
    project_map = {}
    for summary in project_summaries:
        project_name = summary['projectName']
        if project_name in project_map:
            project_map[project_name]['updates'] += 1
        else:
            project_map[project_name] = {
                'name': project_name,
                'updates': 1,
                'status': 'Active'
            }
    
    return {
        'projects': list(project_map.values()),
        'projectSummaries': project_summaries
    }
    
@app.route('/api/projects')
def get_projects():
    """API endpoint to get project data."""
    if datetime.now() < cache['expiry'] and cache['data'] is not None:
        return jsonify(cache['data'])
    
    log_dir = app.config['CHAT_LOGS_DIR']
    response_data = process_log_files(log_dir)
    cache['data'] = response_data
    cache['expiry'] = datetime.now() + timedelta(seconds=60)
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
