"""Plan 05 S1 - crafted input must not hang, crash or empty a file (cc-CR000.001
H4, E6, L1, L2).

The timed cases run the extractor in a child process with a hard timeout, so a
regression fails in seconds instead of hanging the suite for minutes.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import graphify_lang.astgrep.extract as astgrep_extract
from graphify_lang.astgrep.extract import extract_astgrep
from graphify_lang.autolisp.extract import extract_autolisp

_CHILD = """
import sys, time
from importlib import import_module
from pathlib import Path
mod, fn, path = sys.argv[1:4]
f = getattr(import_module(mod), fn)
t = time.perf_counter()
r = f(Path(path))
print(time.perf_counter() - t, len(r["nodes"]), len(r["edges"]),
      max(len(repr(n)) for n in r["nodes"]))
"""


def _timed(mod: str, fn: str, path: Path, timeout: float = 30) -> tuple[float, int, int, int]:
    """(seconds, nodes, edges, largest node repr) of ``mod.fn(path)`` in a child process."""
    try:
        proc = subprocess.run([sys.executable, "-c", _CHILD, mod, fn, str(path)],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        pytest.fail(f"{fn}({path.name}) still running after {timeout} s")
    if proc.returncode:
        pytest.fail(f"{fn}({path.name}) exited {proc.returncode}:\n{proc.stderr}")
    secs, nodes, edges, size = proc.stdout.split()
    return float(secs), int(nodes), int(edges), int(size)


def _bomb(levels: int, head: tuple[str, ...] = ("id: bomb", "language: python",
                                                 "rule: {pattern: x}")) -> str:
    """ast-grep YAML whose alias levels each repeat the previous one 10 times;
    ``head`` may name the last level (``*<letter>``)."""
    a = "abcdefghijk"
    lines = ["a: &a {matches: u}"]
    lines += [f"{a[i]}: &{a[i]} [{','.join([f'*{a[i - 1]}'] * 10)}]" for i in range(1, levels + 1)]
    return "\n".join(lines + list(head)) + "\n"


def _rule_file(tmp_path: Path, text: str, name: str = "rules/bomb.yml") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("levels", [6, 9])
def test_h4_alias_bomb_bounded(tmp_path, levels):
    path = _rule_file(tmp_path, _bomb(levels))
    assert len(_bomb(levels).encode()) < 500
    secs, nodes, _, _ = _timed("graphify_lang.astgrep.extract", "extract_astgrep", path)
    assert secs < 1, f"{levels} alias levels took {secs:.2f} s"
    assert nodes == 2  # file + rule


@pytest.mark.parametrize("name,head,nodes", [
    ("rules/b.yml", ("id: *g", "language: python", "rule: {pattern: x}"), 1),
    ("rules/b-test.yml", ("id: *g", "valid: [x]"), 1),
    ("sgconfig.yml", ("ruleDirs: [rules]", "testConfigs: [{testDir: *g}]"), 1),
])
def test_s1_h1_alias_bomb_at_id_and_test_dir(tmp_path, name, head, nodes):
    """7 levels of 10 aliases at ``id`` or ``testDir``: a 90 MB string if
    ``str()`` expands it; a scalar-only sink skips the value."""
    path = _rule_file(tmp_path, _bomb(7, head), name)
    assert len(path.read_bytes()) < 400
    secs, n, _, size = _timed("graphify_lang.astgrep.extract", "extract_astgrep", path)
    assert size < 1000, f"a node is {size} characters"
    assert secs < 1, f"took {secs:.2f} s"
    assert n == nodes


def test_s1_e1_shared_matches_credited_once(tmp_path):
    """The memoised ``_matches`` still finds ``matches:`` under a shared alias,
    once per user: one ``references`` edge to the local util."""
    path = _rule_file(tmp_path, "id: r\nlanguage: python\nm: &m {matches: helper}\n"
                                "rule: {all: [*m, *m, {not: *m}]}\n"
                                "utils:\n  helper: {pattern: y}\n")
    result = extract_astgrep(path)
    refs = [(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "references"]
    helper = next(n["id"] for n in result["nodes"] if n["label"] == "helper")
    rule = next(n["id"] for n in result["nodes"] if n["node_kind"] == "rule")
    assert refs == [(rule, helper)]
    assert result["astgrep_refs"] == []


def test_h4_self_alias_keeps_file_node(tmp_path):
    path = _rule_file(tmp_path, "id: loop\nlanguage: python\nrule: &a {any: [*a]}\n")
    result = extract_astgrep(path)
    kinds = [n["node_kind"] for n in result["nodes"]]
    assert kinds == ["file", "rule"]


def test_e6_rule_doc_error_keeps_file_node(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RecursionError("maximum recursion depth exceeded")
    monkeypatch.setattr(astgrep_extract, "_matches", boom)
    path = _rule_file(tmp_path, "id: one\nrule: {pattern: x}\n---\nid: two\nrule: {pattern: y}\n")
    result = extract_astgrep(path)
    assert result["nodes"][0]["node_kind"] == "file"
    assert result["nodes"][0]["source_file"] == str(path)


@pytest.fixture
def py_default_recursion_limit():
    """``_raise_recursion_limit()`` in graphify.extract raises the limit to
    10 000 when an extraction runs (not on import); pin Python's default so the
    review's 1200 levels overflow whatever test ran first."""
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)
    yield
    sys.setrecursionlimit(limit)


