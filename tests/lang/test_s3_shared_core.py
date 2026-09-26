"""Plan 05 S3 - the shared plugin core (cc-CR000.001 H2, M4, M6).

H2: a resolver ref must name the node it came from after upstream has salted
colliding ids apart, so same-stem files keep their cross-file edges.
M4: a plugin file-node id is minted like a built-in one (``_make_id(str(path))``),
so upstream's portable remap applies: the same corpus gives the same ids under
any scan root, no id carries the root path, and no two nodes share an id.
M6 (the rules engine's ``post_file`` prefix rule) is pinned in ``test_rules.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from graphify.extract import extract

ECSCHEMA = ('<?xml version="1.0"?>\n<ECSchema schemaName="S" alias="s" version="01.00" '
            'xmlns="http://www.bentley.com/schemas/Bentley.ECXML.3.1">\n'
            '<ECEntityClass typeName="A"/>\n</ECSchema>\n')
VBA_CLS = 'VERSION 1.0 CLASS\nAttribute VB_Name = "XC"\nOption Explicit\n'


def _build(root: Path, files: dict[str, str]) -> dict:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return extract(sorted(root / rel for rel in files), cache_root=root / ".cache", root=root)


def _node(graph: dict, rel: str, label: str) -> dict:
    found = [n for n in graph["nodes"]
             if str(n.get("source_file")) == rel and n.get("label") == label]
    assert len(found) == 1, (rel, label, found)
    return found[0]


def _dangling(graph: dict) -> list[tuple]:
    ids = {n["id"] for n in graph["nodes"]}
    return [(e["source"], e["relation"], e["target"]) for e in graph["edges"]
            if e["source"] not in ids or e["target"] not in ids]


def _has(graph: dict, src: dict, relation: str, tgt: dict) -> bool:
    return any(e["source"] == src["id"] and e["relation"] == relation and e["target"] == tgt["id"]
               for e in graph["edges"])


def test_h2_same_stem_lsp_mnl_dcl(tmp_path):
    g = _build(tmp_path, {
        "app/x.lsp": ('; @sidecar x.md\n(defun helper () (libfn))\n'
                      '(defun show () (new_dialog "x_dlg" 1) (action_tile "ok" "(done)"))\n'),
        "app/x.mnl": "(defun helper () (libfn))\n",
        "app/x.dcl": "x_dlg : dialog { }\n",
        "app/x.md": "# X\n",
        "sub/lib.lsp": "(defun libfn () 1)\n(defun done () 2)\n",
    })
    assert _dangling(g) == []
    libfn = _node(g, "sub/lib.lsp", "libfn")
    assert _has(g, _node(g, "app/x.lsp", "helper"), "calls", libfn)
    assert _has(g, _node(g, "app/x.mnl", "helper"), "calls", libfn)
    dialog = _node(g, "app/x.dcl", "x_dlg")
    assert _has(g, _node(g, "app/x.lsp", "show"), "dcl_references", dialog)
    assert _has(g, dialog, "dcl_action", _node(g, "sub/lib.lsp", "done"))
    assert _has(g, _node(g, "app/x.lsp", "x.lsp"), "sidecar_doc", _node(g, "app/x.md", "x.md"))


def test_h2_vba_same_stem(tmp_path):
    g = _build(tmp_path, {
        "app/x.bas": 'Attribute VB_Name = "XB"\nPublic Sub Helper()\n    LibFn\nEnd Sub\n',
        "app/x.cls": VBA_CLS + "Public Sub Helper()\n    LibFn\nEnd Sub\n",
        "sub/lib.bas": 'Attribute VB_Name = "Lib"\nPublic Sub LibFn()\nEnd Sub\n',
    })
    assert _dangling(g) == []
    libfn = _node(g, "sub/lib.bas", "LibFn")
    assert _has(g, _node(g, "app/x.bas", "Helper"), "calls", libfn)
    assert _has(g, _node(g, "app/x.cls", "Helper"), "calls", libfn)


_M4 = {
    "autolisp": {"d/x.lsp": "(defun a () 1)\n", "d/x.mnl": "(defun a () 2)\n",
                 "d/x.dcl": "x : dialog { }\n"},
    "vba": {"d/x.bas": 'Attribute VB_Name = "XB"\n', "d/x.cls": VBA_CLS,
            "d/x.frm": 'Attribute VB_Name = "XF"\n'},
    "bmake": {"d/x.mki": "A = 1\n", "d/x.mke": "B = $(A)\n"},
    "ecschema": {"d/x.xml": ECSCHEMA},
    "astgrep": {"rules/x.yml": "id: r\nlanguage: python\nrule:\n  pattern: eval($A)\n"},
}


@pytest.mark.parametrize("plugin", list(_M4))
def test_m4_file_ids_portable(tmp_path, plugin):
    # A same-stem .py file beside the plugin files: its file node id is the
    # built-in form every plugin file must collide with and be salted from.
    files = {**_M4[plugin], f"{next(iter(_M4[plugin])).rsplit('.', 1)[0]}.py": "def f():\n    pass\n"}
    runs = []
    for tag in ("one", "two"):
        root = tmp_path / tag / "checkout"
        ids = [n["id"] for n in _build(root, files)["nodes"]]
        assert len(ids) == len(set(ids)), sorted(ids)
        assert not [i for i in ids if tag in i or "checkout" in i], sorted(ids)
        runs.append(sorted(ids))
    assert runs[0] == runs[1]



# N3: every key of a shipped manifest has a reader. Keys read by manifest.py
# and the plugin core, plus those the rules engine reads when it is the runtime.
_READ = {
    "schema", "language.name", "language.suffixes", "language.hook_suffixes",
    "language.priority", "language.kind", "language.augments", "language.overrides",
    "language.case_insensitive", "grammar.module", "grammar.extra",
    "extract.runtime", "extract.resolver", "extract.builtins_file", "extract.builtins_prefixes",
    "match.globs", "match.filenames", "resolve.context_fields", "sniff.rules", "sniff.min_score", "sniff.head_bytes",
}
_READ_BY_RULES = {
    "grammar.language_fn", "extract.queries", "extract.comments", "extract.post_file",
    "extract.python", "rule.kind", "rule.pattern", "rule.scope", "rule.multiline",
    "rule.suffix", "rule.node", "rule.name_group", "rule.edge", "rule.target",
    "rule.edge_from_scope",
}
_SHIPPED = sorted((Path(__file__).parents[2] / "graphify_lang").rglob("*.toml"))


def _keys(data: dict) -> set[str]:
    out = set()
    for key, value in data.items():
        tables = value if isinstance(value, list) else [value]
        if tables and all(isinstance(t, dict) for t in tables):
            out |= {f"{key}.{k}" for t in tables for k in t}
        else:
            out.add(key)
    return out


@pytest.mark.parametrize("toml", _SHIPPED, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_n3_every_manifest_key_is_read(toml):
    from graphify_lang.manifest import tomllib

    data = tomllib.loads(toml.read_text(encoding="utf-8"))
    read = _READ | (_READ_BY_RULES if data["extract"]["runtime"] == "graphify_lang.rules" else set())
    assert sorted(_keys(data) - read) == []


_N2 = pytest.mark.xfail(strict=True, raises=AssertionError, reason="S3-N2: True == 1")


@pytest.mark.parametrize("schema, ok", [("1", True), ('"v1"', True), ("2", False),
                                        pytest.param("true", False, marks=_N2),
                                        pytest.param("1.0", False, marks=_N2)])
def test_n3_schema_is_read(tmp_path, schema, ok):
    from graphify_lang.manifest import LanguageManifest

    toml = tmp_path / "m.toml"
    toml.write_text(f'schema = {schema}\n[language]\nname = "x"\nsuffixes = [".x"]\n'
                    '[extract]\nruntime = "m"\n')
    assert (LanguageManifest.from_toml(toml)[1] == []) is ok


_CC_KB = Path(__file__).parent / "fixtures" / "cc_kb"


class _CountingList(list):
    iterations = 0

    def __iter__(self):
        type(self).iterations += 1
        return super().__iter__()


def test_l3_cc_kb_resolver_scans_nodes_once():
    from graphify_lang.cc_kb.resolve import resolve

    docs = sorted((_CC_KB / "docs").glob("cc-*.md"))
    per_file = [r for r in (_get_extractor_result(d) for d in docs) if r.get("cc_kb_refs")]
    assert len(per_file) >= 3
    nodes = _CountingList(n for r in per_file for n in r["nodes"])
    _CountingList.iterations = 0
    resolve(per_file, nodes, [])
    assert _CountingList.iterations == 1


def _get_extractor_result(path: Path) -> dict:
    from graphify.extract import _get_extractor

    return _get_extractor(path)(path)


def test_e8_cc_kb_augment_reads_no_other_file(monkeypatch):
    """E8, then H3 (plan 05 S4): the docs/ root scan left the augment for the
    resolver, so the augment lists no folder and tests no other path."""
    import os

    from graphify.extract import extract_markdown
    from graphify_lang.cc_kb import augment

    docs = sorted((_CC_KB / "docs").glob("cc-*.md"))
    bases = [extract_markdown(d) for d in docs]
    calls = []
    monkeypatch.setattr(os, "scandir", lambda p: calls.append(p))
    monkeypatch.setattr(Path, "is_file", lambda p: calls.append(p) or True)
    monkeypatch.setattr(Path, "samefile", lambda p, q: calls.append(q) or False)
    for doc, base in zip(docs, bases):
        augment.augment_cc_kb(doc, base)
    assert calls == []


def test_s2_n5_one_tomllib_shim():
    import re

    import graphify_lang.manifest as manifest

    shim = re.compile(r"^\s*import tomli\b", re.M)
    root = Path(__file__).resolve().parents[2]
    shims = sorted(str(p.relative_to(root)) for d in ("graphify_lang", "tests/lang")
                   for p in (root / d).rglob("*.py") if shim.search(p.read_text(encoding="utf-8")))
    assert shims == ["graphify_lang/manifest.py"]
    assert hasattr(manifest, "tomllib") and not hasattr(manifest, "tomli")


# --- cc-CR000.003 S003 review fixes -------------------------------------------

def _lsp_results(tmp_path):
    from graphify_lang.autolisp.extract import extract_autolisp

    (tmp_path / "app").mkdir()
    (tmp_path / "sub").mkdir()
    (tmp_path / "app/x.lsp").write_text("(defun go () (libfn))\n")
    (tmp_path / "sub/lib.lsp").write_text("(defun libfn () 1)\n")
    return [extract_autolisp(tmp_path / "app/x.lsp"), extract_autolisp(tmp_path / "sub/lib.lsp")]


def _calls(per_file):
    from graphify_lang.autolisp.resolve import resolve

    nodes = [n for r in per_file for n in r["nodes"]]
    edges: list = []
    resolve(per_file, nodes, edges)
    labels = {n["id"]: n["label"] for n in nodes}
    return {(labels[e["source"]], labels[e["target"]]) for e in edges if e["relation"] == "calls"}


@pytest.mark.xfail(strict=True, raises=KeyError, reason="S3-M1: a node-less ref raises")
def test_s3_m1_stale_cache_ref_degrades(tmp_path):
    """S3-M1 / S3-E1: a pre-S3 AST cache entry (refs carry ``source``, not
    ``node``) degrades that file, never the whole resolver pass. The plugin-set
    fingerprint (E1, ``lang_registry._namespace_ast_cache``) already keeps such
    entries unread; this pins the resolver side."""
    from graphify_lang._common import refs_of

    fresh = _lsp_results(tmp_path)
    assert _calls(fresh) == {("go", "libfn")}
    stale = [dict(r) for r in fresh]
    stale[0]["autolisp_refs"] = [{k: v for k, v in ref.items() if k != "node"}
                                 | {"source": stale[0]["nodes"][ref["node"]]["id"]}
                                 for ref in fresh[0]["autolisp_refs"]]
    assert _calls(stale) == {("go", "libfn")}  # pre-S3 ``source`` is still an id of that result
    gone = [{**stale[0], "autolisp_refs": [{k: v for k, v in r.items() if k != "source"}
                                           for r in stale[0]["autolisp_refs"]]}, stale[1]]
    assert _calls(gone) == set() and refs_of(gone, "autolisp_refs") == []


def test_s3_e1_pick_by_prefix():
    from graphify_lang._common import pick_by_prefix

    def n(i, sf):
        return {"id": i, "source_file": sf}
    assert pick_by_prefix([], "a/x.lsp") == (None, "EXTRACTED")
    assert pick_by_prefix([n("t", "z/y.lsp")], "a/x.lsp") == ("t", "EXTRACTED")
    assert pick_by_prefix([n("far", "old/a/y.lsp"), n("near", "a/y.lsp")], "a/x.lsp") == ("near", "INFERRED")
    assert pick_by_prefix([n("p", "b/y.lsp"), n("q", "c/y.lsp")], "a/x.lsp") == (None, "EXTRACTED")


def test_s3_e1_sink_ref_unique_and_add_salting(tmp_path):
    from graphify_lang._common import Sink

    s = Sink(tmp_path / "x.lsp")
    a = s.node("function", "f", 1)
    b = s.node("function", "f", 7)
    assert b == f"{a}_l7" and len({n["id"] for n in s.nodes}) == 3
    s.ref("call", a, 2, unique=True, name="g")
    s.ref("call", a, 3, unique=True, name="g")
    s.ref("call", a, 4, name="g")
    assert [(r["node"], r["line"]) for r in s.refs] == [(1, 2), (1, 4)]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S3-N4: Out overrides Sink methods")
def test_s3_n4_rules_out_keeps_the_sink_signatures():
    import inspect

    from graphify_lang._common import Sink
    from graphify_lang.rules import Out

    clash = [m for m in vars(Out) if callable(vars(Out)[m]) and hasattr(Sink, m) and not m.startswith("__")
             and inspect.signature(getattr(Out, m)) != inspect.signature(getattr(Sink, m))]
    assert clash == []


def test_s3_n3_every_read_key_has_a_reader_in_code():
    """S3-N3: ``_READ`` is kept in this test, so each key's leaf name must also
    be read somewhere in ``graphify_lang`` (as a string literal), or the list
    could name a key nothing reads. ``extract.runtime`` is read by the registry
    for a GRAPHIFY_LANG_PATH plugin (``registry._path_manifest``)."""
    root = Path(__file__).resolve().parents[2] / "graphify_lang"
    code = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    missing = sorted(k for k in _READ | _READ_BY_RULES
                     if f'"{k.split(".")[-1]}"' not in code and f"'{k.split('.')[-1]}'" not in code)
    assert missing == []


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S3-N2: message omits v1")
def test_s3_n2_schema_message_names_both_forms(tmp_path):
    from graphify_lang.manifest import LanguageManifest

    toml = tmp_path / "m.toml"
    toml.write_text('schema = 2\n[language]\nname = "x"\nsuffixes = [".x"]\n[extract]\nruntime = "m"\n')
    assert LanguageManifest.from_toml(toml)[1] == ['schema must be 1 or "v1"']
