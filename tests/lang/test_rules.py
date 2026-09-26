"""Rules runtime (plan 01 S005, repaired in plan 04 S7 / T28).

Every rules call runs from the fixture root on a relative path, so ids carry
the corpus prefix (``src_core_err_...``) as they do under ``extract(root=)``.
"""

import sys
import types
from pathlib import Path

import pytest

from graphify.extractors.base import _file_stem, _make_id
from graphify_lang.manifest import tomllib
from graphify_lang.rules import build

FIXTURE_DIR = Path(__file__).parent / "fixtures"
CORPUS_FILES = Path(__file__).parent / "corpus_files.txt"
TEMPLATES = Path(__file__).parent.parent.parent / "graphify_lang" / "templates"
ERR = Path("src/core/err.lsp")
CONTRACT = ("id", "label", "file_type", "node_kind", "source_file", "source_location")

LISP_REGEX = [
    {"pattern": r"\(defun\s+(?P<name>[^\s()]+)", "node": "function", "scope": "set"},
    {"pattern": r"\((?P<name>[^\s()';\"]+)", "edge": "calls"},
]
LISP_TAGS = """
(defun (defun_header function_name: (_) @name)) @definition.function
(list_lit . [(sym_lit) (package_lit)] @name) @reference.calls
"""
COMMONLISP = {"kind": "tree-sitter", "module": "tree_sitter_commonlisp"}


@pytest.fixture(autouse=True)
def _at_fixture_root(monkeypatch):
    monkeypatch.chdir(FIXTURE_DIR)


def _run(manifest, path=ERR, manifest_path=None):
    extract, resolver = build(manifest_path or FIXTURE_DIR / "m.toml", manifest)
    assert resolver is None
    return extract(Path(path))


def _stem(path):
    """Symbol-id prefix: the file id without its suffix (M4)."""
    return _make_id(_file_stem(Path(path)))


def _kinds(result, kind):
    return {n["label"]: n["id"] for n in result["nodes"] if n["node_kind"] == kind}


def _edges(result, relation):
    return {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == relation}


def _tags_manifest(tmp_path, text=LISP_TAGS, grammar=COMMONLISP):
    (tmp_path / "tags.scm").write_text(text)
    return {"manifest": {"grammar": grammar, "extract": {"queries": "tags.scm"}},
            "manifest_path": tmp_path / "m.toml"}


# --- corpus list (T5.1) ---------------------------------------------------

