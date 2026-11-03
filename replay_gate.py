"""Replay and promotion gate for T1 candidates."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "memory.db"
SCHEMA_PATH = ROOT / "schema.sql"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return db


def verify_and_promote(
    candidate_id: str,
    verifier: Callable[[str], bool],
    path: Path = DB_PATH,
) -> bool:
    db = connect(path)
    try:
        candidate = db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None or candidate["status"] != "pending":
            return False
        try:
            passed = bool(verifier(candidate["rule_text"]))
        except Exception:
            passed = False
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        if not passed:
            db.execute("UPDATE candidates SET status = 'rejected', updated_at = ? WHERE id = ?", (now, candidate_id))
            db.commit()
            return False
        db.execute(
            """INSERT INTO rules(id, repo, rule_text, rule_hash, created_at, updated_at)
               VALUES (lower(hex(randomblob(16))), ?, ?, ?, ?, ?)
               ON CONFLICT(rule_hash) DO UPDATE SET updated_at = excluded.updated_at""",
            (candidate["repo"], candidate["rule_text"], candidate["rule_hash"], now, now),
        )
        db.execute("UPDATE candidates SET status = 'promoted', updated_at = ? WHERE id = ?", (now, candidate_id))
        db.commit()
        return True
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a verified T1 candidate")
    parser.add_argument("candidate_id")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--accept", action="store_true", help="accept after an external replay has passed")
    args = parser.parse_args()
    if not args.accept:
        raise SystemExit("refusing to promote without an explicit replay result")
    print(verify_and_promote(args.candidate_id, lambda _rule: True, args.db))


if __name__ == "__main__":
    main()
