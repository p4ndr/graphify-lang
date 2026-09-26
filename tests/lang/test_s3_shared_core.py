"""Plan 05 S3 - the shared plugin core (cc-CR000.001 H2, M4, M6).

H2: a resolver ref must name the node it came from after upstream has salted
colliding ids apart, so same-stem files keep their cross-file edges.
M4: a plugin file-node id is minted like a built-in one (``_make_id(str(path))``),
so upstream's portable remap applies: the same corpus gives the same ids under
any scan root, no id carries the root path, and no two nodes share an id.
M6: the rules engine imports a ``post_file`` hook only from ``graphify_lang.*``.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from graphify.extract import extract
from graphify_lang.rules import build

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


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="cc-CR000.001 H2: autolisp refs carry extraction-time ids")
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


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="cc-CR000.001 H2: vba refs carry extraction-time ids")
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


_M4_OPEN = {"autolisp", "vba"}  # each plugin move closes its own


@pytest.mark.parametrize("plugin", [
    pytest.param(p, marks=pytest.mark.xfail(strict=True, raises=AssertionError,
                 reason=f"cc-CR000.001 M4: {p} file ids drop the suffix")) if p in _M4_OPEN
    else p for p in _M4])
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


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="cc-CR000.001 M6: post_file imports any module")
def test_m6_post_file_prefix_only(tmp_path, monkeypatch):
    called = []
    monkeypatch.setitem(sys.modules, "evil_hook_mod",
                        types.SimpleNamespace(hook=lambda *a: called.append(a)))
    f = tmp_path / "s.ext"
    f.write_text("x\n")
    extract_fn, _ = build(tmp_path / "m.toml", {"extract": {"post_file": "evil_hook_mod:hook"}})
    r = extract_fn(f)
    assert called == []
    assert r["nodes"] == [] and "graphify_lang." in r.get("error", "")
