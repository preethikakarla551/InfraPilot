"""Minimal SQLite persistence for diagnostic history."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = os.getenv("INFRAPILOT_DB", "data/infrapilot.db")


def connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)")
    return db


@contextmanager
def database():
    db = connect()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def save_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    created = datetime.now(timezone.utc).isoformat()
    with database() as db:
        cur = db.execute("INSERT INTO snapshots(created_at,payload) VALUES (?,?)", (created, json.dumps(payload)))
        snapshot_id = cur.lastrowid
    return {"id": snapshot_id, "created_at": created, "payload": payload}


def recent_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    with database() as db:
        rows = db.execute("SELECT id,created_at,payload FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": row[0], "created_at": row[1], "payload": json.loads(row[2])} for row in rows]
