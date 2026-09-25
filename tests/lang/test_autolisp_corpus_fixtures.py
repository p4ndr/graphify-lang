"""SC4 on the checked-in corpus files (plan 01 S006 tasks 6-7).

tests/lang/fixtures/src/ holds byte-identical copies of ~/repos/autolithp
(d5a2074) src/core/err.lsp, src/core/ldr.lsp and src/ui/manager.dcl. The tree
mirrors the corpus prefix, so ids come out as they do on the corpus. SC4's 27
is derived from the defun recipe and the checked-in collision set, not asserted.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

from graphify.extract import extract

FIXTURES = Path(__file__).parent / "fixtures"
FILES = ["src/core/err.lsp", "src/core/ldr.lsp", "src/ui/manager.dcl"]


@pytest.fixture(scope="module")
def graph(tmp_path_factory):
    return extract([FIXTURES / f for f in FILES], root=FIXTURES,
                   cache_root=tmp_path_factory.mktemp("cache"))


def _defs(graph, rel):
    return [n for n in graph["nodes"] if n.get("source_file") == rel
            and n.get("node_kind") in ("function", "command")]


def _collision_set():
    rows = [l.split("\t") for l in (FIXTURES / "collision_set.tsv").read_text().splitlines()
            if l and not l.startswith("#")]
    return {(f, int(n), labels) for f, n, labels in rows}


def test_sc4_err_lsp_functions_from_recipe(graph):
    source = (FIXTURES / "src/core/err.lsp").read_text(encoding="utf-8")
    recipe = len(re.findall(r"\(\s*defun(-q)?\s", source, re.I))
    defs = _defs(graph, "src/core/err.lsp")
    assert len(defs) == recipe == 27
    assert len({n["id"] for n in defs}) == recipe
    assert all(n["node_kind"] == "function" for n in defs)


def test_collision_groups_match_checked_in_set(graph):
    rel = "src/core/err.lsp"
    groups = Counter(re.sub(r"_l\d+$", "", n["id"]) for n in _defs(graph, rel))
    found = set()
    for base, count in groups.items():
        if count > 1:
            labels = sorted({n["label"] for n in _defs(graph, rel)
                             if re.sub(r"_l\d+$", "", n["id"]) == base})
            found.add((rel, count, " ".join(labels)))
    assert found == {row for row in _collision_set() if row[0] == rel}
    assert len(_collision_set()) == 11


def test_sc4_err_trap_one_node(graph):
    labels = [n["label"] for n in _defs(graph, "src/core/err.lsp")]
    assert labels.count("err:trap") == 1 and labels.count("err:_trap") == 1


def test_sc4_commands(graph):
    commands = {n["label"] for n in _defs(graph, "src/core/ldr.lsp") if n["node_kind"] == "command"}
    assert {"C:LITHP", "C:LITHP-MGR", "C:LITHP-INIT"} <= commands


def test_manager_dcl_dialog(graph):
    dialogs = [n["label"] for n in graph["nodes"] if n.get("node_kind") == "dialog"]
    assert dialogs == ["lithp_mgr"]


def test_cond_clause_head_is_not_a_call(tmp_path):
    from graphify_lang.autolisp.extract import extract_autolisp

    f = tmp_path / "c.lsp"
    f.write_text("(defun flag () T)\n(defun g () nil)\n(defun f () (cond (flag (g))))\n")
    r = extract_autolisp(f)
    lab = {n["id"]: n["label"] for n in r["nodes"]}
    assert [(lab[e["source"]], lab[e["target"]]) for e in r["edges"] if e["relation"] == "calls"] == [("f", "g")]


def test_upper_case_suffix_resolves_cross_file(tmp_path):
    (tmp_path / "ERR.LSP").write_text("(defun err:trap (f) (princ))\n")
    (tmp_path / "db.lsp").write_text("(defun db:get () (err:trap 'x))\n")
    g = extract(sorted(tmp_path.iterdir()), root=tmp_path, cache_root=tmp_path / "cache")
    lab = {n["id"]: n["label"] for n in g["nodes"]}
    assert [(lab[e["source"]], lab[e["target"]]) for e in g["edges"] if e["relation"] == "calls"] == [("db:get", "err:trap")]


def test_mnl_and_defun_q_authored(tmp_path):
    """Zero corpus instances (SRS §1.3), so authored: `.mnl` is AutoLISP, `defun-q` defines."""
    (tmp_path / "acad.mnl").write_text("(defun-q q:legacy () (mnl:boot))\n(defun mnl:boot () nil)\n")
    g = extract([tmp_path / "acad.mnl"], root=tmp_path, cache_root=tmp_path / "cache")
    assert not g.get("error")
    lab = {n["id"]: n["label"] for n in g["nodes"]}
    assert sorted((n["label"], n["node_kind"]) for n in g["nodes"]) == [
        ("acad.mnl", "file"), ("mnl:boot", "function"), ("q:legacy", "function")]
    assert [(lab[e["source"]], lab[e["target"]]) for e in g["edges"] if e["relation"] == "calls"] == [("q:legacy", "mnl:boot")]
