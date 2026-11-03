import json
from pathlib import Path

from benchmark_adapter import report, validate_memory


def test_validates_frontier_export(tmp_path: Path):
    out = tmp_path / "memory"
    out.mkdir()
    text = "# Codex Project Memory\n\n- Use src\n"
    (out / "MEMORY.md").write_text(text)
    (out / "manifest.json").write_text(json.dumps({"memory_bytes": len(text.encode()), "rule_count": 1}))
    assert validate_memory(out)["valid"]


def test_reports_gain(tmp_path: Path):
    result = report(5, 8, 15, tmp_path / "report.json")
    assert result["absolute_gain"] == 0.2
    assert json.loads((tmp_path / "report.json").read_text())["memory_passes"] == 8
