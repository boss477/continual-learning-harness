import sqlite3
from pathlib import Path

from replay_gate import verify_and_promote
from sleep_engine import consolidate
from wake_collector import record_event


def candidate_id(db: Path) -> str:
    return sqlite3.connect(db).execute("SELECT id FROM candidates").fetchone()[0]


def test_failed_replay_quarantines_candidate(tmp_path: Path):
    db = tmp_path / "memory.db"
    record_event({"repo": "demo", "corrections": ["Use src"]}, db)
    consolidate(db)
    assert not verify_and_promote(candidate_id(db), lambda _: False, db)
    assert sqlite3.connect(db).execute("SELECT status FROM candidates").fetchone()[0] == "rejected"


def test_passed_replay_promotes_rule(tmp_path: Path):
    db = tmp_path / "memory.db"
    record_event({"repo": "demo", "corrections": ["Use src"]}, db)
    consolidate(db)
    assert verify_and_promote(candidate_id(db), lambda rule: "Use src" in rule, db)
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM rules").fetchone()[0] == 1
