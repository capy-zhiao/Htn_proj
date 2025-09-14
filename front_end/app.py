from flask import Flask, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import json
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parents[1]
CHAT_LOGS_DIR = BASE_DIR / "MCP_Chat_Logger" / "chat_logs"
app.config["CHAT_LOGS_DIR"] = str(CHAT_LOGS_DIR)

cache = {
    'data': None,
    'expiry': datetime.min
}

@app.route("/")
def index():
    return render_template("index.html")

def process_log_files(log_dir):
    """Reads all log files and processes them into project and summary data."""
    p = Path(log_dir)
    if not p.exists() or not p.is_dir():
        return {"projects": [], "projectSummaries": []}

    files = sorted(p.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    project_summaries = []
    for fpath in files:
        try:
            with fpath.open("r", encoding="utf-8") as f:
                data = json.load(f)

            project_summary = {
                "id": data.get("id"),
                "projectName": data.get("project_name"),
                "title": data.get("title"),
                "summary": data.get("summary"),
                "messages": data.get("messages"),
                "messageCount": data.get("message_count"),
            }
            project_summaries.append(project_summary)
        except Exception as e:
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
    
@app.route("/api/projects")
def get_projects():
    if datetime.now() < cache["expiry"] and cache["data"] is not None:
        return jsonify(cache["data"])

    data = process_log_files(app.config["CHAT_LOGS_DIR"])
    cache["data"] = data
    cache["expiry"] = datetime.now() + timedelta(seconds=60)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
