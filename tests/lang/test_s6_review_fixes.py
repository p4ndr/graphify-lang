"""Plan 05 review-fix pass, S006 (cc-CR000.003 S6-*).

S6-N4: ``corpus_ls`` keeps a tracked name with a space whole. S6-L4: the
manifest has no unread ``fixture`` field. Owner decision on S5-M2: the cc-kb
watch rule also claims every ``docs/cc-*.md`` by file name alone, so a new
spoke refreshes its hub -> spoke edges.
"""
from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path

import pytest


def test_s6_n4_corpus_ls_keeps_spaced_names(tmp_path, corpus_ls):
    (tmp_path / "a b.cls").write_text("x\n")
    (tmp_path / "c.cls").write_text("x\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    assert sorted(corpus_ls(tmp_path, "*.cls")) == ["a b.cls", "c.cls"]


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S6-L4: LanguageManifest.fixture is set by nothing and read by nothing")
def test_s6_l4_manifest_has_no_fixture_field():
    from graphify_lang.manifest import LanguageManifest

    assert "fixture" not in {f.name for f in dataclasses.fields(LanguageManifest)}


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S5-M2 owner rule: docs/cc-*.md is claimed by name alone")
def test_s6_cc_kb_watch_claims_cc_docs_by_name(tmp_path):
    import graphify.extract  # noqa: F401  (applies the registry)
    import graphify.lang_registry as core

    pages = {
        "docs/cc-XX000.000.md": "# Hub\n",                # no mention, no path
        "docs/cc-XX000.000-S001.md": "# Spoke\n",         # a new spoke
        "docs/notes.md": "# Notes\n",                     # not a cc doc
        "agents/cc-XX000.001.md": "# Not under docs\n",   # cc name, not in docs/
    }
    for rel, text in pages.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    assert {rel: core.watch_claims(tmp_path / rel) for rel in pages} == {
        "docs/cc-XX000.000.md": True,
        "docs/cc-XX000.000-S001.md": True,
        "docs/notes.md": False,
        "agents/cc-XX000.001.md": False,
    }
