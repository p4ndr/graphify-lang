"""Plan 04 S9 - bmake plugin (graphify_lang/bmake): exact node / edge pins.

Fixture tree: tests/lang/fixtures/bmake/ (app.mke, common.mki, policy.mki,
sub/rules.mki, src/foo.cpp, src/foo.h). Runs the real ``graphify.extract.extract``
pipeline, so the registry dispatch and the cross-file resolver are exercised.
"""
from __future__ import annotations

import getpass
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pytest

from graphify.extract import _get_extractor, extract
from graphify_lang.bmake.extract import extract_bmake

FIXTURE = Path(__file__).parent / "fixtures" / "bmake"
MK = (".mki", ".mke")


def _run(root: Path, cache: Path) -> dict:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    return extract(files, cache_root=cache, root=root)


@pytest.fixture(scope="module")
def graph(tmp_path_factory):
    root = tmp_path_factory.mktemp("bmake")
    shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
    return _run(root, tmp_path_factory.mktemp("cache"))


def _edges(graph, *relations):
    lab = {n["id"]: n.get("label") for n in graph["nodes"]}
    return sorted((e["relation"], e["confidence"], lab.get(e["source"]), lab.get(e["target"]))
                  for e in graph["edges"] if e["relation"] in relations)


def test_nodes_exact(graph):
    got = Counter((Path(n["source_file"]).name, n.get("node_kind"), n["label"])
                  for n in graph["nodes"] if n["source_file"].endswith(MK))
    assert got == Counter({
        ("app.mke", "file", "app.mke"): 1,
        ("app.mke", "macro", "appName"): 1,
        ("app.mke", "macro", "baseDir"): 1,        # two %if branches, one node
        ("app.mke", "macro", "PolicyFile"): 1,
        ("app.mke", "macro", "o"): 1,
        ("app.mke", "macro", "OBJS"): 1,           # `NAME + value`
        ("app.mke", "target", "always"): 1,
        ("app.mke", "target", "$(o)foo$(oext)"): 1,
        ("common.mki", "file", "common.mki"): 1,
        ("common.mki", "macro", "commonName"): 1,
        ("policy.mki", "file", "policy.mki"): 1,
        ("policy.mki", "macro", "PolicyLoaded"): 1,
        ("rules.mki", "file", "rules.mki"): 1,
        ("rules.mki", "target", "rules"): 1,       # recipe `x = $(o)` is no macro
    })


def test_edges_exact(graph):
    """Comments give nothing; undefined macros (SrcRoot, out) and `.r` are dropped."""
    assert _edges(graph, "imports", "depends_on", "references") == sorted([
        ("imports", "EXTRACTED", "app.mke", "common.mki"),
        ("imports", "EXTRACTED", "app.mke", "rules.mki"),     # $(SharedMki)sub/rules.mki
        ("imports", "INFERRED", "app.mke", "policy.mki"),     # via PolicyFile's value
        ("imports", "EXTRACTED", "foo.cpp", "foo.h"),         # upstream C++ #include
        ("depends_on", "EXTRACTED", "$(o)foo$(oext)", "foo.cpp"),
        ("depends_on", "EXTRACTED", "$(o)foo$(oext)", "foo.h"),  # after a `\` continuation
        ("references", "EXTRACTED", "PolicyFile", "baseDir"),
        ("references", "EXTRACTED", "app.mke", "PolicyFile"),    # %include $(PolicyFile)
        ("references", "EXTRACTED", "always", "o"),              # recipe line
        ("references", "EXTRACTED", "$(o)foo$(oext)", "baseDir"),
        ("references", "EXTRACTED", "$(o)foo$(oext)", "o"),
        ("references", "EXTRACTED", "OBJS", "o"),
        ("references", "EXTRACTED", "commonName", "appName"),    # up the include chain
        ("references", "EXTRACTED", "rules", "o"),
    ])


def test_every_include_is_accounted_for(graph):
    """Each %include directive is an imports edge or an unresolved_includes entry."""
    app = next(n for n in graph["nodes"] if n["label"] == "app.mke")
    assert app["unresolved_includes"] == "missing.mki"
    imports = [e for e in _edges(graph, "imports") if e[2] == "app.mke"]
    directives = [r for r in extract_bmake(FIXTURE / "app.mke")["bmake_refs"] if r["kind"] == "include"]
    assert (len(imports), len(directives)) == (3, 4)  # the two comment lines give nothing


def test_contains_tree(graph):
    got = _edges(graph, "contains")
    mk = [c for c in got if c[2] and c[2].endswith(MK)]
    assert len(mk) == 10  # every macro / target has its file as parent
    assert ("contains", "EXTRACTED", "rules.mki", "rules") in got


