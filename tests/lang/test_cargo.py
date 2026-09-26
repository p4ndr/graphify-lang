"""Plan 04 S10 - cargo augment (graphify_lang/cargo): exact pins.

Fixture tree: tests/lang/fixtures/cargo/ (a virtual workspace: members
``crates/*`` + ``tools/gen``, ``crates/skip`` excluded). Core
``extract_package_manifest`` runs first; the augment adds the workspace node
and the ``cargo_refs`` payload; the resolver adds ``has_member`` edges,
``external_deps``, and the edge for a renamed path dep (plan 05 S4, H3).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from graphify.extract import _get_extractor, extract
from graphify.lang_registry import format_languages
from graphify.manifest_ingest import extract_package_manifest

FIXTURE = Path(__file__).parent / "fixtures" / "cargo"
MEMBERS = ["pkg_demo_cli", "pkg_demo_core", "pkg_demo_gen"]


def _rel(relation: str, result: dict) -> list[tuple[str, str]]:
    return sorted((e["source"], e["target"]) for e in result["edges"] if e["relation"] == relation)


def test_cargo_listed_as_augment():
    row = next(line for line in format_languages().splitlines() if line.startswith("cargo "))
    assert "+.toml" in row and "match" in row


def test_virtual_root_gets_workspace_and_payload():
    """The augment reads only its own file (H3): members are a payload."""
    root = FIXTURE / "Cargo.toml"
    assert extract_package_manifest(root) == {"nodes": [], "edges": []}
    got = _get_extractor(root)(root)
    assert [(n["id"], n["type"]) for n in got["nodes"]] == [("cargo_workspace_cargo", "workspace")]
    assert got["nodes"][0]["cargo_ws_deps"] == ["demo-core=demo-core@path", "serde=serde"]
    assert got["edges"] == []
    assert got["cargo_refs"]["workspace"] == {"id": "cargo_workspace_cargo",
                                              "members": ["crates/*", "tools/gen"],
                                              "exclude": ["crates/skip"]}


def test_crate_keeps_base_and_carries_deps():
    cli = FIXTURE / "crates" / "cli" / "Cargo.toml"
    base, got = extract_package_manifest(cli), _get_extractor(cli)(cli)
    assert got["edges"] == base["edges"] and got["nodes"] == base["nodes"]
    assert got["cargo_refs"]["crate"] == {"id": "pkg_demo_cli", "external": ["clap", "windows"],
                                          "renamed": ["demo-gen"], "inherit": ["demo-core="]}


def test_pipeline_external_and_renamed():
    files = sorted(FIXTURE.rglob("Cargo.toml"))
    with tempfile.TemporaryDirectory() as cache:
        result = extract(files, cache_root=Path(cache), root=FIXTURE)
    by_id = {n["id"]: n for n in result["nodes"]}
    assert by_id["pkg_demo_cli"]["external_deps"] == ["clap", "windows"]
    assert by_id["pkg_demo_core"]["external_deps"] == ["serde"]   # workspace-inherited external
    assert ("pkg_demo_cli", "pkg_demo_gen") in _rel("depends_on", result)


def test_pyproject_untouched():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "pyproject.toml"
        p.write_text("[project]\nname = 'x'\ndependencies = ['requests']\n", encoding="utf-8")
        assert _get_extractor(p) is extract_package_manifest


def test_pipeline_member_edges_resolve():
    files = sorted(FIXTURE.rglob("Cargo.toml"))
    with tempfile.TemporaryDirectory() as cache:
        result = extract(files, cache_root=Path(cache), root=FIXTURE)
    ids = {n["id"] for n in result["nodes"]}
    members = [t for s, t in _rel("has_member", result)]
    assert members == MEMBERS and set(members) <= ids
