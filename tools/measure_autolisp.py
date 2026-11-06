"""Re-run the case 003 measurement (plan 02, A7) — fork vs stock on AutoLISP repos.

Not a pytest module: it needs the local corpus and the stock pipx venv.

    .venv/bin/python tools/measure_autolisp.py ~/repos/autolithp [more repos...]

Plan 06 mode reads a built graph and prints its AutoLISP quality numbers:

    .venv/bin/python tools/measure_autolisp.py --graph <repo>/graphify-out/graph.json [more graphs...]

Each engine runs in its own subprocess:
``graphify.extract.extract(files, cache_root=<fresh temp dir>, root=repo)`` over
every .lsp / .dcl / .mnl file (``.git/`` and ``graphify-out/`` excluded), so no
cache is shared (D11) and nothing is written inside the corpus. Ground truth is
regex over the same files. Prints markdown tables.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

STOCK_PY = Path.home() / ".local/share/pipx/venvs/graphifyy/bin/python"
FORK_PY = Path(__file__).resolve().parents[1] / ".venv/bin/python"
SUFFIXES = {".lsp", ".dcl", ".mnl"}
TOKEN_KINDS = {"sym_lit", "str_lit", "num_lit", "list_lit", "call", "name", "package_lit"}
DEFUN_RE = re.compile(r"^[ \t]*\(defun[ \t]+([^\s()]+)", re.M | re.I)
GLOBAL_RE = re.compile(r"^\(setq[ \t]+(\*[^*\s]+\*)", re.M)


def corpus(repo: Path) -> list[Path]:
    skip = {".git", "graphify-out"}
    return sorted(p for p in repo.rglob("*")
                  if p.is_file() and p.suffix.lower() in SUFFIXES and not skip & set(p.relative_to(repo).parts))


def run_engine(repo: str) -> None:
    """Child mode: extract, print JSON {nodes, edges, seconds, stdout_noise}."""
    import contextlib
    import io

    from graphify.extract import extract

    files = corpus(Path(repo))
    buf = io.StringIO()
    with tempfile.TemporaryDirectory() as cache, contextlib.redirect_stdout(buf):
        t0 = time.perf_counter()
        result = extract(files, cache_root=Path(cache), root=Path(repo))
        seconds = time.perf_counter() - t0
    json.dump({"nodes": result["nodes"], "edges": result["edges"], "seconds": seconds,
               "stdout_noise": buf.getvalue().count("DEBUG")}, sys.stdout)


def engine(python: Path, repo: Path) -> dict:
    out = subprocess.run([str(python), __file__, "--engine", str(repo)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def truth(repo: Path) -> dict:
    defuns, top_globals = set(), set()
    for p in corpus(repo):
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(repo).as_posix()
        if p.suffix.lower() != ".dcl":
            defuns |= {(rel, m.casefold()) for m in DEFUN_RE.findall(text)}
            top_globals |= {m.casefold() for m in GLOBAL_RE.findall(text)}
    return {"defuns": defuns, "top_globals": top_globals}


def quality(g: dict, t: dict, n_files: int) -> dict:
    nodes, edges = g["nodes"], g["edges"]
    kind = Counter(n.get("node_kind") for n in nodes)
    by_kind = lambda k: [n for n in nodes if n.get("node_kind") == k]  # noqa: E731
    fn = by_kind("function") + by_kind("command")
    found = {(n.get("source_file", ""), n.get("label", "").casefold()) for n in fn}
    globals_ = by_kind("global")
    labels = {n["id"]: n.get("label") for n in nodes}
    sf = {n["id"]: n.get("source_file") for n in nodes}
    rel = Counter(e["relation"] for e in edges)
    return {
        "nodes": len(nodes), "edges": len(edges), "seconds": g["seconds"],
        "files": n_files, "file_nodes": kind["file"],
        "functions": len(by_kind("function")), "commands": len(by_kind("command")),
        "fn_unique": len({(s, l) for s, l in found}), "truth": len(t["defuns"]),
        "missed": sorted(t["defuns"] - found),
        "globals": len(globals_), "globals_unique": len({n["label"].casefold() for n in globals_}),
        "globals_truth": len(t["top_globals"]),
        "locals": sum(1 for n in globals_ if not re.match(r"^\*.+\*$", n["label"])),
        "token_nodes": sum(kind[k] for k in TOKEN_KINDS),
        "missing_sf_label": sum(1 for n in nodes if not n.get("source_file") or not n.get("label")),
        "dup_ids": len(nodes) - len({n["id"] for n in nodes}),
        "dialogs": kind["dialog"], "modules": kind["module"],
        "relations": dict(sorted(rel.items())),
        "err_trap_inbound_xfile": sum(
            1 for e in edges if e["relation"] == "calls" and labels.get(e["target"], "").casefold() == "err:trap"
            and sf.get(e["source"]) != sf.get(e["target"])),
        "dcl_ref_lithp_mgr": sum(1 for e in edges if e["relation"] == "dcl_references"
                                 and labels.get(e["target"]) == "lithp_mgr"),
        "stdout_noise": g["stdout_noise"],
    }


def main(repos: list[str]) -> None:
    rows = []
    for r in repos:
        repo = Path(r).expanduser().resolve()
        files = corpus(repo)
        stock, fork = engine(STOCK_PY, repo), engine(FORK_PY, repo)
        q = quality(fork, truth(repo), len(files))
        rows.append((repo.name, files, stock, q))
    print("| Repo | Files (.lsp/.dcl/.mnl) | Stock nodes | Stock edges | Stock s | Fork nodes | Fork edges | Fork s | ≤ 3× stock + 1 s |")
    print("|:--|:--:|--:|--:|--:|--:|--:|--:|:--:|")
    for name, files, stock, q in rows:
        n = Counter(p.suffix.lower() for p in files)
        ok = q["seconds"] <= 3 * stock["seconds"] + 1
        print(f"| {name} | {n['.lsp']} / {n['.dcl']} / {n['.mnl']} | {len(stock['nodes'])} | {len(stock['edges'])} | "
              f"{stock['seconds']:.2f} | {q['nodes']} | {q['edges']} | {q['seconds']:.2f} | {'yes' if ok else 'NO'} |")
    print()
    print("| Repo | File nodes / files | Functions / commands | Unique fn / regex truth | Missed | Globals / unique / top-level truth | Non-`*x*` globals | Token nodes | Missing sf/label | Dup ids | Dialogs | Modules | DEBUG |")
    print("|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for name, _, _, q in rows:
        print(f"| {name} | {q['file_nodes']} / {q['files']} | {q['functions']} / {q['commands']} | "
              f"{q['fn_unique']} / {q['truth']} | {len(q['missed'])} | {q['globals']} / {q['globals_unique']} / "
              f"{q['globals_truth']} | {q['locals']} | {q['token_nodes']} | {q['missing_sf_label']} | {q['dup_ids']} | "
              f"{q['dialogs']} | {q['modules']} | {q['stdout_noise']} |")
    print()
    print("| Repo | Edges by relation | `err:trap` inbound cross-file calls | `dcl_references` → `lithp_mgr` |")
    print("|:--|:--|--:|--:|")
    for name, _, _, q in rows:
        rel = ", ".join(f"{k} {v}" for k, v in q["relations"].items())
        print(f"| {name} | {rel} | {q['err_trap_inbound_xfile']} | {q['dcl_ref_lithp_mgr']} |")
    for name, _, _, q in rows:
        if q["missed"]:
            print(f"\nMissed in {name}: " + ", ".join(f"{f}:{n}" for f, n in q["missed"][:20]))


def graph_numbers(path: Path) -> dict:
    """Plan 06 numbers for one built graph.json."""
    g = json.loads(path.read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g.get("links") or g.get("edges") or []
    lisp = {n["id"]: n for n in nodes if str(n.get("source_file", "")).lower().endswith((".lsp", ".mnl", ".dcl"))}
    calls = [e for e in edges if e.get("relation") == "calls" and e["source"] in lisp]
    fns = [n for n in lisp.values() if n.get("node_kind") in ("function", "command")]
    live = [n for n in fns if not n.get("shadow_of")]

    def dups(ns: list) -> int:
        return sum(1 for v in Counter(str(n.get("label", "")).casefold() for n in ns).values() if v > 1)
    deg: Counter = Counter()
    for e in edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    top = [lisp[i] for i, _ in deg.most_common() if i in lisp and not lisp[i].get("shadow_of")
           and lisp[i].get("node_kind") in ("function", "command")][:10]
    globals_ = {i for i, n in lisp.items() if n.get("node_kind") == "global"}
    used = {e["target"] for e in edges if e.get("relation") in ("reads_global", "writes_global")}
    inferred = sum(1 for e in calls if e.get("confidence") == "INFERRED")
    return {
        "calls": len(calls), "calls_inferred": inferred,
        "inferred_share": round(100 * inferred / len(calls), 1) if calls else 0.0,
        "calls_extracted": len(calls) - inferred,
        "dup_labels_all": dups(fns), "dup_labels_live": dups(live),
        "shadow_nodes": sum(1 for n in lisp.values() if n.get("shadow_of")),
        "shadow_files": len({n.get("source_file") for n in lisp.values() if n.get("shadow_of")}),
        "god10_dup": len(top) - len({str(n.get("label", "")).casefold() for n in top}),
        "globals": len(globals_), "globals_used": len(globals_ & used),
        "global_edges": sum(1 for e in edges if e.get("relation") in ("reads_global", "writes_global")),
        "module_depends": sum(1 for e in edges if e.get("relation") == "module_depends"),
    }


if __name__ == "__main__":
    if sys.argv[1:2] == ["--graph"]:
        for arg in sys.argv[2:]:
            print(arg, json.dumps(graph_numbers(Path(arg))))
    elif sys.argv[1:2] == ["--engine"]:
        run_engine(sys.argv[2])
    else:
        main(sys.argv[1:])
