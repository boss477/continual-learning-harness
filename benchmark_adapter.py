"""FrontierMemory-compatible export validation and local score reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_memory(memory_dir: Path, max_bytes: int = 51200) -> dict:
    memory = memory_dir / "MEMORY.md"
    manifest = memory_dir / "manifest.json"
    if not memory.is_file() or not manifest.is_file():
        raise ValueError("memory export must contain MEMORY.md and manifest.json")
    content = memory.read_text(encoding="utf-8")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    size = len(content.encode("utf-8"))
    if size > max_bytes:
        raise ValueError(f"MEMORY.md exceeds {max_bytes} bytes")
    if data.get("memory_bytes") != size:
        raise ValueError("manifest memory_bytes does not match MEMORY.md")
    if data.get("rule_count", 0) != content.count("\n- "):
        raise ValueError("manifest rule_count does not match MEMORY.md")
    return {"valid": True, "memory_bytes": size, "rule_count": data.get("rule_count", 0)}


def report(control_passes: int, memory_passes: int, total_tasks: int, output: Path) -> dict:
    result = {
        "total_tasks": total_tasks,
        "control_pass_rate": control_passes / total_tasks if total_tasks else 0,
        "memory_pass_rate": memory_passes / total_tasks if total_tasks else 0,
        "absolute_gain": (memory_passes - control_passes) / total_tasks if total_tasks else 0,
        "control_passes": control_passes,
        "memory_passes": memory_passes,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate/export benchmark artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate")
    check.add_argument("memory", type=Path)
    report_parser = sub.add_parser("report")
    report_parser.add_argument("--control", type=int, required=True)
    report_parser.add_argument("--memory", type=int, required=True)
    report_parser.add_argument("--tasks", type=int, default=15)
    report_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        print(json.dumps(validate_memory(args.memory), indent=2))
    else:
        print(json.dumps(report(args.control, args.memory, args.tasks, args.out), indent=2))


if __name__ == "__main__":
    main()
