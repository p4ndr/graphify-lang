"""Shared fixture for the plugin corpus tests (plan 05 S6.1, M12)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def corpus_ls():
    """`git ls-files` for a checkout under ~/repos, a recursive glob for a
    checked-in sample under tests/lang/fixtures/."""
    def ls(root: Path, *patterns: str) -> list[str]:
        if (root / ".git").exists():
            return subprocess.run(["git", "-C", str(root), "ls-files", *patterns],
                                  capture_output=True, text=True, check=True).stdout.split()
        return sorted({p.relative_to(root).as_posix()
                       for pat in patterns for p in root.rglob(pat) if p.is_file()})
    return ls
