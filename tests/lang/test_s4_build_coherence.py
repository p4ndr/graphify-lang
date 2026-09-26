"""Plan 05 S4 - build coherence (cc-CR000.001 E5, H1, H3, L9, L11, M2, E1).

E5: for every plugin fixture, a clean build and a clean build followed by an
incremental build of one plugin file (``_rebuild_code(changed_paths=[f])``) give
the same node ids and ``(source, target, relation)`` edges. Edges with an
endpoint that is not a graphed node are left out: upstream's incremental merge
drops an unchanged file's dangling edges (``depends_on`` to an external crate)
with or without plugins. Only plugin files are touched: re-extracting a
same-stem ``foo.cpp`` / ``foo.h`` pair alone un-salts their ids, which is
upstream's own behaviour (measured with ``GRAPHIFY_LANG_DISABLE=1``).
H1 is the cause of the parity failures: the context nodes of unchanged files
lack the plugin fields the resolvers index by (``node_kind``, ...).
H3: an augment result must be a function of the file bytes, because the AST
cache keys it by them. L9: nothing outside the scan root is read.
M2 / E1: the AST cache namespace names the active plugin set.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from graphify.extract import extract

FIXTURES = Path(__file__).parent / "fixtures"

# plugin -> (fixture folder, the suffixes or file names of its files)
_PARITY = {
    "autolisp": ("plan02", (".lsp", ".mnl", ".dcl")),
    "autolisp-core": ("src", (".lsp", ".mnl", ".dcl")),
    "vba": ("vba", (".bas", ".cls", ".frm")),
    "bmake": ("bmake", (".mki", ".mke")),
    "cargo": ("cargo", ("Cargo.toml",)),
    "astgrep": ("astgrep", (".yml", ".yaml")),
    "ecschema": ("ecschema", (".xml",)),
    "cc-kb": ("cc_kb", (".md",)),
}


# Keys that differ between builds by design: provenance and clustering.
_VOLATILE = {"_origin", "community", "weight"}
# (plugin, path): the CLI path runs ``--code-only``, which skips ``.md``.
_PATHS = [(p, how) for p in _PARITY for how in ("watch", "cli") if (p, how) != ("cc-kb", "cli")]


def _graph(root: Path) -> tuple[dict, list]:
    """Node dicts by id and sorted edge dicts, minus ``_VOLATILE``."""
    g = json.loads((root / "graphify-out" / "graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: {k: v for k, v in n.items() if k not in _VOLATILE} for n in g["nodes"]}
    edges = sorted(json.dumps({k: v for k, v in e.items() if k not in _VOLATILE}, sort_keys=True)
                   for e in g.get("links", g.get("edges", []))
                   if e["source"] in nodes and e["target"] in nodes)
    return nodes, edges


def _run(how: str, root: Path, changed: list[Path] | None = None, monkeypatch=None) -> None:
    """A clean (``changed=None``, no graph) or incremental build by ``how``:
    ``watch._rebuild_code`` or ``graphify extract --code-only`` (cli.py)."""
    if how == "watch":
        from graphify.watch import _rebuild_code
        assert _rebuild_code(root, changed_paths=changed, no_cluster=True, acquire_lock=False)
        return
    from graphify.cli import dispatch_command
    monkeypatch.setattr(sys, "argv", ["graphify", "extract", str(root), "--code-only", "--no-cluster"])
    try:
        dispatch_command("extract")
    except SystemExit as done:
        assert done.code in (0, None)


def _clean(how: str, root: Path, monkeypatch=None) -> tuple[dict, list]:
    shutil.rmtree(root / "graphify-out", ignore_errors=True)
    _run(how, root, None, monkeypatch)
    return _graph(root)


@pytest.mark.parametrize("plugin,how", _PATHS)
def test_e5_incremental_parity(plugin, how, tmp_path, monkeypatch):
    """S4-L2: both hooked paths; each plugin file gets a byte appended (a real
    content change) and the incremental graph must equal a clean build of the
    edited tree, whole node and edge dicts."""
    folder, claims = _PARITY[plugin]
    root = tmp_path / folder
    shutil.copytree(FIXTURES / folder, root)
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and (p.suffix in claims or p.name in claims))
    assert files
    assert _clean(how, root, monkeypatch)[1], "the fixture graphs edges"
    for f in files:
        with f.open("ab") as fh:
            fh.write(b"\n")
        _run(how, root, [f], monkeypatch)
        incremental = _graph(root)
        assert incremental == _clean(how, root, monkeypatch), f.name


# S4-E1: an unchanged file's edge to a newly added target.
# case -> (files before, file added, the relation the incremental build misses)
_ADD = {
    "cargo": ({"Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
               "crates/a/Cargo.toml": '[package]\nname = "a"\nversion = "0.1.0"\n'},
              {"crates/b/Cargo.toml": '[package]\nname = "b"\nversion = "0.1.0"\n'}, "has_member"),
    "cc-kb": ({"docs/cc-XX000.000.md": "# Hub\n\nSee cc-XX000.001.\n"},
              {"docs/cc-XX000.001.md": "# Spoke\n"}, "cites"),
    "autolisp": ({"a.lsp": "(defun c:go () (helper))\n"}, {"b.lsp": "(defun helper () 1)\n"}, "calls"),
    "python": ({"a.py": "from b import helper\n\n\ndef go():\n    return helper()\n"},
               {"b.py": "def helper():\n    return 1\n"}, "calls"),
}


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S4-E1 known limit: an unchanged file's edge to an added target "
                          "appears on the next full or cached build only (upstream semantics)")
@pytest.mark.parametrize("case", list(_ADD))
def test_s4_e1_add_file_limit(case, tmp_path):
    before, added, relation = _ADD[case]
    root = tmp_path / "r"
    _write(root, before)
    _clean("watch", root)
    new = _write(root, added)
    _run("watch", root, new)

    def rel(edges: list) -> list:
        return [e for e in edges if json.loads(e)["relation"] == relation]
    incremental = rel(_graph(root)[1])
    clean = rel(_clean("watch", root)[1])
    assert clean, "a clean build has the edge"
    assert incremental == clean


def _write(root: Path, files: dict[str, str]) -> list[Path]:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return sorted(root / rel for rel in files)


def _edges(graph: dict, relation: str) -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in graph["edges"] if e["relation"] == relation}


def test_h3_new_member_crate_appears(tmp_path):
    root, cache = tmp_path / "ws", tmp_path / "cache"
    files = _write(root, {
        "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
        "crates/a/Cargo.toml": '[package]\nname = "a"\nversion = "0.1.0"\n',
    })
    first = extract(files, cache_root=cache, root=root)
    assert _edges(first, "has_member") == {("cargo_workspace_ws", "pkg_a")}
    files += _write(root, {"crates/b/Cargo.toml": '[package]\nname = "b"\nversion = "0.1.0"\n'})
    second = extract(sorted(files), cache_root=cache, root=root)   # root manifest: a cache hit
    assert _edges(second, "has_member") == {("cargo_workspace_ws", "pkg_a"),
                                            ("cargo_workspace_ws", "pkg_b")}


def test_h3_new_code_ref_target_appears(tmp_path):
    root, cache = tmp_path / "kb", tmp_path / "cache"
    doc_files = _write(root, {"docs/cc-XX000.000.md": "# Hub\n\nRuns `scripts/new.ps1`.\n"})
    extract(doc_files, cache_root=cache, root=root)
    files = doc_files + _write(root, {"scripts/new.ps1": "function New-Thing { }\n"})
    g = extract(sorted(files), cache_root=cache, root=root)        # the doc: a cache hit
    page = next(n["id"] for n in g["nodes"] if n.get("label") == "cc-XX000.000.md")
    script = next(n["id"] for n in g["nodes"] if n.get("label") == "new.ps1")
    assert (page, script) in _edges(g, "cites")


def test_l9_outer_workspace_ignored(tmp_path):
    outer = tmp_path / "outer"
    _write(outer, {"Cargo.toml": ('[workspace]\nmembers = ["repo"]\n[workspace.dependencies]\n'
                                  'foo = { path = "../lib", package = "real" }\n')})
    root = outer / "repo"
    files = _write(root, {"Cargo.toml": ('[package]\nname = "r"\nversion = "0.1.0"\n'
                                         '[dependencies]\nfoo = { workspace = true }\n')})
    g = extract(files, cache_root=tmp_path / "cache", root=root)
    assert ("pkg_r", "pkg_real") not in _edges(g, "depends_on")
    assert next(n for n in g["nodes"] if n["id"] == "pkg_r")["external_deps"] == ["foo"]


def test_l11_dotdot_ruledirs(tmp_path):
    files = _write(tmp_path, {
        "proj/sgconfig.yml": "ruleDirs:\n  - ../shared/rules\n",
        "shared/rules/r.yml": "id: r\nlanguage: python\nrule:\n  pattern: eval($A)\n",
    })
    g = extract(files, cache_root=tmp_path / "cache", root=tmp_path)
    ids = {n["label"]: n["id"] for n in g["nodes"] if n.get("node_kind") == "file"}
    assert (ids["sgconfig.yml"], ids["r.yml"]) in _edges(g, "loads")


_M2_PROBE = """
import json, sys
from pathlib import Path
from graphify.extract import extract
p = Path(sys.argv[1])
g = extract([p], cache_root=Path(sys.argv[2]), root=p.parent)
print(json.dumps(sorted(n.get("node_kind") or "-" for n in g["nodes"])))
"""


def _m2_run(src: Path, cache: Path, disable: bool) -> list[str]:
    env = {k: v for k, v in os.environ.items() if k != "GRAPHIFY_LANG_DISABLE"}
    if disable:
        env["GRAPHIFY_LANG_DISABLE"] = "1"
    out = subprocess.run([sys.executable, "-c", _M2_PROBE, str(src), str(cache)], env=env,
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


def test_m2_disable_toggle_uses_own_cache(tmp_path):
    src = _write(tmp_path / "p", {"app.lsp": "(defun c:go () (princ))\n(defun helper () 1)\n"})[0]
    cache = tmp_path / "cache"
    fresh = _m2_run(src, tmp_path / "fresh", disable=False)
    assert "command" in fresh                          # the AutoLISP extractor
    stock = _m2_run(src, cache, disable=True)
    assert "command" not in stock                      # stock Common Lisp
    assert _m2_run(src, cache, disable=False) == fresh


def test_m2_same_plugin_set_shares_cache(tmp_path):
    from graphify.cache import cache_dir

    files = _write(tmp_path / "p", {"app.lsp": "(defun c:go () (princ))\n"})
    extract(files, cache_root=tmp_path / "cache", root=tmp_path / "p")
    first = sorted(cache_dir(tmp_path / "cache").glob("*.json"))
    assert first
    extract(files, cache_root=tmp_path / "cache", root=tmp_path / "p")
    assert sorted(cache_dir(tmp_path / "cache").glob("*.json")) == first


def test_e1_pre_stage3_entries_unreachable(tmp_path):
    """Stage 3 open point: an entry written before stage 3 holds refs without
    ``node``. It lives in the plain ``v<version>-s<schema>`` namespace; E1 moves
    the live namespace away from it, so it is never read again."""
    import graphify.cache as cache_mod
    from importlib.metadata import version

    root, cache = tmp_path / "p", tmp_path / "cache"
    files = _write(root, {"app.lsp": "(defun c:go () (helper))\n",
                          "lib.lsp": "(defun helper () 1)\n"})
    extract(files, cache_root=cache, root=root)
    ast = cache / "graphify-out" / "cache" / "ast"
    plain = ast / f"v{version('graphifyy')}-s{cache_mod._AST_CACHE_SCHEMA}"
    entries = {p.name: json.loads(p.read_text()) for p in ast.glob("*/*.json")}
    assert entries
    for d in ast.iterdir():
        shutil.rmtree(d)
    cache_mod._cleaned_ast_dirs.clear()
    plain.mkdir(parents=True)
    for name, entry in entries.items():              # the pre-stage-3 shape
        for ref in entry.get("autolisp_refs", []):
            ref.pop("node", None)
            ref["source"] = "stale_id"
        (plain / name).write_text(json.dumps(entry))
    g = extract(files, cache_root=cache, root=root)
    by_label = {n["label"]: n["id"] for n in g["nodes"]}
    assert (by_label["c:go"], by_label["helper"]) in _edges(g, "calls")


def test_h1_context_fields_union():
    from graphify.lang_registry import context_fields

    assert {"node_kind", "astgrep_scope", "astgrep_role", "visibility", "accessor", "ec_schema",
            "version", "bmake_includes", "cc_kb_links", "cargo_ws_deps"} <= set(context_fields())


# --- plan 05 review-fix, S004 section of cc-CR000.003 ----------------------------

def test_s4_m1_no_packages_distributions(monkeypatch):
    """S4-M1: the plugin distributions come from their entry points; the
    full-environment ``packages_distributions()`` scan (~130 ms) is not run."""
    import importlib.metadata

    import graphify.cache as cache
    import graphify.lang_registry as core
    from graphify_lang import registry

    def scan():
        raise RuntimeError("packages_distributions() called")

    monkeypatch.setattr(importlib.metadata, "packages_distributions", scan)
    monkeypatch.setattr(cache, "_EXTRACTOR_VERSION", cache._EXTRACTOR_VERSION)
    core._fingerprint.cache_clear()
    try:
        core._namespace_ast_cache(registry)
    finally:
        core._fingerprint.cache_clear()
    assert "-lang" in cache._EXTRACTOR_VERSION


def test_s4_m1_single_file_plugin_hashes_own_file(tmp_path, monkeypatch):
    """S4-M1: a plugin shipped as a top-level module (``site-packages/x.py``)
    hashes that file, not its folder (all of ``site-packages``)."""
    import graphify.lang_registry as core

    (tmp_path / "s4m1_single.py").write_text("X = 1\n")
    (tmp_path / "neighbour.py").write_text("Y = 1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    __import__("s4m1_single")
    fp = core._fingerprint.__wrapped__
    first = fp(("x",), ("s4m1_single",))
    (tmp_path / "neighbour.py").write_text("Y = 2\n")
    assert fp(("x",), ("s4m1_single",)) == first
    (tmp_path / "s4m1_single.py").write_text("X = 2\n")
    assert fp(("x",), ("s4m1_single",)) != first


def test_s4_l1_fingerprint_failure_fails_closed(monkeypatch):
    """S4-L1: a failed fingerprint lands in a ``-langerr`` namespace, never the
    plain ``v<version>-s<schema>`` one a pre-S3 build wrote."""
    import graphify.cache as cache
    import graphify.lang_registry as core

    def boom(*_args):
        raise OSError("plugin file unreadable")

    monkeypatch.setattr(core, "_fingerprint", boom)
    monkeypatch.setattr(cache, "_EXTRACTOR_VERSION", cache._EXTRACTOR_VERSION)
    core._apply_registry()
    assert cache._EXTRACTOR_VERSION == f"{core._BASE_CACHE_VERSION}-langerr"


def test_s4_l3_hook_failure_is_logged(tmp_path, monkeypatch, caplog):
    """S4-L3: a registry failure in the incremental context hook reverts H1, so
    it is logged as a warning, not swallowed."""
    import logging

    from graphify_lang import registry

    root = tmp_path / "p"
    files = _write(root, {"a.lsp": "(defun c:go () (helper))\n", "b.lsp": "(defun helper () 1)\n"})
    _clean("watch", root)

    def boom(*_args):
        raise RuntimeError("context boom")

    monkeypatch.setattr(registry, "context_fields", boom)
    with caplog.at_level(logging.WARNING, logger="graphify.lang_registry"):
        _run("watch", root, [files[0]])
    assert any("context boom" in r.getMessage() and r.levelno >= logging.WARNING
               for r in caplog.records)


def test_s4_l4_fingerprint_covers_lang_registry(tmp_path, monkeypatch):
    """S4-L4: ``graphify/lang_registry.py`` (the fork's dispatch into the
    plugins) is part of the fingerprint, so an edit to it under an unchanged
    version string moves the AST cache namespace."""
    import graphify.lang_registry as core

    fp = core._fingerprint.__wrapped__
    first = fp(("x",), ())
    edited = tmp_path / "lang_registry.py"
    edited.write_text(Path(core.__file__).read_text() + "# edited\n")
    monkeypatch.setattr(core, "__file__", str(edited))
    assert fp(("x",), ()) != first
