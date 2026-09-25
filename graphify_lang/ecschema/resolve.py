"""ECSchema cross-file resolver (plan 04 §3.4, S12).

Consumes the ``ecschema_refs`` each extractor result carries.

- ``schema``: an ``imports`` edge from the schema node to the schema node with
  that ``schemaName`` (a candidate whose version equals the reference's is
  preferred). Unresolved references stay on ``ec_references`` only.
- ``member``: the ref's relation (``inherits``, ``source_constraint``,
  ``target_constraint``, ``uses``) from the class or property to the class or
  enumeration with that name in that schema.

One candidate resolves as EXTRACTED. Several (the same schema checked in
twice) resolve to the one sharing the longest directory prefix with the
source, as INFERRED; a tie is dropped (the AutoLISP, VBA, bmake and astgrep
resolvers' rule).
"""
from __future__ import annotations

import re
from pathlib import Path

from graphify.resolver_registry import LanguageResolver

_OUR_SUFFIXES = (".xml",)


def _version(v: str) -> tuple[int, ...]:
    parts = [int(x) for x in re.findall(r"\d+", v or "")]
    while parts and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _pick(found: list[dict], source_file: str) -> tuple[str | None, str]:
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


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    schemas: dict[str, list[dict]] = {}
    members: dict[tuple[str, str], list[dict]] = {}
    for n in all_nodes:
        if not str(n.get("source_file", "")).lower().endswith(_OUR_SUFFIXES):
            continue
        kind = n.get("node_kind")
        if kind == "schema":
            schemas.setdefault(str(n["label"]), []).append(n)
        elif kind in ("class", "enumeration") and n.get("ec_schema"):
            members.setdefault((str(n["ec_schema"]), str(n["label"])), []).append(n)

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}
    for res in per_file:
        if not (isinstance(res, dict) and res.get("ecschema_refs")):
            continue
        for ref in res["ecschema_refs"]:
            src = res["nodes"][ref["node"]]["id"]  # current id: colliding ids are salted by now
            if ref["kind"] == "schema":
                found = schemas.get(ref["schema"], [])
                same = [n for n in found if _version(n.get("version", "")) == _version(ref["version"])]
                tgt, conf = _pick(same or found, ref["source_file"])
                relation = "imports"
            else:
                tgt, conf = _pick(members.get((ref["schema"], ref["name"]), []), ref["source_file"])
                relation = ref["relation"]
            if tgt and tgt != src and (src, tgt, relation) not in seen:
                seen.add((src, tgt, relation))
                all_edges.append({"source": src, "target": tgt, "relation": relation,
                                  "confidence": conf, "source_file": ref["source_file"],
                                  "source_location": f"L{ref['line']}", "weight": 1.0})


RESOLVER = LanguageResolver(name="ecschema", suffixes=frozenset(_OUR_SUFFIXES), resolve=resolve)
