"""Export approved T2 rules in a compact Codex-loadable format."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"


def export_memory(db_path: Path, output_dir: Path, repo: str, max_bytes: int = 51200) -> dict:
    db = sqlite3.connect(db_path)
    try:
        db.row_factory = sqlite3.Row
        db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        rows = db.execute(
            "SELECT rule_text FROM rules WHERE repo = ? ORDER BY reuse_count DESC, updated_at DESC",
            (repo,),
        ).fetchall()
    finally:
        db.close()
    lines = ["# Codex Project Memory", "", f"Repository: `{repo}`", "", "## Verified rules", ""]
    for row in rows:
        line = f"- {row['rule_text']}"
        candidate = "\n".join(lines + [line, ""])
        if len(candidate.encode("utf-8")) > max_bytes:
            break
        lines.extend([line, ""])
    content = "\n".join(lines).rstrip() + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "MEMORY.md").write_text(content, encoding="utf-8")
    manifest = {
        "format": 1,
        "repo": repo,
        "rule_count": content.count("\n- "),
        "memory_bytes": len(content.encode("utf-8")),
        "source_trajectories": 0,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Export approved Codex memory")
    parser.add_argument("repo")
    parser.add_argument("output", type=Path)
    parser.add_argument("--db", type=Path, default=ROOT / "memory.db")
    parser.add_argument("--max-bytes", type=int, default=51200)
    args = parser.parse_args()
    print(json.dumps(export_memory(args.db, args.output, args.repo, args.max_bytes), indent=2))


if __name__ == "__main__":
    main()
