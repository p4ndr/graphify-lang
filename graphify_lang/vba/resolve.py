"""VBA cross-module resolver (plan 04 §3.4).

Consumes the ``vba_refs`` each extractor result carries and emits ``calls``,
``implements`` and ``uses`` edges. Names match case-insensitively, as VBA does.

- ``call`` with no qualifier: a non-private Sub / Function / Declare of a
  standard module (``.bas``); class and form members need an object.
- ``call`` with a qualifier (``Module.Proc`` or ``obj.Method`` with ``obj As
  Class``): a non-private member of the module / class / form of that name.
- ``implements`` / ``uses``: a class or form of that name, or a public Type /
  Enum.

One candidate resolves as EXTRACTED. Several resolve to the one sharing the
longest directory prefix with the caller, as INFERRED; a tie is dropped (the
AutoLISP resolver's rule). Unresolved names are dropped.
"""
from __future__ import annotations

from graphify.resolver_registry import LanguageResolver
from graphify_lang._common import pick_by_prefix as _pick, refs_of
from graphify_lang.vba.extract import accessor_match

_OUR_SUFFIXES = (".bas", ".cls", ".frm")
_MODULES = ("module", "class", "form")
_MEMBERS = ("sub", "function", "property", "declare")


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    ours = [n for n in all_nodes if str(n.get("source_file", "")).lower().endswith(_OUR_SUFFIXES)]
    by_id = {n["id"]: n for n in ours}
    parent: dict[str, str] = {}
    for e in all_edges:
        if e.get("relation") == "contains" and e.get("target") in by_id:
            parent[e["target"]] = e["source"]

    public: dict[str, list[dict]] = {}        # unqualified: .bas members
    qualified: dict[tuple[str, str], list[dict]] = {}
    types: dict[str, list[dict]] = {}
    for n in ours:
        kind, label = n.get("node_kind"), str(n.get("label", "")).casefold()
        if kind in ("class", "form"):
            types.setdefault(label, []).append(n)
        if n.get("visibility") == "private":
            continue
        if kind in ("type", "enum"):
            types.setdefault(label, []).append(n)
        elif kind in _MEMBERS:
            owner = by_id.get(parent.get(n["id"], ""))
            if owner is None:
                continue
            qualified.setdefault((str(owner.get("label", "")).casefold(), label), []).append(n)
            if owner.get("node_kind") == "module":
                public.setdefault(label, []).append(n)

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}
    refs = refs_of(per_file, "vba_refs")
    for ref in refs:
        name = ref["name"].casefold()
        if ref["kind"] == "call":
            found = (qualified.get((ref["qualifier"].casefold(), name), [])
                     if ref.get("qualifier") else public.get(name, []))
            relation = "calls"
        else:
            found, relation = types.get(name, []), ref["kind"]
        if relation == "calls":  # a property is reached through its matching accessor
            keep = set(accessor_match([(n["id"], n.get("accessor", "")) for n in found],
                                      ref.get("accessor", "get")))
            found = [n for n in found if n["id"] in keep]
        target, confidence = _pick(found, ref["source_file"])
        key = (ref["source"], target, relation)
        if target and target != ref["source"] and key not in seen:
            seen.add(key)
            all_edges.append({"source": ref["source"], "target": target, "relation": relation,
                              "confidence": confidence, "source_file": ref["source_file"],
                              "source_location": f"L{ref['line']}", "weight": 1.0})


RESOLVER = LanguageResolver(name="vba", suffixes=frozenset(_OUR_SUFFIXES), resolve=resolve)
