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


def _qgraph() -> nx.Graph:
    G = nx.Graph()
    G.add_node("a", label="ust:rget", source_file="src/a.lsp")
    G.add_node("b", label="Say()", source_file="src/b.cs")
    G.add_edge("a", "b")
    return G


def test_query_names_a_symbol_it_could_not_find():
    from graphify.serve import _query_graph_text

    text = _query_graph_text(_qgraph(), "ust:bench-say callers")
    assert text.splitlines()[0].startswith("no exact match for 'ust:bench-say'; nearest: ")
    assert not _query_graph_text(_qgraph(), "ust:rget").startswith("no exact match")
    assert not _query_graph_text(_qgraph(), "say callers").startswith("no exact match")


def test_query_names_a_stale_graph(tmp_path):
    from graphify.serve import _query_graph_text

    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("1")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-qm", "one")
    built = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()
    (tmp_path / "graphify-out").mkdir()
    gp = str(tmp_path / "graphify-out" / "graph.json")
    G = _qgraph()
    G.graph["built_at_commit"] = built
    assert "graph built at" not in _query_graph_text(G, "ust:rget", graph_path=gp)
    (tmp_path / "a.txt").write_text("2")
    _git(tmp_path, "commit", "-qam", "two")
    first = _query_graph_text(G, "ust:rget", graph_path=gp).splitlines()[0]
    assert first.startswith(f"graph built at {built[:8]}, HEAD is ") and "(1 commits); run graphify update " in first


def test_loaded_graph_keeps_built_at_commit(tmp_path):
    import json

    from graphify.serve import _load_graph

    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps({"directed": False, "multigraph": False, "graph": {}, "nodes": [{"id": "a"}],
                              "links": [], "built_at_commit": "abc123"}))
    assert _load_graph(str(gp)).graph["built_at_commit"] == "abc123"


def test_cli_query_prints_the_staleness_line(tmp_path):
    import json
    import sys

    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("1")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-qm", "one")
    (tmp_path / "graphify-out").mkdir()
    gp = tmp_path / "graphify-out" / "graph.json"
    gp.write_text(json.dumps({"directed": False, "multigraph": False, "graph": {},
                              "nodes": [{"id": "a", "label": "ust:rget", "source_file": "a.lsp"}],
                              "links": [], "built_at_commit": "0" * 40}))
    out = subprocess.run([sys.executable, "-m", "graphify", "query", "ust:rget", "--graph", str(gp)],
                         capture_output=True, text=True, cwd=tmp_path)
    assert "graph built at 00000000, HEAD is " in out.stdout, out.stdout + out.stderr


def _build(tmp_path, files: dict[str, str]) -> tuple[dict, dict]:
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    res = extract(sorted(tmp_path.rglob("*.lsp")), cache_root=tmp_path / ".cache", root=tmp_path)
    return res, {n["id"]: n for n in res["nodes"]}


def _rel(res: dict, nodes: dict, relation: str) -> list[tuple]:
    return sorted((nodes[e["source"]]["label"], nodes[e["target"]]["label"], e["confidence"])
                  for e in res["edges"] if e["relation"] == relation)


def test_global_reads_and_writes(tmp_path):
    res, nodes = _build(tmp_path, {
        "a.lsp": "(setq *cfg* nil)\n(defun a:get () (car *cfg*))\n",
        "b.lsp": "(defun b:set (v) (setq *cfg* v *only* 1) (list *cfg* 'x))\n",
    })
    assert _rel(res, nodes, "reads_global") == [("a:get", "*cfg*", "EXTRACTED"), ("b:set", "*cfg*", "EXTRACTED")]
    assert _rel(res, nodes, "writes_global") == [("b:set", "*cfg*", "EXTRACTED"), ("b:set", "*only*", "EXTRACTED")]
    only = [n for n in nodes.values() if n.get("label") == "*only*"]
    assert len(only) == 1 and only[0]["node_kind"] == "global" and only[0].get("confidence") == "INFERRED"
    targets = {nodes[e["target"]]["source_file"] for e in res["edges"] if e["relation"] == "reads_global"}
    assert targets == {"a.lsp"}


def test_load_and_autoload_edges(tmp_path):
    res, nodes = _build(tmp_path, {
        "main.lsp": '(load "lib/util")\n(autoload "tools.fas" \'("TL"))\n(load "gone.lsp")\n'
                    "(defun m:go (f) (load f))\n",
        "lib/util.lsp": "(defun u:x () 1)\n",
        "tools.lsp": "(defun t:x () 1)\n",
    })
    deps = sorted((nodes[e["source"]]["source_file"], nodes[e["target"]]["source_file"])
                  for e in res["edges"] if e["relation"] == "module_depends")
    assert deps == [("main.lsp", "lib/util.lsp"), ("main.lsp", "tools.lsp")]
    main = next(n for n in nodes.values() if n["source_file"] == "main.lsp" and n.get("node_kind") == "file")
    assert main.get("unresolved_loads") == ["gone.lsp"]


def test_report_lists_unresolved_loads():
    from graphify.report import _unresolved_loads_section, generate

    G = nx.Graph()
    G.add_node("m", source_file="main.lsp", unresolved_loads=["gone.lsp"])
    assert _unresolved_loads_section(G) == ["", "## Unresolved loads (1)",
                                            "- `main.lsp` loads `gone.lsp`: no such file in the graph"]
    text = generate(G, {}, {}, {}, [], [], {"total_files": 1, "total_words": 1}, {"input": 0, "output": 0}, "/r")
    assert "## Unresolved loads (1)" in text


def test_defun_set_global_in_two_sibling_files_still_links(tmp_path):
    res, nodes = _build(tmp_path, {
        "x/a.lsp": "(defun a:set () (setq *g* 1))\n",
        "x/b.lsp": "(defun b:set () (setq *g* 2))\n",
        "x/c.lsp": "(defun c:get () *g*)\n",
    })
    writes = sorted((nodes[e["source"]]["label"], nodes[e["target"]]["source_file"])
                    for e in res["edges"] if e["relation"] == "writes_global")
    assert writes == [("a:set", "x/a.lsp"), ("b:set", "x/b.lsp")]
    assert _rel(res, nodes, "reads_global") == [("c:get", "*g*", "INFERRED")]