def test_corpus_file_list():
    lines = [l.strip() for l in CORPUS_FILES.read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    assert CORPUS_FILES.read_text().startswith("#")
    assert len(lines) == 84, "81 .lsp + 3 .dcl at autolithp d5a2074 (SRS §1.3)"
    assert all(not l.startswith("/") and "/" in l for l in lines)


# --- emission contract ----------------------------------------------------

def test_empty_manifest_emits_the_file_node():
    r = _run({})
    assert r["edges"] == []
    assert r["nodes"] == [{"id": "src_core_err_lsp", "label": "err.lsp", "file_type": "code",
                           "node_kind": "file", "source_file": "src/core/err.lsp",
                           "source_location": "L1"}]


def test_regex_tier_on_err_lsp():
    r = _run({"rule": LISP_REGEX})
    assert "error" not in r
    fns = _kinds(r, "function")
    assert len(fns) == 27 and len(_kinds(r, "file")) == 1
    # err:_trap and err:trap normalise to one id; the later one takes its line
    assert (fns["err:_trap"], fns["err:trap"]) == ("src_core_err_err_trap", "src_core_err_err_trap_161")
    for n in r["nodes"]:
        assert all(n.get(k) for k in CONTRACT), n
        assert n["file_type"] == "code" and n["source_file"] == "src/core/err.lsp"
    assert _edges(r, "contains") == {("src_core_err_lsp", nid) for nid in fns.values()}
    calls = _edges(r, "calls")
    assert ("src_core_err_err_trap_161", "src_core_err_err_trap") in calls
    assert len(calls) == 29


def test_query_tier_matches_regex_tier_on_err_lsp(tmp_path):
    q = _run(**_tags_manifest(tmp_path))
    r = _run({"rule": LISP_REGEX})
    assert "error" not in q
    assert len(_kinds(q, "function")) == 27
    assert q["nodes"] == r["nodes"]
    assert _edges(q, "calls") == _edges(r, "calls")
    assert all(all(n.get(k) for k in CONTRACT) for n in q["nodes"])


@pytest.mark.parametrize("pred, keep", [
    ('(#not-match? @name "^err:_")', lambda t: not t.startswith("err:_")),
    ('(#match? @name "^err:_")', lambda t: t.startswith("err:_")),
    ('(#any-of? @name "err:_report" "err:_log")', lambda t: t in ("err:_report", "err:_log")),
    ('(#not-eq? @name "err:_report")', lambda t: t != "err:_report"),
])
def test_query_predicates_filter_captures(tmp_path, pred, keep):
    """Evaluated in Python: tree-sitter 0.23 inverts #not-match? and ignores #any-of?."""
    tags = LISP_TAGS.replace("@name) @reference.calls", f"@name {pred}) @reference.calls")
    q = _run(**_tags_manifest(tmp_path, tags))
    labels = {n["id"]: n["label"] for n in q["nodes"]}
    all_targets = {labels[t] for _, t in _edges(_run({"rule": LISP_REGEX}), "calls")}
    targets = {labels[t] for _, t in _edges(q, "calls")}
    assert targets == {t for t in all_targets if keep(t)} != set()


def test_id_clash_gets_the_line_number(tmp_path):
    f = tmp_path / "dup.lsp"
    f.write_text("(defun foo ()\n  1)\n(defun foo ()\n  (foo))\n")
    r = _run({"rule": LISP_REGEX}, f)
    ids = [n["id"] for n in r["nodes"] if n["node_kind"] == "function"]
    stem = _stem(f)
    assert ids == [f"{stem}_foo", f"{stem}_foo_3"]
    assert _edges(r, "calls") == {(f"{stem}_foo_3", f"{stem}_foo")}


def test_builtins_filter_names_prefixes_and_case(tmp_path):
    (tmp_path / "b.txt").write_text("# comment\n; comment\nERR:_TRAP\n")
    base = {"rule": LISP_REGEX, "language": {"case_insensitive": True}}
    full = _edges(_run({"rule": LISP_REGEX}), "calls")
    named = _edges(_run({**base, "extract": {"builtins_file": "b.txt"}},
                        manifest_path=tmp_path / "m.toml"), "calls")
    assert full - named == {(s, t) for s, t in full if t == "src_core_err_err_trap"} != set()
    r = _run({**base, "extract": {"builtins_prefixes": ["Err:_"]}})
    labels = {n["id"]: n["label"] for n in r["nodes"]}
    pref = _edges(r, "calls")
    assert pref and not any(labels[t].startswith("err:_") for _, t in pref)
    exact = _edges(_run({"rule": LISP_REGEX, "extract": {"builtins_prefixes": "Err:_"}}), "calls")
    assert exact == full  # case-sensitive: "Err:_" matches nothing


def test_scope_push_pop_and_edge_from_scope(tmp_path):
    f = tmp_path / "s.blk"
    f.write_text("block a {\n  use b\n}\nuse a\nblock b {\n}\n")
    rules = [
        {"pattern": r"block (?P<name>\w+) \{", "node": "block", "scope": "push"},
        {"pattern": r"^\}", "scope": "pop"},
        {"pattern": r"use (?P<name>\w+)", "edge": "uses"},
    ]
    r = _run({"rule": rules}, f)
    stem, fid = _stem(f), r["nodes"][0]["id"]
    assert _edges(r, "uses") == {(f"{stem}_a", f"{stem}_b"), (fid, f"{stem}_a")}
    rules[2] = {**rules[2], "edge_from_scope": False}
    assert _edges(_run({"rule": rules}, f), "uses") == {(fid, f"{stem}_b"), (fid, f"{stem}_a")}
    rules[2] = {**rules[2], "suffix": ".other"}
    assert _edges(_run({"rule": rules}, f), "uses") == set()


def test_post_file_hook(monkeypatch):
    seen = {}

    def hook(path, tree, nodes, edges, manifest):
        seen["tree"] = tree
        return {"nodes": nodes + [{"id": "extra"}]}

    monkeypatch.setitem(sys.modules, "graphify_lang.rules_hook_mod", types.SimpleNamespace(hook=hook))
    r = _run({"rule": LISP_REGEX, "extract": {"post_file": "graphify_lang.rules_hook_mod:hook"}})
    assert r["nodes"][-1] == {"id": "extra"} and seen["tree"] is None
    bad = _run({"extract": {"post_file": "graphify_lang.rules_hook_mod:nope"}})
    assert bad["nodes"] == [] and "failed to load" in bad["error"]


def test_m6_post_file_prefix_only(monkeypatch):
    """cc-CR000.001 M6 / plan 05 D1: a hook outside graphify_lang.* is a manifest
    error and is never imported."""
    called = []
    monkeypatch.setitem(sys.modules, "evil_hook_mod",
                        types.SimpleNamespace(hook=lambda *a: called.append(a)))
    r = _run({"extract": {"post_file": "evil_hook_mod:hook"}})
    assert called == []
    assert r["nodes"] == [] and "graphify_lang." in r["error"] and "failed to load" in r["error"]


# --- loud failures --------------------------------------------------------

@pytest.mark.parametrize("grammar, query, marker", [
    ({"module": "tree_sitter_not_there"}, LISP_TAGS, "not installed"),
    ({}, LISP_TAGS, "failed to load"),
    (COMMONLISP, "(no_such_node) @definition.x", "failed to load"),
])
def test_query_tier_fails_loudly(tmp_path, caplog, grammar, query, marker):
    r = _run(**_tags_manifest(tmp_path, query, grammar))
    assert r["nodes"] == [] and r["edges"] == []
    assert marker in r["error"]
    assert marker in caplog.text


def test_missing_query_file_fails_loudly(tmp_path):
    r = _run({"grammar": COMMONLISP, "extract": {"queries": "absent.scm"}}, manifest_path=tmp_path / "m.toml")
    assert r["nodes"] == [] and "failed to load" in r["error"]


@pytest.mark.parametrize("rule", [
    {"pattern": "("},
    {"pattern": "x", "node": "a", "edge": "b"},
    {"pattern": "x"},
    {"pattern": "x", "node": "a", "scope": "open"},
])
def test_bad_regex_rule_fails_loudly(rule):
    r = _run({"rule": [rule]})
    assert r["nodes"] == [] and "failed to load" in r["error"]


# --- DCL parity (plan 04 S7 acceptance) -----------------------------------

def _rules_dcl():
    path = Path(__file__).parent / "rules_dcl.toml"
    return build(path, tomllib.loads(path.read_text()))[0]


def test_rules_dcl_matches_extract_dcl_on_fixtures():
    from graphify_lang.autolisp.extract import extract_dcl

    files = sorted(p.relative_to(FIXTURE_DIR) for p in FIXTURE_DIR.rglob("*.dcl"))
    assert len(files) >= 2
    extract = _rules_dcl()
    for f in files:
        want, got = extract_dcl(f), extract(f)
        assert _kinds(want, "dialog"), f
        assert got["nodes"] == want["nodes"], f
        assert got["edges"] == want["edges"], f


def test_rules_dcl_skips_commented_dialogs(tmp_path):
    from graphify_lang.autolisp.extract import extract_dcl

    f = tmp_path / "c.dcl"
    f.write_text("/* old : dialog {\n} */\n// gone : dialog {\nreal : dialog {\n}\n")
    got = _rules_dcl()(f)
    assert list(_kinds(got, "dialog")) == ["real"]
    assert got["nodes"] == extract_dcl(f)["nodes"]


# --- templates ------------------------------------------------------------

def test_templates_are_valid_manifests():
    for name in ("programming.toml", "markup.toml", "prose.toml"):
        data = tomllib.loads((TEMPLATES / name).read_text())
        assert {"schema", "language", "grammar", "extract"} <= data.keys(), name
        assert data["extract"]["runtime"] == "graphify_lang.rules"
    assert "post_file" in (TEMPLATES / "programming.toml").read_text()


def test_programming_template_runs(tmp_path):
    path = TEMPLATES / "programming.toml"
    extract, _ = build(path, tomllib.loads(path.read_text()))
    f = tmp_path / "s.ext"
    f.write_text("def a(x):\n    b(x)\ndef b(y):\n    print(y)\n")
    r = extract(f)
    stem = _stem(f)
    assert list(_kinds(r, "function")) == ["a", "b"]
    assert _edges(r, "calls") == {(f"{stem}_a", f"{stem}_b")}


def test_templates_are_package_data():
    pyproject = tomllib.loads((TEMPLATES.parent.parent / "pyproject.toml").read_text())
    assert "templates/*.toml" in pyproject["tool"]["setuptools"]["package-data"]["graphify_lang"]


# --- cc-CR000.003 S003 review fixes -------------------------------------------

def test_s3_l1_post_file_from_the_callers_package(monkeypatch):
    """S3-L1: an out-of-tree plugin that calls ``build`` may name a hook in its
    own package; any other module stays rejected (plan 05 D1)."""
    def hook(path, tree, nodes, edges, manifest):
        return {"nodes": nodes + [{"id": "extra"}]}

    monkeypatch.setitem(sys.modules, "mylang", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "mylang.hooks", types.SimpleNamespace(post=hook))
    monkeypatch.setitem(sys.modules, "mylangx", types.SimpleNamespace(post=hook))
    ok = {"extract": {"post_file": "mylang.hooks:post"}}
    extract, _ = build(FIXTURE_DIR / "m.toml", ok, package="mylang")
    assert extract(ERR)["nodes"][-1] == {"id": "extra"}
    for manifest, package in ((ok, None), ({"extract": {"post_file": "mylangx:post"}}, "mylang")):
        extract, _ = build(FIXTURE_DIR / "m.toml", manifest, package=package)
        assert "rejected" in extract(ERR)["error"]


def test_s3_l2_recursive_call_keeps_its_self_loop(tmp_path):
    """S3-L2: a recursive call is a ``calls`` self-loop, as upstream's built-in
    extractors emit it (``def f(n): return f(n-1)`` -> ``f calls f``)."""
    f = tmp_path / "r.lsp"
    f.write_text("(defun fact (n)\n  (fact (1- n)))\n")
    stem = _stem(f)
    assert _edges(_run({"rule": LISP_REGEX}, f), "calls") == {(f"{stem}_fact", f"{stem}_fact")}


def test_s3_n1_hash_name_is_not_a_comment(tmp_path):
    """S3-N1: ``#`` starts a comment only when a space or the line end follows,
    so the AutoLISP builtin ``#&/`` survives the shared loader."""
    from graphify_lang.autolisp.extract import is_builtin

    assert is_builtin("#&/")
    (tmp_path / "b.txt").write_text("#\n# comment\n#&/\n")
    from graphify_lang.builtins import Builtins

    assert Builtins.from_manifest(tmp_path / "m.toml", {"extract": {"builtins_file": "b.txt"}}).names == {"#&/"}


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="int grammar pointer is deprecated")
def test_int_grammar_pointer_warns_nothing(tmp_path):
    """``tree_sitter_commonlisp.language()`` returns an int; ``Language(int)``
    is deprecated in py-tree-sitter 0.25, so the pointer is wrapped in a capsule."""
    import warnings

    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        r = _run(**_tags_manifest(tmp_path))
    assert "error" not in r
    assert [str(w.message) for w in seen if issubclass(w.category, DeprecationWarning)] == []
