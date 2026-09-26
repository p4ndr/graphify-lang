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


def _graph(root: Path) -> tuple[set, set]:
    g = json.loads((root / "graphify-out" / "graph.json").read_text(encoding="utf-8"))
    ids = {n["id"] for n in g["nodes"]}
    edges = {(e["source"], e["target"], e["relation"]) for e in g["links"]
             if e["source"] in ids and e["target"] in ids}
    return ids, edges


def _clean(root: Path) -> tuple[set, set]:
    shutil.rmtree(root / "graphify-out", ignore_errors=True)
    from graphify.watch import _rebuild_code
    assert _rebuild_code(root, no_cluster=True, acquire_lock=False)
    return _graph(root)


@pytest.mark.parametrize("plugin", list(_PARITY))
def test_e5_incremental_parity(plugin, tmp_path):
    from graphify.watch import _rebuild_code

    folder, claims = _PARITY[plugin]
    root = tmp_path / folder
    shutil.copytree(FIXTURES / folder, root)
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and (p.suffix in claims or p.name in claims))
    assert files
    clean = _clean(root)
    assert clean[1], "the fixture graphs edges"
    for f in files:
        f.write_bytes(f.read_bytes())
        assert _rebuild_code(root, changed_paths=[f], no_cluster=True, acquire_lock=False)
        ids, edges = _graph(root)
        assert (sorted(clean[0] - ids), sorted(edges ^ clean[1])) == ([], []), f.name
        _clean(root)


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
            "version", "bmake_includes", "cc_kb_links"} <= set(context_fields())
