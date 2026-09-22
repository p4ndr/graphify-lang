#!/usr/bin/env python3
"""Dump the six core tables to tests/upstream_tables.json for rebase comparison."""

from __future__ import annotations

import json
from pathlib import Path


def read_table(path: Path, start_line: int, end_line: int | None = None) -> list[str]:
    """Read lines from a file (1-indexed, inclusive)."""
    lines = path.read_text().splitlines()
    start_idx = start_line - 1  # convert to 0-indexed
    if end_line is None:
        end_idx = len(lines)
    else:
        end_idx = end_line  # already 1-indexed, so slice will be exclusive
    return lines[start_idx:end_idx]


def main() -> None:
    repo_root = Path(__file__).parent.parent
    tables: dict[str, list[str]] = {}

    # graphify/extract.py:_DISPATCH (line 5733 ends the dict)
    extract_path = repo_root / "graphify" / "extract.py"
    # _DISPATCH starts around line 5630, ends at 5733
    tables["graphify/extract.py:_DISPATCH"] = read_table(extract_path, 5630, 5733)

    # graphify/extract.py:_EXTRA_FOR_EXTENSION (line 5755 ends the dict)
    tables["graphify/extract.py:_EXTRA_FOR_EXTENSION"] = read_table(extract_path, 5740, 5755)

    # graphify/detect.py:CODE_EXTENSIONS (line 54)
    detect_path = repo_root / "graphify" / "detect.py"
    tables["graphify/detect.py:CODE_EXTENSIONS"] = read_table(detect_path, 54, 54)

    # graphify/detect.py:DOC_EXTENSIONS (line 45)
    tables["graphify/detect.py:DOC_EXTENSIONS"] = read_table(detect_path, 45, 45)

    # graphify/detect.py:PAPER_EXTENSIONS (line 46)
    tables["graphify/detect.py:PAPER_EXTENSIONS"] = read_table(detect_path, 46, 46)

    # graphify/cli.py:_HOOK_SOURCE_EXTS
    cli_path = repo_root / "graphify" / "cli.py"
    # Find _HOOK_SOURCE_EXTS manually
    lines = cli_path.read_text().splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if "_HOOK_SOURCE_EXTS" in line and "=" in line:
            start_idx = i
            break

    if start_idx is not None:
        # Find the closing bracket/paren
        depth = 0
        end_idx = len(lines)
        for i in range(start_idx, len(lines)):
            for char in lines[i]:
                if char == "[" or char == "(":
                    depth += 1
                elif char == "]" or char == ")":
                    depth -= 1
            if depth == 0 and i > start_idx:
                end_idx = i + 1
                break
        tables["graphify/cli.py:_HOOK_SOURCE_EXTS"] = lines[start_idx:end_idx]
    else:
        raise ValueError("Could not find _HOOK_SOURCE_EXTS in cli.py")

    # Write to tests/upstream_tables.json
    output_path = repo_root / "tests" / "upstream_tables.json"
    output_path.write_text(json.dumps(tables, indent=2) + "\n")
    print(f"Wrote {len(tables)} tables to {output_path}")


if __name__ == "__main__":
    main()
