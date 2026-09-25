"""AutoLISP cross-file resolver (plan 02 §3).

Consumes the ``autolisp_refs`` each extractor result carries and emits
``calls``, ``dcl_references``, ``dcl_action``, ``module_depends`` and
``sidecar_doc`` edges. A name resolves case-insensitively; a same-file target
wins, otherwise exactly one corpus-wide target is required. Ambiguous and
unresolved names are dropped (the same god-node guard the core member-call
resolvers use). The registry registers ``RESOLVER``; this module never
registers itself.
"""
from __future__ import annotations

from pathlib import Path

from graphify.resolver_registry import LanguageResolver

_OUR_SUFFIXES = (".lsp", ".mnl", ".dcl")
_GROUP = {"function": "fn", "command": "fn", "dialog": "dialog", "module": "module"}


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    index: dict[str, dict[str, list[dict]]] = {}
    by_label: dict[str, list[dict]] = {}
    for node in all_nodes:
        by_label.setdefault(str(node.get("label", "")), []).append(node)
        group = _GROUP.get(node.get("node_kind"))
        if group and str(node.get("source_file", "")).lower().endswith(_OUR_SUFFIXES):
            index.setdefault(group, {}).setdefault(str(node.get("label", "")).casefold(), []).append(node)

    def lookup(group: str, name: str, source_file: str) -> tuple[str | None, str]:
        """(target id, confidence). One candidate: EXTRACTED. Several: the one
        sharing the longest directory prefix with the caller, INFERRED (an
        archived copy of a module must not capture calls from live code); a tie
        on that prefix is dropped, as the core member-call resolvers drop
        ambiguous names."""
        found = index.get(group, {}).get(name.casefold(), [])
        if len(found) <= 1:
            return (found[0]["id"] if found else None), "EXTRACTED"
        caller = Path(source_file).parts
        def shared(node: dict) -> int:
            n = 0
            for a, b in zip(caller, Path(str(node.get("source_file", ""))).parts):
                if a != b:
                    break
                n += 1
            return n
        scores = sorted(((shared(n), n["id"]) for n in found), reverse=True)
        if scores[0][0] == scores[1][0]:
            return None, "EXTRACTED"
        return scores[0][1], "INFERRED"

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}

    def add(src: str, tgt: str | None, confidence: str = "EXTRACTED", *, relation: str, ref: dict, **extra) -> None:
        if not tgt or tgt == src or (src, tgt, relation) in seen:
            return
        seen.add((src, tgt, relation))
        all_edges.append({"source": src, "target": tgt, "relation": relation,
                          "confidence": confidence, "source_file": ref["source_file"],
                          "source_location": f"L{ref['line']}", "weight": 1.0, **extra})

    refs = [r for result in per_file if isinstance(result, dict) for r in result.get("autolisp_refs", ())]
    dialogs_of: dict[str, list[str]] = {}
    # EXTRACTED dialog refs first so an INFERRED duplicate never wins the de-dup.
    for ref in sorted((r for r in refs if r["kind"] == "dialog"), key=lambda r: r["confidence"] != "EXTRACTED"):
        target, confidence = lookup("dialog", ref["name"], ref["source_file"])
        if target:
            dialogs_of.setdefault(ref["source"], []).append(target)
            add(ref["source"], target, "INFERRED" if "INFERRED" in (confidence, ref["confidence"]) else "EXTRACTED",
                relation="dcl_references", ref=ref)
    for ref in refs:
        kind = ref["kind"]
        if kind == "call":
            add(ref["source"], *lookup("fn", ref["name"], ref["source_file"]), relation="calls", ref=ref)
        elif kind == "depends":
            add(ref["source"], *lookup("module", ref["name"], ref["source_file"]), relation="module_depends", ref=ref)
        elif kind == "sidecar":
            doc = Path(ref["name"])
            if doc.with_suffix("") == Path(ref["source_file"]).with_suffix(""):
                continue  # same stem: graphify already gives both files one node id
            # The doc's own file node: same file name, source_file = the path
            # (absolute, or already root-relative when its extractor ran first).
            docs = [n["id"] for n in by_label.get(doc.name, ())
                    if str(doc) == str(n.get("source_file")) or str(doc).endswith("/" + str(n.get("source_file")))]
            add(ref["source"], docs[0] if len(docs) == 1 else None, relation="sidecar_doc", ref=ref)
        elif kind == "action":
            fn, confidence = lookup("fn", ref["name"], ref["source_file"])
            for dialog in dict.fromkeys(dialogs_of.get(ref["source"], ())):
                add(dialog, fn, confidence, relation="dcl_action", ref=ref, key=ref["key"])


RESOLVER = LanguageResolver(name="autolisp", suffixes=frozenset(_OUR_SUFFIXES), resolve=resolve)