def test_same_stem_mki_and_mke(tmp_path):
    """x.mki and x.mke share a file stem; upstream salts the file ids apart before
    the resolvers run, and the edges follow the salted ids."""
    (tmp_path / "pch.mke").write_text("A = 1\n%include mdl.mki\n%include nothere.mki\n")
    (tmp_path / "pch.mki").write_text("%include mdl.mki\n%include gone.mki\n")
    (tmp_path / "mdl.mki").write_text("B = $(A)\n")
    g = _run(tmp_path, tmp_path / "cache")
    ids = {n["id"] for n in g["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in g["edges"])
    files = {n["label"]: n for n in g["nodes"] if n.get("node_kind") == "file"}
    assert files["pch.mke"]["id"] != files["pch.mki"]["id"]
    assert (files["pch.mke"]["unresolved_includes"], files["pch.mki"]["unresolved_includes"]) \
        == ("nothere.mki", "gone.mki")
    assert _edges(g, "imports", "references") == [
        ("imports", "EXTRACTED", "pch.mke", "mdl.mki"),
        ("imports", "EXTRACTED", "pch.mki", "mdl.mki"),
        ("references", "EXTRACTED", "B", "A"),   # pch.mki defines no A: one candidate
    ]


def test_ambiguous_macro_dropped(tmp_path):
    """Two includers in one directory define the macro: a tie, no edge."""
    for name in ("a.mke", "b.mke"):
        (tmp_path / name).write_text("X = 1\n%include shared.mki\n")
    (tmp_path / "shared.mki").write_text("Y = $(X)\n")
    g = _run(tmp_path, tmp_path / "cache")
    assert _edges(g, "references") == []
    assert len(_edges(g, "imports")) == 2


def test_undecodable_bytes_never_raise(tmp_path):
    path = tmp_path / "noise.mki"
    path.write_bytes(bytes(range(256)) * 8 + b"\n%include x.mki\nA = \xff$(B)\n")
    result = extract_bmake(path)
    assert result["nodes"][0]["node_kind"] == "file"
    assert [r["name"] for r in result["bmake_refs"] if r["kind"] == "include"] == ["x.mki"]


def test_mki_and_mke_go_straight_to_bmake():
    for suffix in (".mki", ".mke", ".MKE"):
        assert _get_extractor(Path("x" + suffix)) is extract_bmake


def test_lang_list_row():
    env = {k: v for k, v in os.environ.items() if k != "GRAPHIFY_LANG_DISABLE"}
    out = subprocess.run([sys.executable, "-m", "graphify", "lang", "list"],
                         capture_output=True, text=True, env=env, check=True).stdout
    rows = {line.split()[0]: line.split() for line in out.splitlines()[1:]}
    assert rows["bmake"] == ["bmake", ".mke", ".mki", "-", "-", "bmake"]


@pytest.mark.parametrize("repo", [
    pytest.param(FIXTURE, id="sample"),
    pytest.param(Path(os.path.expanduser(f"~{getpass.getuser()}")) / "repos/BentleyHelp",
                 marks=pytest.mark.corpus, id="BentleyHelp"),
])
def test_bentleyhelp_includes(repo, corpus_ls):
    """Plan 04 S9: every non-comment %include line in the corpus gives an edge or
    an unresolved_includes entry; `grep -c %include` also counts comment lines.
    The checked-in sample runs in CI; the private corpus is marked `corpus`."""
    if not repo.exists():
        pytest.skip(f"corpus: {repo.name} not on this host")
    names = corpus_ls(repo, "*.mki", "*.mke")
    files = [repo / n for n in names]
    directives = sum(1 for f in files for line in f.read_bytes().decode("utf-8", "replace").splitlines()
                     if re.match(r"\s*%include\b", line))
    g = extract(files, cache_root=Path(tempfile.mkdtemp()), root=repo)
    lower = {n.lower() for n in (Path(x).name for x in names)}
    refs = [r for f in files for r in extract_bmake(f)["bmake_refs"] if r["kind"] == "include"]
    resolved = [r for r in refs if r["name"] and r["name"].lower() in lower]
    unresolved = sum(len(n["unresolved_includes"].split("; "))
                     for n in g["nodes"] if n.get("unresolved_includes"))
    assert len(refs) == directives
    assert len(resolved) + unresolved == directives
    pairs = {(r["source_file"], r["name"].lower()) for r in resolved}
    assert len([e for e in g["edges"] if e["relation"] == "imports"]) == len(pairs)
