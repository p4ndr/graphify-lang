"""cc-kb cross-file resolver (plan 04 §3.4, S13).

Consumes the ``cc_kb_refs`` payload of each augmented ``cc-*.md`` result.
Targets are found by file name, never by id scheme:

- a ``cc`` mention -> the page node of ``cc-<id>.md`` in the same ``docs/``
  folder (edge ``RELATION``,
  context ``cc_ref``); a mention with no such doc in the corpus goes to the
  ``dangling_cc_refs`` list on the citing page node;
- ``hubs`` -> ``contains`` (context ``hub_spoke``) from the parent doc:
  ``cc-XXGGG.000`` for ``cc-XXGGG.SSS``, ``cc-XXGGG.SSS`` for its ``-SNNN``
  spoke. The edge is owned by the child's file;
- a ``code`` path -> the file node of that path under the doc's repo root
  (edge ``RELATION``, context ``code_ref``). A path that is not a graphed
  file adds nothing.

A pair that any edge already joins (a Markdown link, say) gets no second edge.
"""
from __future__ import annotations

import posixpath

from graphify.resolver_registry import LanguageResolver

from graphify_lang.cc_kb.augment import CC_ID

# Not ``references``: graphify.watch._reconcile_markdown_links prunes an AST
# ``references`` edge from a Markdown file that no authored link backs, so
# on ``graphify update`` every mention and code-path edge would be dropped.
RELATION = "cites"


def _norm(source_file: str) -> str:
    return posixpath.normpath(str(source_file).replace("\\", "/"))


def _parent(cc_id: str) -> str | None:
    m = CC_ID.fullmatch(cc_id)
    if not m:
        return None
    cls, group, sub, spoke = m.groups()
    if spoke:
        return f"cc-{cls}{group}.{sub}"
    return None if sub == "000" else f"cc-{cls}{group}.000"


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    docs: dict[tuple[str, str], dict] = {}  # (docs dir, cc_id) -> page node
    files: dict[str, dict] = {}
    for n in all_nodes:
        sf = n.get("source_file")
        if not sf or n.get("label") != posixpath.basename(_norm(sf)):
            continue  # not a file / page node
        files.setdefault(_norm(sf), n)
        name = str(n["label"])
        folder = posixpath.dirname(_norm(sf))
        if (CC_ID.fullmatch(name[:-3]) and name.endswith(".md") and n.get("node_kind") == "page"
                and posixpath.basename(folder) == "docs"):
            docs.setdefault((folder, name[:-3]), n)

    pairs = {frozenset((e.get("source"), e.get("target"))) for e in all_edges}

    def add(src: str, tgt: str, relation: str, context: str, sf: str, line: int | None) -> None:
        pair = frozenset((src, tgt))
        if src == tgt or pair in pairs:
            return
        pairs.add(pair)
        all_edges.append({"source": src, "target": tgt, "relation": relation,
                          "context": context, "confidence": "EXTRACTED",
                          "confidence_score": 1.0, "source_file": sf,
                          "source_location": f"L{line or 1}", "weight": 1.0})

    work = []
    for res in per_file:
        if isinstance(res, dict) and res.get("cc_kb_refs"):
            node = res["nodes"][res["cc_kb_refs"]["node"]]
            me = next((n for n in all_nodes if n.get("id") == node["id"]), node)
            work.append((res["cc_kb_refs"], me, node.get("source_file", "")))

    # Hub -> spoke first: a structural edge wins a pair over a mention.
    for refs, me, sf in work:
        if refs.get("hubs"):
            parent = docs.get((posixpath.dirname(_norm(sf)), _parent(str(me.get("label", ""))[:-3])))
            if parent is not None:
                add(parent["id"], me["id"], "contains", "hub_spoke", sf, 1)
    for refs, me, sf in work:
        dangling = []
        for cc_id, line in refs.get("cc", []):
            target = docs.get((posixpath.dirname(_norm(sf)), cc_id))
            if target is None:
                dangling.append(cc_id)
            else:
                add(me["id"], target["id"], RELATION, "cc_ref", sf, line)
        if dangling and "dangling_cc_refs" not in me:
            me["dangling_cc_refs"] = dangling
        root = posixpath.dirname(posixpath.dirname(_norm(sf)))
        for rel, line in refs.get("code", []):
            target = files.get(_norm(posixpath.join(root, rel)))
            if target is not None:
                add(me["id"], target["id"], RELATION, "code_ref", sf, line)

RESOLVER = LanguageResolver(name="cc-kb", suffixes=frozenset({".md"}), resolve=resolve)
