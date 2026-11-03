import json
import sqlite3
from pathlib import Path

from sleep_engine import consolidate
from wake_collector import record_event


def test_consolidates_explicit_signals_only(tmp_path: Path):
    db = tmp_path / "memory.db"
    record_event({"repo": "demo", "outcome": "FAIL", "workaround": "run lint first"}, db)
    record_event({"repo": "demo", "outcome": "PASS", "corrections": ["Use src/ for modules"]}, db)
    assert consolidate(db) == 2
    rows = sqlite3.connect(db).execute("SELECT rule_text FROM candidates ORDER BY rule_text").fetchall()
    assert [row[0] for row in rows] == ["User correction: Use src/ for modules", "When this failure occurs, use: run lint first"]


def test_deduplicates_candidates(tmp_path: Path):
    db = tmp_path / "memory.db"
    record_event({"repo": "demo", "corrections": ["Use src/ for modules"]}, db)
    assert consolidate(db) == 1
    assert consolidate(db) == 0
    count = sqlite3.connect(db).execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    assert count == 1
