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

pytestmark = pytest.mark.skipif(astgrep_extract._yaml is None, reason="PyYAML absent")

_CHILD = """
import sys, time
from importlib import import_module
from pathlib import Path
mod, fn, path = sys.argv[1:4]
f = getattr(import_module(mod), fn)
t = time.perf_counter()
r = f(Path(path))
print(time.perf_counter() - t, len(r["nodes"]), len(r["edges"]))
"""


def _timed(mod: str, fn: str, path: Path, timeout: float = 30) -> tuple[float, int, int]:
    """(seconds, nodes, edges) of ``mod.fn(path)`` in a child process."""
    try:
        proc = subprocess.run([sys.executable, "-c", _CHILD, mod, fn, str(path)],
                              capture_output=True, text=True, timeout=timeout, check=True)
    except subprocess.TimeoutExpired:
        pytest.fail(f"{fn}({path.name}) still running after {timeout} s")
    secs, nodes, edges = proc.stdout.split()
    return float(secs), int(nodes), int(edges)


def _bomb(levels: int) -> str:
    """ast-grep rule whose alias levels each repeat the previous one 10 times."""
    a = "abcdefghijk"
    lines = ["id: bomb", "language: python", "rule: {pattern: x}", "a: &a {matches: u}"]
    lines += [f"{a[i]}: &{a[i]} [{','.join([f'*{a[i - 1]}'] * 10)}]" for i in range(1, levels + 1)]
    return "\n".join(lines) + "\n"


def _rule_file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "rules" / "bomb.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("levels", [6, 9])
def test_h4_alias_bomb_bounded(tmp_path, levels):
    path = _rule_file(tmp_path, _bomb(levels))
    assert len(_bomb(levels).encode()) < 500
    secs, nodes, _ = _timed("graphify_lang.astgrep.extract", "extract_astgrep", path)
    assert secs < 1, f"{levels} alias levels took {secs:.2f} s"
    assert nodes == 2  # file + rule


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
    """graphify.extract raises the limit to 10 000 on import; pin Python's
    default so the review's 1200 levels overflow whatever test ran first."""
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)
    yield
    sys.setrecursionlimit(limit)


@pytest.mark.xfail(strict=True, raises=RecursionError,
                   reason="cc-CR000.001 L1: the walker recurses per list level")
def test_l1_deep_nesting_falls_back(tmp_path, py_default_recursion_limit):
    depth = 1200
    path = tmp_path / "deep.lsp"
    path.write_text("(defun deep ()\n  " + "(list " * depth + "1" + ")" * depth + ")\n"
                    "(defun c:other () (deep))\n", encoding="utf-8")
    result = extract_autolisp(path)
    labels = {n["label"]: n.get("confidence") for n in result["nodes"]}
    assert labels == {"deep.lsp": None, "deep": "INFERRED", "c:other": "INFERRED"}


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="cc-CR000.001 L2: quadratic edge de-duplication")
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
    secs, nodes, edges = _timed("graphify_lang.ecschema.extract", "extract_ecschema", path)
    assert secs < 2, f"{n} properties took {secs:.2f} s"
    assert (nodes, edges) == (n + 4, 2 * n + 3)
