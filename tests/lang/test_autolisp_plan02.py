"""Plan 02 (case 003 defects) — exact node / edge pins for the AutoLISP plugin.

Fixture tree: tests/lang/fixtures/plan02/src/ (lib.lsp, app.lsp, broken.lsp,
lib.md, ui/dlg.dcl). Runs the real ``graphify.extract.extract`` pipeline, so the
registry dispatch, the cross-file resolver and the id remap are all exercised.
"""
from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest

from graphify.extract import extract

FIXTURE = Path(__file__).parent / "fixtures" / "plan02"
LISP_SUFFIXES = (".lsp", ".dcl")


@pytest.fixture(scope="module")
def graph(tmp_path_factory):
    root = tmp_path_factory.mktemp("plan02")
    shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    result = extract(files, cache_root=tmp_path_factory.mktemp("cache"), root=root)
    return result


def _ours(graph):
    return [n for n in graph["nodes"] if str(n.get("source_file", "")).endswith(LISP_SUFFIXES)]


def _labels(graph):
    return {n["id"]: n.get("label") for n in graph["nodes"]}


def _edges(graph, relation):
    lab = _labels(graph)
    return sorted(
        (lab.get(e["source"]), lab.get(e["target"]))
        for e in graph["edges"]
        if e["relation"] == relation
    )


def test_nodes_exact(graph):
    got = Counter((Path(n["source_file"]).name, n.get("node_kind"), n["label"]) for n in _ours(graph))
    want = Counter({
        ("lib.lsp", "file", "lib.lsp"): 1,
        ("lib.lsp", "module", "lib"): 1,
        ("lib.lsp", "global", "*lib:count*"): 1,
        ("lib.lsp", "global", "*lib:name*"): 1,
        ("lib.lsp", "function", "lib:helper"): 1,
        ("lib.lsp", "function", "lib:dup"): 2,
        ("lib.lsp", "command", "C:LibCmd"): 1,
        ("lib.lsp", "command", "C:log:list-vars"): 1,
        ("app.lsp", "file", "app.lsp"): 1,
        ("app.lsp", "module", "app"): 1,
        ("app.lsp", "global", "*app:state*"): 1,
        ("app.lsp", "function", "app:run"): 1,
        ("app.lsp", "function", "app:local"): 1,
        ("app.lsp", "function", "app:on-ok"): 1,
        ("app.lsp", "function", "app:show"): 1,
        ("broken.lsp", "file", "broken.lsp"): 1,
        ("broken.lsp", "function", "ok1"): 1,
        ("broken.lsp", "function", "bad1"): 1,
        ("broken.lsp", "function", "after1"): 1,
        ("broken.lsp", "function", "after2"): 1,
        ("dlg.dcl", "file", "dlg.dcl"): 1,
        ("dlg.dcl", "dialog", "app_dlg"): 1,
        ("dlg.dcl", "dialog", "other_dlg"): 1,
    })
    assert got == want


def test_every_node_has_label_and_source(graph):
    for n in _ours(graph):
        assert n.get("label") and n.get("source_file"), n


def test_no_duplicate_ids(graph):
    ids = [n["id"] for n in graph["nodes"]]
    assert len(ids) == len(set(ids))


def test_in_file_collision_gets_line_suffix(graph):
    dups = sorted(n["id"] for n in _ours(graph) if n["label"] == "lib:dup")
    assert dups[0].endswith("lib_dup") and dups[1].endswith("lib_dup_l13")


def test_parse_error_fallback_is_inferred(graph):
    broken = {n["label"]: n for n in _ours(graph) if n["source_file"].endswith("broken.lsp")}
    assert broken["ok1"].get("confidence", "EXTRACTED") == "EXTRACTED"
    # Whatever tree-sitter drops after the ERROR node comes back from the regex.
    assert any(n.get("confidence") == "INFERRED" for n in broken.values())


def test_contains_edges(graph):
    contains = _edges(graph, "contains")
    for n in _ours(graph):
        if n.get("node_kind") != "file":
            assert (Path(n["source_file"]).name, n["label"]) in contains, n


def test_calls_exact(graph):
    calls = [c for c in _edges(graph, "calls") if c[0] not in ("ok1", "bad1", "after1", "after2")]
    assert calls == sorted([
        ("C:LibCmd", "lib:helper"),
        ("app:run", "app:local"),
        ("app:run", "lib:helper"),
    ])


def test_cross_file_call_is_extracted(graph):
    lab = _labels(graph)
    [e] = [e for e in graph["edges"] if e["relation"] == "calls"
           and lab[e["source"]] == "app:run" and lab[e["target"]] == "lib:helper"]
    assert e["confidence"] == "EXTRACTED"


def test_module_depends(graph):
    assert _edges(graph, "module_depends") == [("app", "lib")]


def test_sidecar_doc(graph):
    assert _edges(graph, "sidecar_doc") == [("lib.lsp", "lib-notes.md")]


def test_dcl_references(graph):
    assert _edges(graph, "dcl_references") == [("app:run", "app_dlg"), ("app:show", "app_dlg")]


def test_dcl_action(graph):
    lab = _labels(graph)
    acts = [(lab[e["source"]], lab[e["target"]], e.get("key")) for e in graph["edges"]
            if e["relation"] == "dcl_action"]
    assert acts == [("app_dlg", "app:on-ok", "accept")]


def test_no_token_nodes(graph):
    kinds = {n.get("node_kind") for n in _ours(graph)}
    assert kinds <= {"file", "module", "global", "function", "command", "dialog"}


def test_no_debug_stdout(tmp_path, capsys):
    from graphify_lang.autolisp.extract import extract_autolisp
    extract_autolisp(FIXTURE / "src" / "app.lsp")
    assert "DEBUG" not in capsys.readouterr().out


def test_core_has_no_autolisp_import():
    src = (Path(__file__).parents[2] / "graphify" / "extract.py").read_text(encoding="utf-8")
    assert "graphify_lang" not in src and "autolisp" not in src.lower()


def test_resolver_registered_once():
    from graphify.resolver_registry import registered_resolvers
    from graphify_lang import registry

    registry.reset()
    registry.registered_names()
    registry.reset()
    registry.registered_names()
    names = [r.name for r in registered_resolvers()]
    assert names.count("autolisp") == 1


def test_duplicate_definition_resolves_to_nearest_copy(tmp_path):
    """An archived copy must not capture live calls; the nearer definition wins, INFERRED."""
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "Archive" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "err.lsp").write_text("(defun err:trap (f) (princ))\n")
    (tmp_path / "Archive" / "core" / "err.lsp").write_text("(defun err:trap (f) (princ))\n")
    (tmp_path / "src" / "db.lsp").write_text("(defun db:get () (err:trap 'x))\n")
    files = sorted(tmp_path.rglob("*.lsp"))
    graph = extract(files, cache_root=tmp_path / "cache", root=tmp_path)
    src = {n["id"]: n["source_file"] for n in graph["nodes"]}
    calls = [(src[e["source"]], src[e["target"]], e["confidence"]) for e in graph["edges"] if e["relation"] == "calls"]
    assert calls == [("src/db.lsp", "src/core/err.lsp", "INFERRED")]
