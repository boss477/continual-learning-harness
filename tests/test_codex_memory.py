import json
import sqlite3
from pathlib import Path

from codex_memory import export_memory


def test_export_is_bounded_and_self_contained(tmp_path: Path):
    db = tmp_path / "memory.db"
    sqlite3.connect(db).executescript(
        """CREATE TABLE rules (id TEXT, repo TEXT, rule_text TEXT, rule_hash TEXT, reuse_count INTEGER, created_at TEXT, updated_at TEXT);
        INSERT INTO rules VALUES ('1','demo','Run lint before tests','a',2,'','');
        INSERT INTO rules VALUES ('2','other','Do not leak this','b',9,'','');"""
    )
    out = tmp_path / "memory"
    manifest = export_memory(db, out, "demo", max_bytes=200)
    assert manifest["rule_count"] == 1
    assert manifest["memory_bytes"] <= 200
    assert "Run lint before tests" in (out / "MEMORY.md").read_text()
    assert "Do not leak this" not in (out / "MEMORY.md").read_text()
    assert json.loads((out / "manifest.json").read_text())["repo"] == "demo"
