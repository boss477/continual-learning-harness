"""Bounded, redacting T0 collector for coding-agent session evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "memory.db"
SCHEMA_PATH = ROOT / "schema.sql"

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----", re.S),
    re.compile(r"\b(?:ghp|github_pat|sk|xox[baprs])_[A-Za-z0-9_\-]{12,}\b"),
]


def redact(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if not isinstance(value, str):
        return value
    result = value
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return connection


def prune(connection: sqlite3.Connection, max_bytes: int = 500 * 1024 * 1024) -> None:
    now = utc_now().isoformat()
    connection.execute("DELETE FROM episodes WHERE expires_at <= ?", (now,))
    total = connection.execute("SELECT COALESCE(SUM(byte_size), 0) FROM episodes").fetchone()[0]
    while total > max_bytes:
        row = connection.execute(
            "SELECT id, byte_size FROM episodes ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            break
        connection.execute("DELETE FROM episodes WHERE id = ?", (row["id"],))
        total -= row["byte_size"]


def record_event(event: dict, path: Path = DB_PATH, max_bytes: int = 500 * 1024 * 1024) -> str:
    safe_event = redact(event)
    now = utc_now()
    payload = json.dumps(safe_event, ensure_ascii=False, separators=(",", ":"))
    event_id = str(uuid.uuid4())
    repo = str(safe_event.get("repo", "unknown"))
    instruction = safe_event.get("instruction")
    outcome = safe_event.get("outcome")
    connection = connect(path)
    try:
        connection.execute(
            """INSERT INTO episodes
               (id, repo, created_at, instruction, outcome, evidence_json, byte_size, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, repo, now.isoformat(), instruction, outcome, payload,
             len(payload.encode("utf-8")), (now + timedelta(days=7)).isoformat()),
        )
        prune(connection, max_bytes=max_bytes)
        connection.commit()
    finally:
        connection.close()
    return event_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Record bounded Codex wake-phase evidence")
    parser.add_argument("event", type=Path, help="JSON event file")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    event = json.loads(args.event.read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise SystemExit("event must be a JSON object")
    print(record_event(event, args.db))


if __name__ == "__main__":
    main()
