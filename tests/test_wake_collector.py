import json
import sqlite3
from pathlib import Path

from wake_collector import record_event


def test_redacts_secret_and_records_event(tmp_path: Path):
    db = tmp_path / "memory.db"
    record_event({"repo": "demo", "instruction": "use api_key=topsecret", "outcome": "PASS"}, db)
    row = sqlite3.connect(db).execute("SELECT evidence_json FROM episodes").fetchone()
    assert row is not None
    assert "topsecret" not in row[0]
    assert "[REDACTED]" in row[0]


def test_enforces_byte_cap(tmp_path: Path):
    db = tmp_path / "memory.db"
    for i in range(3):
        record_event({"repo": "demo", "instruction": "x" * 100, "n": i}, db, max_bytes=250)
    count = sqlite3.connect(db).execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    assert count < 3
