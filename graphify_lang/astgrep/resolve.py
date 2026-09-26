"""ast-grep cross-file resolver (plan 04 §3.4, S11).

Consumes the ``astgrep_refs`` each extractor result carries.

- ``test`` / ``snapshot``: a ``tested_by`` / ``has_snapshot`` edge from the rule
  node with that id to the test or snapshot file node.
- ``util``: a ``references`` edge from the rule or util to the global util node
  (one in a util file) with that id. Unknown ids are dropped.
- ``dir``: a ``loads`` edge from the sgconfig file node to each rule and util
  file node under that directory (relative to the sgconfig).

One candidate resolves as EXTRACTED. Several (two ast-grep projects in one
scan) resolve to the one sharing the longest directory prefix with the source,
as INFERRED; a tie is dropped (the AutoLISP, VBA and bmake resolvers' rule).
"""
from __future__ import annotations

import os
from pathlib import Path

from graphify.resolver_registry import LanguageResolver

from graphify_lang._common import pick_by_prefix as _pick, source_of

_OUR_SUFFIXES = (".yml", ".yaml")
_RELATION = {"test": "tested_by", "snapshot": "has_snapshot", "util": "references"}


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    rules: dict[str, list[dict]] = {}
    utils: dict[str, list[dict]] = {}
    files: list[dict] = []                     # rule and util file nodes
    for n in all_nodes:
        if not str(n.get("source_file", "")).lower().endswith(_OUR_SUFFIXES):
            continue
        if n.get("node_kind") == "rule":
            rules.setdefault(str(n["label"]), []).append(n)
        elif n.get("node_kind") == "util" and n.get("astgrep_scope") == "global":
            utils.setdefault(str(n["label"]), []).append(n)
        elif n.get("astgrep_role") in ("rule", "util"):
            files.append(n)

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}

    def add(src: str | None, tgt: str | None, relation: str, confidence: str, ref: dict) -> None:
        if src and tgt and src != tgt and (src, tgt, relation) not in seen:
            seen.add((src, tgt, relation))
            all_edges.append({"source": src, "target": tgt, "relation": relation,
                              "confidence": confidence, "source_file": ref["source_file"],
                              "source_location": f"L{ref['line']}", "weight": 1.0})

    for res in per_file:
        if not (isinstance(res, dict) and res.get("astgrep_refs")):
            continue
        for ref in res["astgrep_refs"]:
            owner = res["nodes"][ref["node"]]  # current id: colliding ids are salted by now
            kind = ref["kind"]
            if kind in ("test", "snapshot"):
                rule, conf = _pick(rules.get(ref["name"], []), ref["source_file"])
                add(rule, owner["id"], _RELATION[kind], conf, ref)
            elif kind == "util":
                util, conf = _pick(utils.get(ref["name"], []), ref["source_file"])
                add(owner["id"], util, "references", conf, ref)
            elif kind == "dir":
                # normpath both sides: is_relative_to is lexical, so
                # ``../shared/rules`` never matched (L11)
                base = os.path.normpath(str(Path(source_of(owner)).parent / ref["name"]))
                for f in files:
                    if Path(os.path.normpath(source_of(f))).is_relative_to(base):
                        add(owner["id"], f["id"], "loads", "EXTRACTED", ref)


RESOLVER = LanguageResolver(name="astgrep", suffixes=frozenset(_OUR_SUFFIXES), resolve=resolve)
