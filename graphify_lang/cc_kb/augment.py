"""cc-*.md augment: document-schema attributes and reference payload.

File name schema ``cc-[CLASS][GROUP].[SUBGROUP][-S<NNN>].md``: CLASS is two
upper-case letters, GROUP and SUBGROUP three digits, SUBGROUP ``000`` is a
hub. On the page node of core ``extract_markdown`` this adds ``cc_id``,
``doc_class``, ``group``, ``subgroup``, ``is_hub`` and ``spoke`` (``S001``)
when present. ``cc_id`` is the join key to ``kb.db``; no DB is read here.

The cross-file part (doc -> doc mentions, hub -> spoke, doc -> code file)
needs the whole corpus, so the result carries a ``cc_kb_refs`` payload that
``resolve.py`` consumes. The augment reads only its own file, because the AST
cache keys a result by the file's bytes (plan 05 S4, cc-CR000.001 H3); the
scope check moved to the resolver. Scope (D6, D11): a ``docs/cc-*.md`` doc,
and the root ``*.md``, ``agents/**/*.md`` and ``skills/**/*.md`` files of a
harness root, which is a folder whose ``docs/`` holds a graphed ``cc-*.md``
file. Only ``docs/cc-*.md`` docs get the attributes and hub -> spoke edges.

- ``cc``: every ``cc-XXGGG.SSS[-SNNN]`` mention other than the doc itself,
  with the line of its first occurrence;
- ``code``: every backticked path-like span, optionally ``:line``, read as
  root-relative, first line only (the resolver keeps those that are graphed
  files); ``$CLAUDE_HOME/`` and ``~/.claude/`` prefixes are read as the root;
- ``up``: the candidate harness roots, as folders up from the file, in the
  order the resolver tries them.
- ``cc_heads`` / ``code_heads`` (D12): ``(ref, line, node)`` for the same
  refs, ``node`` being the index of the heading node whose section holds the
  mention (the nearest ``extract_markdown`` heading at or above the line).
  A mention above the first heading has only the page item.

``GRAPHIFY_CC_KB_OFF`` (comma list of ``attrs``, ``cc``, ``hubs``, ``code``)
switches an element off; the S14 value test measures each one.
"""
from __future__ import annotations

import os
import re
from bisect import bisect_right
from pathlib import Path

CC_ID = re.compile(r"cc-([A-Z]{2})(\d{3})\.(\d{3})(?:-S(\d{3}))?")
_NAME = re.compile(CC_ID.pattern + r"\.md")
_MENTION = re.compile(r"(?<![\w-])" + CC_ID.pattern + r"(?![\w-]|\.\d)")
_SPAN = re.compile(r"`([^`\n]+)`")
_FENCE = re.compile(r"^\s*(```|~~~)")
_PATHLIKE = re.compile(r"[\w.$~-][\w./\\$~-]*\.[A-Za-z0-9]{1,8}")
_ROOT_ALIASES = ("$CLAUDE_HOME/", "~/.claude/", "$env:USERPROFILE/.claude/")


def off(element: str) -> bool:
    return element in {e.strip() for e in os.environ.get("GRAPHIFY_CC_KB_OFF", "").split(",")}


def parse_cc_id(name: str) -> dict | None:
    """Attributes for a file name ``cc-SY050.001.md``, or None off-schema."""
    m = _NAME.fullmatch(name)
    if not m:
        return None
    cls, group, sub, spoke = m.groups()
    attrs = {"cc_id": name[:-3], "doc_class": cls, "group": group,
             "subgroup": sub, "is_hub": sub == "000" and spoke is None}
    if spoke:
        attrs["spoke"] = f"S{spoke}"
    return attrs


def _roots(path: Path) -> list[int]:
    """Candidate harness roots, as folders up from the file, in the order they
    are tried: the parent of ``docs/`` for a ``docs/cc-*`` file, the file's own
    folder, then the parent of each ``agents/`` or ``skills/`` ancestor. The
    resolver takes the first whose ``docs/`` holds a graphed ``cc-*.md`` (H3:
    nothing here reads another file)."""
    ups = [2] if path.parent.name == "docs" and path.name.startswith("cc-") else []
    ups.append(1)
    ups += [up + 1 for up, folder in enumerate(path.parents, 1)
            if folder.name in ("agents", "skills")]
    return list(dict.fromkeys(ups))


def _code_ref(span: str) -> tuple[str, int | None] | None:
    text = span.strip().replace("\\", "/")
    for alias in _ROOT_ALIASES:
        if text.startswith(alias):
            text = text[len(alias):]
            break
    m = re.fullmatch(r"(.+?)(?::(\d+))?", text)
    if m is None:  # empty span
        return None
    path, line = m.group(1), m.group(2)
    if not _PATHLIKE.fullmatch(path) or path.startswith("/") or ".." in path.split("/"):
        return None
    return path.removeprefix("./"), int(line) if line else None


def _heads(refs: dict[tuple[str, int], int]) -> list[tuple[str, int, int]]:
    return sorted((ref, line, node) for (ref, node), line in refs.items())


def augment_cc_kb(path: Path, base: dict) -> dict:
    path = Path(path)
    page = next((i for i, n in enumerate(base.get("nodes", []))
                 if n.get("node_kind") == "page"), None)
    if page is None:
        return {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    me = parse_cc_id(path.name) if path.parent.name == "docs" else None
    self_id = me["cc_id"] if me else None
    heads = sorted((int(n["source_location"][1:]), i) for i, n in enumerate(base["nodes"])
                   if n.get("node_kind") == "heading")
    cc: dict[str, int] = {}
    code: dict[str, int] = {}
    cc_at: dict[tuple[str, int], int] = {}
    code_at: dict[tuple[str, int], int] = {}
    fenced = False
    for no, line in enumerate(lines, 1):
        at = bisect_right(heads, (no, len(base["nodes"])))
        owner = heads[at - 1][1] if at else None
        for m in _MENTION.finditer(line):
            if m.group(0) != self_id:
                cc.setdefault(m.group(0), no)
                if owner is not None:
                    cc_at.setdefault((m.group(0), owner), no)
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in _SPAN.finditer(line):
            ref = _code_ref(m.group(1))
            if ref:
                code.setdefault(ref[0], no)
                if owner is not None:
                    code_at.setdefault((ref[0], owner), no)
    out: dict = {}
    page_attrs = dict(me) if me and not off("attrs") else {}
    # The doc's links to other .md files (every cc-kb edge joins a .md to
    # something), relative to its folder: a pair a link joins gets no second
    # edge, and an incremental build sees an unchanged doc's links only
    # through its context page node (H1).
    page_id = base["nodes"][page]["id"]
    links = sorted({os.path.relpath(e["target_file"], path.parent).replace("\\", "/")
                    for e in base.get("edges", []) if e.get("source") == page_id
                    and e.get("relation") == "references"
                    and str(e.get("target_file", "")).lower().endswith(".md")})
    if links:
        page_attrs["cc_kb_links"] = links
    if page_attrs:
        out["attrs"] = {page_id: page_attrs}
    refs = {"node": page, "up": _roots(path), "cc": [] if off("cc") else sorted(cc.items()),
            "code": [] if off("code") else sorted(code.items()),
            "hubs": bool(me) and not off("hubs")}
    refs["cc_heads"] = [] if off("cc") else _heads(cc_at)
    refs["code_heads"] = [] if off("code") else _heads(code_at)
    if refs["cc"] or refs["code"] or refs["hubs"]:
        out["cc_kb_refs"] = refs
    return out
