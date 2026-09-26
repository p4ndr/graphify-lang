"""Before/after corpus comparison for a plugin change (case 008, cc-CR000.003 S3-E2).

Not a pytest module: it needs the local corpora.

    .venv/bin/python tools/compare_corpus.py --before <ref> [--after <ref>] \\
        autolisp=~/repos/autolithp vba=~/repos/bim-chk ...

Each side is a tree of this repo: a git ref exported with ``git archive`` into a
temp dir, or the working tree when ``--after`` is omitted. Each corpus is a
``git archive HEAD`` copy of the repo, files = its ``git ls-files`` entries with
the plugin's suffixes. Each run is a subprocess with ``PYTHONPATH`` = the tree
and cwd outside it (so ``''`` on ``sys.path`` cannot shadow it), checks that
``graphify`` imports from that tree, and calls
``extract(files, cache_root=<fresh temp dir>, root=<corpus copy>)``.

Nodes are compared as their dicts minus ``id``; edges id-free, each endpoint as
``(source_file, label, node_kind)``. Prints one markdown row per corpus and the
first differing items; exits 1 when any corpus differs.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUFFIXES = {
    "autolisp": {".lsp", ".mnl", ".dcl", ".md"}, "vba": {".bas", ".cls", ".frm"},
    "bmake": {".mki", ".mke"}, "astgrep": {".yml", ".yaml"}, "ecschema": {".xml"},
    "cc-kb": {".md"}, "cargo": {".toml"},
}

_CHILD = r"""
import json, sys, tempfile
from pathlib import Path
import graphify
tree, root, out, files = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4:]
if not Path(graphify.__file__).resolve().is_relative_to(Path(tree).resolve()):
    sys.exit(f"graphify imported from {graphify.__file__}, not {tree}")
from graphify.extract import extract
with tempfile.TemporaryDirectory() as cache:
    g = extract([root / f for f in files], cache_root=Path(cache), root=root)
Path(out).write_text(json.dumps({"nodes": g["nodes"], "edges": g["edges"]}, default=str))
"""


def _archive(repo: Path, ref: str, dest: Path) -> Path:
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(repo), "archive", ref], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar, check=True)
    return dest


def _run(tree: Path, corpus: Path, files: list[str], scratch: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(tree)}
    out = scratch / "graph.json"  # extract prints progress on stdout
    proc = subprocess.run([sys.executable, "-c", _CHILD, str(tree), str(corpus), str(out), *files],
                          cwd=scratch, env=env, capture_output=True, text=True)
    if proc.returncode:
        sys.exit(f"extract failed in {tree}:\n{proc.stderr[-2000:]}")
    return json.loads(out.read_text())


def _summary(g: dict) -> tuple[dict, Counter, Counter]:
    by_id = {n["id"]: n for n in g["nodes"]}

    def end(nid: str) -> tuple:
        n = by_id.get(nid)
        return (str(n.get("source_file")), str(n.get("label")), str(n.get("node_kind"))) if n else ("?", nid, "?")
    nodes = Counter(json.dumps({k: v for k, v in n.items() if k != "id"}, sort_keys=True, default=str)
                    for n in g["nodes"])
    edges = Counter((end(e["source"]), e.get("relation"), end(e["target"])) for e in g["edges"])
    dangling = sum(1 for e in g["edges"] if e["source"] not in by_id or e["target"] not in by_id)
    counts = {"nodes": len(g["nodes"]), "ids": len(by_id), "edges": len(g["edges"]), "dangling": dangling}
    return counts, nodes, edges


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", required=True, help="git ref of this repo")
    ap.add_argument("--after", help="git ref of this repo (default: the working tree)")
    ap.add_argument("corpora", nargs="+", metavar="PLUGIN=REPO")
    args = ap.parse_args()
    differ = False
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        before = _archive(REPO, args.before, tmp / "before")
        after = _archive(REPO, args.after, tmp / "after") if args.after else REPO
        print("| Plugin | Repo | Files | Before nodes / ids / edges / dangling "
              "| After nodes / ids / edges / dangling | Node diff | Edge diff |")
        print("|:--|:--|--:|:--|:--|--:|--:|")
        notes = []
        for spec in args.corpora:
            plugin, _, repo = spec.partition("=")
            repo = Path(repo).expanduser()
            corpus = _archive(repo, "HEAD", tmp / "corpus" / f"{plugin}-{repo.name}")
            listed = subprocess.run(["git", "-C", str(repo), "ls-files"], check=True,
                                    capture_output=True, text=True).stdout.splitlines()
            files = sorted(f for f in listed if Path(f).suffix.lower() in SUFFIXES[plugin]
                           and (corpus / f).is_file())
            (cb, nb, eb), (ca, na, ea) = (_summary(_run(t, corpus, files, tmp)) for t in (before, after))
            nd, ed = (nb - na) + (na - nb), (eb - ea) + (ea - eb)
            fmt = " / ".join(str(c) for c in cb.values()), " / ".join(str(c) for c in ca.values())
            print(f"| {plugin} | {repo.name} | {len(files)} | {fmt[0]} | {fmt[1]} "
                  f"| {sum(nd.values())} | {sum(ed.values())} |")
            if nd or ed or cb != ca:
                differ = True
                notes += [f"{repo.name} node -: {k}" for k in list((nb - na).elements())[:5]]
                notes += [f"{repo.name} node +: {k}" for k in list((na - nb).elements())[:5]]
                notes += [f"{repo.name} edge -: {k}" for k in list((eb - ea).elements())[:5]]
                notes += [f"{repo.name} edge +: {k}" for k in list((ea - eb).elements())[:5]]
        for line in notes:
            print(line)
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
