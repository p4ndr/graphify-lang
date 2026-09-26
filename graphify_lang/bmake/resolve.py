"""bmake cross-file resolver (plan 04 §3.4).

Consumes the ``bmake_refs`` each extractor result carries.

- ``include``: an ``imports`` edge from the file to the file node whose name
  matches the ``%include`` basename (case-insensitive, any graphed file). An
  include whose path was expanded through a same-file macro is INFERRED.
  Unresolved includes are not dropped: their raw paths are kept on the file
  node as ``unresolved_includes`` (``"; "``-joined), so each directive is
  accounted for either way.
- ``depends``: a ``depends_on`` edge from a target to the graphed file of that
  basename (``.cpp``, ``.h``, ``.mke``...). No file node: dropped (a ``.r``
  resource is not graphed, and object outputs never exist).
- ``macro``: a ``references`` edge to a macro node defined in a file on the
  include chain of the user (a file it includes, directly or not, or one that
  includes it), the scope bmake's textual include gives a macro. Undefined
  names (environment, built-ins such as ``SrcRoot``): dropped.

One candidate resolves as EXTRACTED. Several resolve to the one sharing the
longest directory prefix with the source, as INFERRED; a tie is dropped (the
AutoLISP and VBA resolvers' rule).
"""
from __future__ import annotations

from pathlib import Path

from graphify.resolver_registry import LanguageResolver

from graphify_lang._common import pick_by_prefix as _pick, refs_of, source_of

_OUR_SUFFIXES = (".mki", ".mke")


def _reach(start: str, graph: dict[str, set[str]]) -> set[str]:
    seen, stack = set(), [start]
    while stack:
        for nxt in graph.get(stack.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    files: dict[str, list[dict]] = {}          # folded basename -> file nodes
    macros: dict[str, list[dict]] = {}         # macro name -> macro nodes
    by_id: dict[str, dict] = {}
    file_of: dict[str, str] = {}               # source path -> bmake file node id
    includers: list[dict] = []                 # bmake file nodes with includes
    for n in all_nodes:
        sf = source_of(n)
        if n.get("label") == Path(sf).name:
            files.setdefault(Path(sf).name.casefold(), []).append(n)
            if sf.lower().endswith(_OUR_SUFFIXES) and n.get("node_kind") == "file":
                file_of.setdefault(sf, n["id"])
                if n.get("bmake_includes"):
                    includers.append(n)
        if n.get("node_kind") == "macro" and sf.lower().endswith(_OUR_SUFFIXES):
            macros.setdefault(str(n["label"]), []).append(n)
        by_id.setdefault(n["id"], n)

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}

    def add(ref: dict, target: str | None, confidence: str, relation: str) -> bool:
        if not target:
            return False
        key = (ref["source"], target, relation)
        if target != ref["source"] and key not in seen:
            seen.add(key)
            all_edges.append({"source": ref["source"], "target": target, "relation": relation,
                              "confidence": confidence, "source_file": ref["source_file"],
                              "source_location": f"L{ref['line']}", "weight": 1.0})
        return True

    refs = refs_of(per_file, "bmake_refs")
    unresolved: dict[str, list[str]] = {}
    for ref in (r for r in refs if r["kind"] == "include"):
        target, confidence = (None, "EXTRACTED")
        if ref["name"]:
            target, confidence = _pick(files.get(ref["name"].casefold(), []), ref["source_file"])
        if ref["expanded"]:
            confidence = "INFERRED"
        if not add(ref, target, confidence, "imports"):
            unresolved.setdefault(ref["source"], []).append(ref["raw"])
    for nid, raws in unresolved.items():
        if nid in by_id:
            by_id[nid]["unresolved_includes"] = "; ".join(raws)

    # The include graph from every bmake file node, unchanged ones included,
    # resolved as the include refs are.
    down: dict[str, set[str]] = {}             # file id -> included file ids
    up: dict[str, set[str]] = {}
    for n in includers:
        for name in n["bmake_includes"]:
            target, _ = _pick(files.get(name.casefold(), []), source_of(n))
            if target:
                down.setdefault(n["id"], set()).add(target)
                up.setdefault(target, set()).add(n["id"])
    scope: dict[str, set[str]] = {}            # file id -> file ids on its include chain
    for ref in refs:
        if ref["kind"] == "depends":
            add(ref, *_pick(files.get(ref["name"].casefold(), []), ref["source_file"]), "depends_on")
        elif ref["kind"] == "macro":
            fid = file_of.get(ref["source_file"])
            if fid not in scope:
                scope[fid] = _reach(fid, down) | _reach(fid, up)
            chain = scope[fid]
            found = [n for n in macros.get(ref["name"], ())
                     if file_of.get(source_of(n)) in chain]
            add(ref, *_pick(found, ref["source_file"]), "references")


RESOLVER = LanguageResolver(name="bmake", suffixes=frozenset(_OUR_SUFFIXES), resolve=resolve)
