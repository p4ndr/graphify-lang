"""Plan 04 S13 - cc-kb augment (graphify_lang/cc_kb): exact pins.

Fixture tree: tests/lang/fixtures/cc_kb/ (hubs XX000 and YY100, spokes
XX000.001 / .002, the -S001 spoke of XX000.001, scripts/tool.ps1, a root
README.md, agents/ag-x.md, skills/s/SKILL.md and docs/notes.md; .002 has a
mention above its first heading and in two sections) and
tests/lang/fixtures/cc_kb_plain/ (a repo whose docs/ holds no cc-*.md). Core ``extract_markdown`` runs first; the augment
adds page-node attributes and the ``cc_kb_refs`` payload, and the resolver
turns that into edges.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from graphify.extract import _get_extractor, extract, extract_markdown
from graphify.lang_registry import format_languages

FIXTURE = Path(__file__).parent / "fixtures" / "cc_kb"
PLAIN = Path(__file__).parent / "fixtures" / "cc_kb_plain"
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
    # :line, alias, fence; a missing file stays in the payload, the resolver drops it (H3)
    assert refs["code"] == [("scripts/none.ps1", 4), ("scripts/tool.ps1", 4)]
    assert refs["cc_heads"] == [("cc-YY100.000", 3, 1), ("cc-ZZ999.000", 3, 1)]
    assert refs["code_heads"] == [("scripts/none.ps1", 4, 1), ("scripts/tool.ps1", 4, 1)]
    assert refs["up"] == [2, 1]


def test_heads_payload_per_section():
    """D12: (ref, line, node) per section; nothing for text above the first heading."""
    doc = DOCS / "cc-XX000.002.md"
    got = _get_extractor(doc)(doc)
    assert [n["label"] for n in got["nodes"]] == [
        "cc-XX000.002.md", "XX spoke two", "Second section", "Third section"]
    refs = got["cc_kb_refs"]
    assert refs["cc"] == [("cc-YY100.000", 1), ("cc-ZZ999.000", 7)]
    assert refs["cc_heads"] == [("cc-YY100.000", 7, 2), ("cc-YY100.000", 11, 3),
                                ("cc-ZZ999.000", 7, 2)]
    assert refs["code_heads"] == [("scripts/tool.ps1", 7, 2)]


def test_root_agent_skill_payload_no_attrs():
    """D11: refs only; no attrs, no hub step, base nodes unchanged."""
    for rel, up in (("README.md", [1]), ("agents/ag-x.md", [1, 2]), ("skills/s/SKILL.md", [1, 3])):
        p = FIXTURE / rel
        got, base = _get_extractor(p)(p), extract_markdown(p)
        assert got["nodes"] == base["nodes"] and got["edges"] == base["edges"], rel
        assert got["cc_kb_refs"]["up"][:len(up)] == up and got["cc_kb_refs"]["hubs"] is False, rel
    odd = DOCS / "cc-XX000.001.squad-check.md"   # docs/cc-* off-schema: refs, no attrs
    got = _get_extractor(odd)(odd)
    assert got["nodes"] == extract_markdown(odd)["nodes"] and got["cc_kb_refs"]["cc"] == [
        ("cc-YY100.000", 3)]
    assert _get_extractor(FIXTURE / "agents/ag-x.md")(FIXTURE / "agents/ag-x.md")[
        "cc_kb_refs"]["code"] == [("scripts/tool.ps1", 3)]


@pytest.mark.parametrize("path", [FIXTURE / "docs" / "notes.md", PLAIN / "README.md",
                                  PLAIN / "docs" / "guide.md", PLAIN / "agents" / "a.md"])
def test_out_of_scope_unchanged(path, tmp_path):
    """The augment cannot see its scope (H3): nodes and edges are the base ones,
    and the resolver, finding no graphed harness root, adds nothing."""
    got, base = _get_extractor(path)(path), extract_markdown(path)
    assert got["nodes"] == base["nodes"] and got["edges"] == base["edges"]
    res = extract([path], cache_root=tmp_path)
    assert not [e for e in res["edges"] if e.get("context") in ("cc_ref", "hub_spoke", "code_ref")]


def _graph(cache):
    paths = (sorted(DOCS.glob("*.md")) + [FIXTURE / "scripts" / "tool.ps1", FIXTURE / "README.md",
             FIXTURE / "agents" / "ag-x.md", FIXTURE / "skills" / "s" / "SKILL.md"])
    res = extract(paths, cache_root=cache)   # the AST cache key does not cover plugin code
    label = {n["id"]: Path(n["source_file"]).name + ("#" + n["label"] if n.get("node_kind") == "heading"
             else "") for n in res["nodes"] if n.get("source_file")}
    page = {Path(n["source_file"]).name: n for n in res["nodes"] if n.get("node_kind") == "page"}
    edges = sorted((label[e["source"]], label[e["target"]], e["relation"], e.get("context"))
                   for e in res["edges"] if e.get("context") in ("cc_ref", "hub_spoke", "code_ref"))
    return edges, page


def test_resolved_edges_and_dangling(tmp_path):
    """Page-level edges as before; D12 adds heading -> target on top (new pairs)."""
    edges, page = _graph(tmp_path)
    assert edges == [
        ("README.md", "cc-XX000.000.md", "cites", "cc_ref"),
        ("README.md", "tool.ps1", "cites", "code_ref"),
        ("README.md#Root file", "cc-XX000.000.md", "cites", "cc_ref"),
        ("README.md#Root file", "tool.ps1", "cites", "code_ref"),
        ("SKILL.md", "cc-XX000.002.md", "cites", "cc_ref"),
        ("SKILL.md#Skill", "cc-XX000.002.md", "cites", "cc_ref"),
        ("ag-x.md", "cc-YY100.000.md", "cites", "cc_ref"),
        ("ag-x.md", "tool.ps1", "cites", "code_ref"),
        ("ag-x.md#Agent", "cc-YY100.000.md", "cites", "cc_ref"),
        ("ag-x.md#Agent", "tool.ps1", "cites", "code_ref"),
        ("cc-XX000.000.md", "cc-XX000.001.md", "contains", "hub_spoke"),
        # hub -> .002 is a Markdown link already (core `references`): no page edge;
        # the heading pairs are new
        ("cc-XX000.000.md#XX hub", "cc-XX000.001.md", "cites", "cc_ref"),
        ("cc-XX000.000.md#XX hub", "cc-XX000.002.md", "cites", "cc_ref"),
        ("cc-XX000.001-S001.md#Spoke S001 of cc-XX000.001", "cc-XX000.001.md", "cites", "cc_ref"),
        ("cc-XX000.001.md", "cc-XX000.001-S001.md", "contains", "hub_spoke"),
        ("cc-XX000.001.md", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.001.md", "tool.ps1", "cites", "code_ref"),
        ("cc-XX000.001.md#XX spoke one", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.001.md#XX spoke one", "tool.ps1", "cites", "code_ref"),
        ("cc-XX000.001.squad-check.md", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.001.squad-check.md#Review of XX000.001", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.002.md", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.002.md", "tool.ps1", "cites", "code_ref"),
        ("cc-XX000.002.md#Second section", "cc-YY100.000.md", "cites", "cc_ref"),
        ("cc-XX000.002.md#Second section", "tool.ps1", "cites", "code_ref"),
        ("cc-XX000.002.md#Third section", "cc-YY100.000.md", "cites", "cc_ref"),
    ]
    assert page["cc-XX000.002.md"]["dangling_cc_refs"] == ["cc-ZZ999.000"]
    assert page["cc-XX000.001.md"]["dangling_cc_refs"] == ["cc-ZZ999.000"]
    assert page["SKILL.md"]["dangling_cc_refs"] == ["cc-ZZ999.000"]
    assert "cc_id" not in page["README.md"]


def test_elements_switch_off(monkeypatch):
    monkeypatch.setenv("GRAPHIFY_CC_KB_OFF", "attrs,cc,hubs,code")
    doc = DOCS / "cc-XX000.001.md"
    assert _get_extractor(doc)(doc) == extract_markdown(doc)
