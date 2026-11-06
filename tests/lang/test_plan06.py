"""Plan 06: AutoLISP graph quality (shadow copies, miss and staleness lines, global and load edges)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import networkx as nx

from graphify.extract import extract
from graphify_lang._common import mark_shadows, pick_by_prefix

FNS = frozenset({"function", "command"})
LIB = "(defun a:one () 1)\n(defun a:two () 2)\n(defun a:three () 3)\n(defun a:four () 4)\n(defun a:five () 5)\n"


def _nodes(path: Path, labels: list[str]) -> list[dict]:
    sf = str(path)
    return [{"id": f"{path.parent.name}_file", "label": path.name, "source_file": sf, "source_location": "L1"}] + [
        {"id": f"{path.parent.name}_{x}", "label": x, "node_kind": "function", "source_file": sf} for x in labels]


def _git(root: Path, *args: str, when: str | None = None) -> None:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    if when:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = when
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def test_logs_copy_is_the_shadow(tmp_path):
    names = ["a:one", "a:two", "a:three", "a:four", "a:five"]
    live, copy = _nodes(tmp_path / "src" / "a.lsp", names), _nodes(tmp_path / "logs" / "a.lsp", names[:4])
    pairs = mark_shadows(live + copy, (".lsp",), FNS)
    assert pairs == [(str(tmp_path / "logs" / "a.lsp"), str(tmp_path / "src" / "a.lsp"), "path")]
    assert all(n.get("shadow_of") == "src_file" for n in copy)
    assert not any(n.get("shadow_of") for n in live)


def test_older_commit_is_the_shadow(tmp_path):
    for d in ("x", "y"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "a.lsp").write_text(LIB)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "x")
    _git(tmp_path, "commit", "-qm", "x", when="2026-01-01T00:00:00")
    _git(tmp_path, "add", "y")
    _git(tmp_path, "commit", "-qm", "y", when="2026-02-01T00:00:00")
    names = ["a:one", "a:two", "a:three", "a:four", "a:five"]
    nodes = _nodes(tmp_path / "x" / "a.lsp", names) + _nodes(tmp_path / "y" / "a.lsp", names)
    assert mark_shadows(nodes, (".lsp",), FNS) == [(str(tmp_path / "x" / "a.lsp"), str(tmp_path / "y" / "a.lsp"),
                                                    "older")]


def test_no_git_time_is_a_tie(tmp_path):
    names = ["a:one", "a:two", "a:three", "a:four", "a:five"]
    nodes = _nodes(tmp_path / "x" / "a.lsp", names) + _nodes(tmp_path / "y" / "a.lsp", names)
    assert mark_shadows(nodes, (".lsp",), FNS) == [(str(tmp_path / "x" / "a.lsp"), None, "tie")]
    assert not any(n.get("shadow_of") for n in nodes)


def test_under_overlap_is_not_a_shadow(tmp_path):
    live = _nodes(tmp_path / "src" / "a.lsp", ["a:one", "a:two", "a:three", "a:four", "a:five"])
    other = _nodes(tmp_path / "logs" / "a.lsp", ["a:one", "a:two", "a:three", "b:x", "b:y"])
    assert mark_shadows(live + other, (".lsp",), FNS) == []


def test_pick_by_prefix_drops_shadow_candidates():
    shadow = {"id": "s", "source_file": "logs/y.lsp", "shadow_of": "f"}
    assert pick_by_prefix([shadow, {"id": "l", "source_file": "src/y.lsp"}], "src/x.lsp") == ("l", "EXTRACTED")
    assert pick_by_prefix([shadow], "src/x.lsp") == ("s", "EXTRACTED")


def test_cross_file_call_into_a_shadowed_module_is_extracted(tmp_path):
    for d in ("src", "logs"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "lib.lsp").write_text(LIB)
    (tmp_path / "src" / "app.lsp").write_text("(defun app:go () (a:one))\n")
    files = sorted(p for p in tmp_path.rglob("*.lsp"))
    res = extract(files, cache_root=tmp_path / ".cache", root=tmp_path)
    labels = {n["id"]: n for n in res["nodes"]}
    calls = [e for e in res["edges"] if e["relation"] == "calls" and labels[e["target"]]["label"] == "a:one"]
    assert len(calls) == 1 and calls[0]["confidence"] == "EXTRACTED"
    assert "src" in str(labels[calls[0]["target"]]["source_file"]).replace("\\", "/").split("/")
    assert any(n.get("shadow_of") for n in res["nodes"] if "logs" in str(n.get("source_file")))


def test_shadow_caller_binds_inside_its_own_copy(tmp_path):
    app = "(defun app:go () (a:one))\n(defun app:a () 1)\n(defun app:b () 2)\n(defun app:c () 3)\n(defun app:d () 4)\n"
    for d in ("src", "logs"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "lib.lsp").write_text(LIB)
        (tmp_path / d / "app.lsp").write_text(app)
    res = extract(sorted(tmp_path.rglob("*.lsp")), cache_root=tmp_path / ".cache", root=tmp_path)
    nodes = {n["id"]: n for n in res["nodes"]}
    calls = sorted((nodes[e["source"]]["source_file"], nodes[e["target"]]["source_file"], e["confidence"])
                   for e in res["edges"] if e["relation"] == "calls" and nodes[e["target"]]["label"] == "a:one")
    assert calls == [("logs/app.lsp", "logs/lib.lsp", "EXTRACTED"), ("src/app.lsp", "src/lib.lsp", "EXTRACTED")]


def test_shadow_nodes_leave_god_nodes_and_lookups():
    from graphify.analyze import god_nodes
    from graphify.serve import _resolve_single_node, _score_nodes

    G = nx.Graph()
    G.add_node("live", label="a:x", source_file="src/a.lsp", node_kind="function")
    G.add_node("copy", label="a:x", source_file="logs/a.lsp", node_kind="function", shadow_of="f")
    G.add_node("only", label="a:old", source_file="logs/a.lsp", node_kind="function", shadow_of="f")
    for i in range(5):
        G.add_edge("copy", f"c{i}")
    G.add_edge("live", "c0")
    assert [g["id"] for g in god_nodes(G, top_n=1)] == ["live"]
    assert _resolve_single_node(G, "a:x") == ("live", None)
    assert _resolve_single_node(G, "a:old") == ("only", None)
    assert _score_nodes(G, ["a:x"])[0][1] == "live"
    assert _score_nodes(G, ["logs/a.lsp", "a:x"])[0][1] == "copy"


def test_report_lists_shadow_copies():
    from graphify.report import _shadow_section

    G = nx.Graph()
    G.add_node("live", source_file="src/a.lsp")
    G.add_node("s1", source_file="logs/a.lsp", shadow_of="live")
    lines = _shadow_section(G)
    assert "## Shadow copies (1 files)" in lines
    assert "- `logs/a.lsp` copies `src/a.lsp` - ignore line: `logs/a.lsp`" in lines
    assert _shadow_section(nx.Graph()) == []
    from graphify.report import generate
    text = generate(G, {}, {}, {}, [], [], {"total_files": 2, "total_words": 10}, {"input": 0, "output": 0}, "/r")
    assert "## Shadow copies (1 files)" in text
