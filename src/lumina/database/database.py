import json, os, sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, config):
        self.db_path = "data/lumina.db"
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp TEXT, type TEXT, data TEXT)")
        self.conn.commit()
    
    def log_event(self, event_type, data):
        self.conn.execute("INSERT INTO events (timestamp, type, data) VALUES (?, ?, ?)", 
                         (datetime.now().isoformat(), event_type, json.dumps(data)))
        self.conn.commit()
    
    def log_environmental_data(self, data_type, value, metadata=None):
        self.log_event("environmental", {"type": data_type, "value": value, "metadata": metadata})
    
    def get_stats(self): 
        return {"total_events": self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]}
    
    def save_state(self, state):
        self.conn.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, data TEXT)")
        self.conn.execute("DELETE FROM state")
        self.conn.execute("INSERT INTO state (data) VALUES (?)", (json.dumps(state),))
        self.conn.commit()
    
    def get_state(self):
        try:
            result = self.conn.execute("SELECT data FROM state LIMIT 1").fetchone()
            return json.loads(result[0]) if result else None
        except:
            return None
    
    def close(self):
        self.conn.close()
