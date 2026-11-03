"""T0 -> T1 consolidation with a deterministic fallback and hard candidate cap."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "memory.db"
SCHEMA_PATH = ROOT / "schema.sql"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return db


def normalize_rule(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def rule_hash(text: str) -> str:
    return hashlib.sha256(normalize_rule(text).encode("utf-8")).hexdigest()


def heuristic_rules(episodes: Iterable[sqlite3.Row]) -> list[str]:
    """Extract only explicit, actionable signals without inventing architecture."""
    rules: set[str] = set()
    for episode in episodes:
        outcome = (episode["outcome"] or "").upper()
        evidence = json.loads(episode["evidence_json"])
        corrections = evidence.get("corrections", [])
        for correction in corrections if isinstance(corrections, list) else []:
            text = str(correction).strip()
            if text:
                rules.add(f"User correction: {text}")
        if outcome == "FAIL":
            workaround = evidence.get("workaround")
            if workaround:
                rules.add(f"When this failure occurs, use: {str(workaround).strip()}")
    return sorted(rules)


def consolidate(
    path: Path = DB_PATH,
    max_candidates: int = 100,
    generator: Callable[[list[sqlite3.Row]], Iterable[str]] = heuristic_rules,
) -> int:
    db = connect(path)
    try:
        episodes = db.execute("SELECT * FROM episodes ORDER BY created_at ASC").fetchall()
        now = datetime.now(timezone.utc).isoformat()
        inserted = 0
        for text in generator(episodes):
            text = str(text).strip()
            if not text or len(text.encode("utf-8")) > 4096:
                continue
            digest = rule_hash(text)
            db.execute(
                """INSERT INTO candidates(id, repo, rule_text, rule_hash, score, status, created_at, updated_at)
                   VALUES (lower(hex(randomblob(16))), ?, ?, ?, 0, 'pending', ?, ?)
                   ON CONFLICT(rule_hash) DO NOTHING""",
                ("mixed", text, digest, now, now),
            )
            inserted += db.execute("SELECT changes()").fetchone()[0]
        db.execute(
            """DELETE FROM candidates WHERE id IN (
                SELECT id FROM candidates WHERE status = 'pending'
                ORDER BY score ASC, created_at ASC
                LIMIT MAX(0, (SELECT COUNT(*) FROM candidates WHERE status = 'pending') - ?)
            )""",
            (max_candidates,),
        )
        db.commit()
        return inserted
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolidate T0 evidence into T1 candidates")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--max-candidates", type=int, default=100)
    args = parser.parse_args()
    print(consolidate(args.db, args.max_candidates))


if __name__ == "__main__":
    main()
