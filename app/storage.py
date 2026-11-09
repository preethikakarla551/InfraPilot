"""Minimal SQLite persistence for diagnostic history."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymysql

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
    if os.getenv("INFRAPILOT_STORAGE_BACKEND", "sqlite").lower() == "mysql":
        return _mysql_save_snapshot(payload, created)
    with database() as db:
        cur = db.execute("INSERT INTO snapshots(created_at,payload) VALUES (?,?)", (created, json.dumps(payload)))
        snapshot_id = cur.lastrowid
    return {"id": snapshot_id, "created_at": created, "payload": payload}


def recent_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    if os.getenv("INFRAPILOT_STORAGE_BACKEND", "sqlite").lower() == "mysql":
        return _mysql_recent_snapshots(limit)
    with database() as db:
        rows = db.execute("SELECT id,created_at,payload FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": row[0], "created_at": row[1], "payload": json.loads(row[2])} for row in rows]


def _mysql_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "infrauser"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "infrapilot"),
        connect_timeout=3,
        read_timeout=3,
        write_timeout=3,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def _ensure_mysql_table(connection: pymysql.connections.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS snapshots (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                created_at VARCHAR(40) NOT NULL,
                payload JSON NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )


def _mysql_save_snapshot(payload: dict[str, Any], created: str) -> dict[str, Any]:
    with _mysql_connection() as connection:
        _ensure_mysql_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO snapshots (created_at, payload) VALUES (%s, %s)",
                (created, json.dumps(payload)),
            )
            snapshot_id = cursor.lastrowid
        connection.commit()
    return {"id": snapshot_id, "created_at": created, "payload": payload}


def _mysql_recent_snapshots(limit: int) -> list[dict[str, Any]]:
    with _mysql_connection() as connection:
        _ensure_mysql_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, created_at, payload FROM snapshots ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "payload": json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"],
        }
        for row in rows
    ]
