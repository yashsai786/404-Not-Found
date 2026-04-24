"""
=========================================
DESIGN PATTERN #1 — SINGLETON (Creational)
=========================================
Owner: Megha Lalwani
Purpose:
  CentralRegistry stores global system state (active kiosk, dispenser type,
  emergency flag, admin session). Exactly one instance must exist.

Implementation: classic __new__ guard + thread-safe lock.
"""
import threading
from db.database import get_conn


class CentralRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.active_kiosk_type = None         # PHARMACY | FOOD | EMERGENCY
        self.admin_authenticated = False
        self.event_log = []                   # in-memory ring buffer for UI

    # ---- persistent config helpers (SQLite-backed) ----
    def get_config(self, key, default=None):
        with get_conn() as conn:
            row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def set_config(self, key, value):
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO config(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )

    def log_event(self, level, message):
        from datetime import datetime
        entry = {"ts": datetime.now().strftime("%H:%M:%S"), "level": level, "message": message}
        self.event_log.append(entry)
        if len(self.event_log) > 200:
            self.event_log.pop(0)
        return entry