def test_l1_deep_nesting_falls_back(tmp_path, py_default_recursion_limit):
    depth = 1200
    path = tmp_path / "deep.lsp"
    path.write_text("(defun deep ()\n  " + "(list " * depth + "1" + ")" * depth + ")\n"
                    "(defun c:other () (deep))\n", encoding="utf-8")
    result = extract_autolisp(path)
    labels = {n["label"]: n.get("confidence") for n in result["nodes"]}
    assert labels == {"deep.lsp": None, "deep": "INFERRED", "c:other": "INFERRED"}
    # S1-L3: the fallback keeps defuns and globals only; every call, dialog and
    # action ref of the file is dropped (c:other -> deep too), not just the deep defun's.
    assert [e["relation"] for e in result["edges"]] == ["contains", "contains"]
    assert result["autolisp_refs"] == []


def test_s1_l1_deep_action_tile_keeps_file(tmp_path, py_default_recursion_limit):
    depth = 1200
    path = tmp_path / "act.lsp"
    path.write_text('(defun c:x () (action_tile "k" "' + "(foo " * depth + "1" + ")" * depth
                    + '"))\n', encoding="utf-8")
    result = extract_autolisp(path)
    assert [n["label"] for n in result["nodes"]] == ["act.lsp", "c:x"]


def test_l2_large_schema_linear(tmp_path):
    n = 20_000
    props = "\n".join(f'    <ECProperty propertyName="P{i}" typeName="Status"/>' for i in range(n))
    path = tmp_path / "Big.01.00.00.ecschema.xml"
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<ECSchema schemaName="Big" alias="big" version="01.00.00" '
        'xmlns="http://www.bentley.com/schemas/Bentley.ECXML.3.1">\n'
        '  <ECEnumeration typeName="Status" backingTypeName="int"/>\n'
        f'  <ECEntityClass typeName="Thing">\n{props}\n  </ECEntityClass>\n'
        '</ECSchema>\n', encoding="utf-8")
    secs, nodes, edges, _ = _timed("graphify_lang.ecschema.extract", "extract_ecschema", path)
    assert secs < 2, f"{n} properties took {secs:.2f} s"
    assert (nodes, edges) == (n + 4, 2 * n + 3)


def test_s1_m1_many_utils_linear(tmp_path):
    n = 20_000
    path = _rule_file(tmp_path, "id: r\nlanguage: python\nrule: {pattern: x}\nutils:\n"
                      + "".join(f"  u{i}: {{pattern: y}}\n" for i in range(n)))
    secs, nodes, edges, _ = _timed("graphify_lang.astgrep.extract", "extract_astgrep", path)
    assert secs < 2, f"{n} utils took {secs:.2f} s"
    assert (nodes, edges) == (n + 2, n + 1)


def test_s1_l2_document_error_names_its_type(tmp_path, monkeypatch, caplog):
    """A bug midway through a document is logged by type, and the log says the
    nodes added before it stay (they do: rule and util)."""
    def boom(*_args, **_kwargs):
        raise RuntimeError("bug")
    monkeypatch.setattr(astgrep_extract, "_matches", boom)
    path = _rule_file(tmp_path, "id: r\nrule: {pattern: x}\nutils:\n  u: {pattern: y}\n")
    with caplog.at_level("WARNING", logger="graphify_lang.astgrep.extract"):
        result = extract_astgrep(path)
    assert [n["node_kind"] for n in result["nodes"]] == ["file", "rule", "util"]
    assert "RuntimeError" in caplog.text and "kept" in caplog.text
    assert "skipped" not in caplog.text
