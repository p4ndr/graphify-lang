"""Plan 04 S13 - cc-kb augment (graphify_lang/cc_kb): exact pins.

Fixture tree: tests/lang/fixtures/cc_kb/ (hubs XX000 and YY100, spokes
XX000.001 / .002, the -S001 spoke of XX000.001, scripts/tool.ps1, and a
README.md outside docs/). Core ``extract_markdown`` runs first; the augment
adds page-node attributes and the ``cc_kb_refs`` payload, and the resolver
turns that into edges.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from graphify.extract import _get_extractor, extract, extract_markdown
from graphify.lang_registry import format_languages

FIXTURE = Path(__file__).parent / "fixtures" / "cc_kb"
DOCS = FIXTURE / "docs"
ADDED = {"cc_id", "doc_class", "group", "subgroup", "is_hub", "spoke", "dangling_cc_refs"}


def test_listed_as_augment():
    row = next(line for line in format_languages().splitlines() if line.startswith("cc-kb "))
    assert "+.md" in row and "match" in row and row.rstrip().endswith("cc-kb")


def test_attrs_added_base_unchanged():
    doc = DOCS / "cc-XX000.001-S001.md"
    base, got = extract_markdown(doc), _get_extractor(doc)(doc)
    assert got["edges"] == base["edges"]
    assert [{k: v for k, v in n.items() if k not in ADDED} for n in got["nodes"]] == base["nodes"]
    assert {k: got["nodes"][0][k] for k in ADDED & set(got["nodes"][0])} == {
        "cc_id": "cc-XX000.001-S001", "doc_class": "XX", "group": "000",
        "subgroup": "001", "is_hub": False, "spoke": "S001"}
    hub = DOCS / "cc-XX000.000.md"
    assert _get_extractor(hub)(hub)["nodes"][0]["is_hub"] is True


def test_payload():
    doc = DOCS / "cc-XX000.001.md"
    refs = _get_extractor(doc)(doc)["cc_kb_refs"]
    assert refs["cc"] == [("cc-YY100.000", 3), ("cc-ZZ999.000", 3)]   # no self, no .2 version
    assert refs["code"] == [("scripts/tool.ps1", 4)]                # :line, alias, fence, missing


def test_outside_docs_not_augmented():
    readme = FIXTURE / "README.md"
    assert _get_extractor(readme)(readme) == extract_markdown(readme)


def _graph():
    paths = sorted(DOCS.glob("*.md")) + [FIXTURE / "scripts" / "tool.ps1"]
    res = extract(paths)
    label = {n["id"]: Path(n["source_file"]).name for n in res["nodes"] if n.get("source_file")}
    page = {Path(n["source_file"]).name: n for n in res["nodes"] if n.get("node_kind") == "page"}
    edges = sorted((label[e["source"]], label[e["target"]], e["relation"], e.get("context"))
                   for e in res["edges"] if e.get("context") in ("cc_ref", "hub_spoke", "code_ref"))
    return edges, page


def test_resolved_edges_and_dangling():
    edges, page = _graph()
    assert edges == [
        ("cc-XX000.000.md", "cc-XX000.001.md", "contains", "hub_spoke"),
        ("cc-XX000.001.md", "cc-XX000.001-S001.md", "contains", "hub_spoke"),
        ("cc-XX000.001.md", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.001.md", "tool.ps1", "cites", "code_ref"),
        # hub -> .002 is a Markdown link already (core `references`): no second edge
    ]
    assert page["cc-XX000.001.md"]["dangling_cc_refs"] == ["cc-ZZ999.000"]


def test_elements_switch_off(monkeypatch):
    monkeypatch.setenv("GRAPHIFY_CC_KB_OFF", "attrs,cc,hubs,code")
    doc = DOCS / "cc-XX000.001.md"
    assert _get_extractor(doc)(doc) == extract_markdown(doc)
