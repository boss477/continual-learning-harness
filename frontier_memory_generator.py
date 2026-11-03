"""Generate a bounded FrontierMemory export from the released trajectory corpus.

This adapter deliberately uses only corpus inputs and deterministic extraction so
the benchmark can attribute results to the harness rather than a second model.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
SIGNAL = re.compile(r"\b(do not|must|only|expected|requires?|remember|always|never)\b", re.I)


def messages(value: object):
    if isinstance(value, dict):
        if isinstance(value.get("message"), str):
            yield value["message"]
        for child in value.values():
            yield from messages(child)
    elif isinstance(value, list):
        for child in value:
            yield from messages(child)


def generate(corpus: Path, output: Path) -> dict:
    rules: set[str] = set()
    for path in sorted((corpus / "inputs").glob("*")):
        try:
            if path.suffix == ".jsonl":
                values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            elif path.suffix == ".json":
                values = [json.loads(path.read_text(encoding="utf-8"))]
            else:
                continue
        except (OSError, json.JSONDecodeError):
            continue
        for value in values:
            for message in messages(value):
                for sentence in re.split(r"(?<=[.!?])\s+", message):
                    sentence = re.sub(r"\s+", " ", sentence).strip()
                    if 20 <= len(sentence) <= 400 and SIGNAL.search(sentence):
                        rules.add(sentence)
    lines = ["# Codex Project Memory", "", "## Consolidated corpus rules", ""]
    for rule in sorted(rules):
        candidate = "\n".join(lines + [f"- {rule}", ""])
        if len(candidate.encode("utf-8")) > MAX_BYTES:
            break
        lines.extend([f"- {rule}", ""])
    output.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines).rstrip() + "\n"
    (output / "MEMORY.md").write_text(content, encoding="utf-8")
    manifest = {
        "format": 1,
        "generator": "continual-learning-harness/deterministic-v1",
        "rule_count": content.count("\n- "),
        "memory_bytes": len(content.encode("utf-8")),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.corpus, args.output), indent=2))


if __name__ == "__main__":
    main()
