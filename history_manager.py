import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, history_dir="chat_history"):
        self.history_dir = history_dir
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

    def save_session(self, session_id, messages):
        """Saves session messages to a JSON file."""
        if not session_id:
            return
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def load_session(self, session_id):
        """Loads session messages from a JSON file."""
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def list_sessions(self):
        """Lists all available sessions, sorted by modification time (newest first)."""
        files = [f for f in os.listdir(self.history_dir) if f.endswith(".json")]
        sessions = []
        for f in files:
            path = os.path.join(self.history_dir, f)
            mtime = os.path.getmtime(path)
            sessions.append({
                "id": f.replace(".json", ""),
                "time": mtime
            })
        sessions.sort(key=lambda x: x["time"], reverse=True)
        return sessions

    def delete_session(self, session_id):
        """Deletes a session file."""
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)

    def generate_session_id(self):
        """Generates a unique session ID based on timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
