"""Plan 04 S11 - ast-grep plugin (graphify_lang/astgrep): exact pins.

Fixture tree: tests/lang/fixtures/astgrep/ (sgconfig.yml, rules/, utils/,
rule-tests/ with a snapshot, plus .github/workflows/ci.yml, config/app.yml and
rules/notes.yml, which must stay documents). Runs the real
``graphify.extract.extract`` pipeline, so dispatch and the resolver are exercised.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

import graphify_lang.astgrep.extract as astgrep_extract
from graphify.detect import classify_file
from graphify.extract import _get_extractor, extract
from graphify.lang_registry import format_languages
from graphify_lang.astgrep.extract import extract_astgrep

FIXTURE = Path(__file__).parent / "fixtures" / "astgrep"
CORPUS = Path.home() / "repos" / "llm-linter-tool"
DOCS = [".github/workflows/ci.yml", "config/app.yml", "rules/notes.yml"]


@pytest.fixture(scope="module")
def root(tmp_path_factory):
    r = tmp_path_factory.mktemp("astgrep")
    shutil.copytree(FIXTURE, r, dirs_exist_ok=True)
    return r


@pytest.fixture(scope="module")
def graph(root, tmp_path_factory):
    files = sorted(p for p in root.rglob("*.yml") if classify_file(p).value == "code")
    return extract(files, cache_root=tmp_path_factory.mktemp("cache"), root=root)


def _edges(graph, *relations):
    lab = {n["id"]: n.get("label") for n in graph["nodes"]}
    return sorted((e["relation"], lab.get(e["source"]), lab.get(e["target"]))
                  for e in graph["edges"] if e["relation"] in relations)


def test_listed():
    row = next(line for line in format_languages().splitlines() if line.startswith("astgrep "))
    assert row.split() == ["astgrep", ".yaml", ".yml", "-", "sniff+match", "astgrep"]


@pytest.mark.parametrize("rel", DOCS)
def test_unmatched_yml_stays_document(root, rel):
    # D3: no [match] hit (or a glob hit with a sniff miss) classifies as upstream does.
    assert classify_file(root / rel).value == "document"


def test_claimed_files_are_code(root):
    got = sorted(str(p.relative_to(root)) for p in root.rglob("*.yml")
                 if classify_file(p).value == "code")
    assert got == sorted(str(p.relative_to(root)) for p in root.rglob("*.yml")
                         if str(p.relative_to(root)) not in DOCS)
    assert _get_extractor(root / "sgconfig.yml").__name__ == "sniff_router[.yml]"


def test_nodes_exact(graph):
    got = Counter((Path(n["source_file"]).name, n.get("node_kind"), n["label"],
                   n.get("astgrep_role") or n.get("astgrep_scope"))
                  for n in graph["nodes"])
    assert got == Counter({
        ("sgconfig.yml", "file", "sgconfig.yml", "sgconfig"): 1,
        ("no-eval.yml", "file", "no-eval.yml", "rule"): 1,
        ("no-eval.yml", "rule", "no-eval", None): 1,
        ("no-eval.yml", "util", "eval-call", "local"): 1,
        ("no-eval.yml", "util", "in-function", "local"): 1,
        ("print-and-exec.yml", "file", "print-and-exec.yml", "rule"): 1,
        ("print-and-exec.yml", "rule", "no-print", None): 1,   # two documents
        ("print-and-exec.yml", "rule", "no-exec", None): 1,
        ("broken.yml", "file", "broken.yml", None): 1,          # malformed: file only
        ("is-call.yml", "file", "is-call.yml", "util"): 1,
        ("is-call.yml", "util", "is-call", "global"): 1,
        ("no-eval-test.yml", "file", "no-eval-test.yml", "test"): 1,
        ("no-print-test.yml", "file", "no-print-test.yml", "test"): 1,
        ("no-eval-snapshot.yml", "file", "no-eval-snapshot.yml", "snapshot"): 1,
    })


def test_attrs(graph):
    by = {(n.get("node_kind"), n["label"]): n for n in graph["nodes"]}
    assert (by["rule", "no-eval"]["language"], by["rule", "no-eval"]["severity"]) == ("python", "error")
    assert "severity" not in by["rule", "no-exec"]
    assert by["file", "no-eval-test.yml"]["astgrep_id"] == "no-eval"
    sg = by["file", "sgconfig.yml"]
    assert (sg["rule_dirs"], sg["util_dirs"], sg["test_dirs"]) == (["rules"], ["utils"], ["rule-tests"])


def test_edges_exact(graph):
    assert _edges(graph, "tested_by", "has_snapshot", "references", "loads") == sorted([
        ("tested_by", "no-eval", "no-eval-test.yml"),
        ("tested_by", "no-print", "no-print-test.yml"),
        ("has_snapshot", "no-eval", "no-eval-snapshot.yml"),
        ("references", "no-eval", "eval-call"),          # local utils, same file
        ("references", "no-eval", "in-function"),
        ("references", "eval-call", "is-call"),          # local util -> global util
        ("references", "no-exec", "is-call"),
        ("loads", "sgconfig.yml", "no-eval.yml"),        # ruleDirs (broken.yml has no role)
        ("loads", "sgconfig.yml", "print-and-exec.yml"),
        ("loads", "sgconfig.yml", "is-call.yml"),        # utilDirs
    ])


def test_malformed_yaml_warns_and_keeps_file_node(caplog):
    with caplog.at_level(logging.WARNING, logger=astgrep_extract.__name__):
        got = extract_astgrep(FIXTURE / "rules" / "python" / "broken.yml")
    assert [n["label"] for n in got["nodes"]] == ["broken.yml"] and got["edges"] == []
    assert "YAML does not parse" in caplog.text


@pytest.mark.skipif(not (CORPUS / "sgconfig.yml").is_file(), reason="llm-linter-tool not present")
def test_corpus_rules_and_tests(tmp_path):
    ls = subprocess.run(["git", "-C", str(CORPUS), "ls-files", "*.yml", "*.yaml"],
                        capture_output=True, text=True, check=True).stdout.split()
    files = [CORPUS / p for p in ls]
    assert all(classify_file(p).value == "code" for p in files)
    graph = extract(files, cache_root=tmp_path, root=CORPUS)
    rules = [n for n in graph["nodes"] if n.get("node_kind") == "rule"]
    with_id = [p for p in ls if p.startswith("rules/")
               and re.search(r"^id:", (CORPUS / p).read_text(encoding="utf-8"), re.M)]
    assert len(rules) == len(with_id)
    tests = {n["astgrep_id"] for n in graph["nodes"] if n.get("astgrep_role") == "test"}
    per_rule = Counter(e["source"] for e in graph["edges"] if e["relation"] == "tested_by")
    assert {r["id"]: per_rule[r["id"]] for r in rules if r["label"] in tests} == \
        {r["id"]: 1 for r in rules if r["label"] in tests}


def test_hook_set_has_data_and_plugin_suffixes():
    """A .yml / .xml edit rebuilds the graph; neither becomes a code suffix."""
    import graphify.cli
    from graphify.detect import CODE_EXTENSIONS
    assert {".yml", ".xml", ".mke", ".frm"} <= set(graphify.cli._HOOK_SOURCE_EXTS)
    assert CODE_EXTENSIONS.isdisjoint({".yml", ".yaml", ".xml"})
