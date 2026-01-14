from __future__ import annotations
import sqlite3, os, json, time
from typing import List, Dict, Any, Optional

DB_PATH = os.getenv('AGENT_EVENTS_DB', 'agent_events.db')

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS agent_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL,
  created_at REAL NOT NULL,
  last_attempt REAL,
  attempts INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  detail TEXT,
  payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_events_request ON agent_events(request_id);
"""

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.executescript(_INIT_SQL)

def record_event(request_id: str, payload: Dict[str, Any]):
    with _conn() as c:
        c.execute("INSERT INTO agent_events(request_id, created_at, status, payload) VALUES (?,?,?,?)",
                  (request_id, time.time(), 'pending', json.dumps(payload)))

def update_event(request_id: str, status: str, detail: str, attempts: int):
    with _conn() as c:
        c.execute("UPDATE agent_events SET status=?, detail=?, attempts=?, last_attempt=? WHERE request_id=?",
                  (status, detail, attempts, time.time(), request_id))

def list_events(limit: int=100, offset: int = 0) -> List[Dict[str, Any]]:
    """List recent events with lightweight size metric (payloadSize bytes). Supports offset for pagination."""
    if offset < 0: offset = 0
    with _conn() as c:
        rows = c.execute("SELECT request_id, created_at, last_attempt, attempts, status, detail, LENGTH(payload) FROM agent_events ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    out=[]
    for r in rows:
        out.append({
            'requestId': r[0],
            'request_id': r[0],  # alias for legacy frontend code
            'createdAt': r[1],
            'lastAttempt': r[2],
            'attempts': r[3],
            'status': r[4],
            'detail': r[5],
            'payloadSize': r[6]
        })
    return out

def get_payload(request_id: str) -> Optional[Dict[str, Any]]:
    # Always pick the most recent event for this request
    with _conn() as c:
        row = c.execute("SELECT payload FROM agent_events WHERE request_id=? ORDER BY id DESC LIMIT 1", (request_id,)).fetchone()
    if not row: return None
    try:
        return json.loads(row[0])
    except Exception:
        return None

def get_payload_info(request_id: str) -> Optional[Dict[str, Any]]:
    """Return size and mode info without transferring full payload (except limited keys)."""
    with _conn() as c:
        row = c.execute("SELECT payload FROM agent_events WHERE request_id=? ORDER BY id DESC LIMIT 1", (request_id,)).fetchone()
    if not row:
        return None
    raw = row[0]
    size = len(raw) if raw else 0
    mode = 'unknown'
    top_keys: List[str] = []
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            top_keys = list(data.keys())[:25]
            if 'full' in data:
                mode = 'full'
            elif 'rasi' in data:
                mode = 'bundle'
            else:
                mode = 'summary'
    except Exception:
        data = None  # noqa: F841
    return {
        'requestId': request_id,
        'sizeBytes': size,
        'sizeKB': round(size/1024,2),
        'approxSizeKB': f"{size/1024:.2f} KB",
        'modeDetected': mode,
        'topLevelKeyCount': len(top_keys),
        'topLevelKeys': top_keys
    }

init_db()