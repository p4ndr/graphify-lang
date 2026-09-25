"""cc-*.md augment: document-schema attributes and reference payload.

File name schema ``cc-[CLASS][GROUP].[SUBGROUP][-S<NNN>].md``: CLASS is two
upper-case letters, GROUP and SUBGROUP three digits, SUBGROUP ``000`` is a
hub. On the page node of core ``extract_markdown`` this adds ``cc_id``,
``doc_class``, ``group``, ``subgroup``, ``is_hub`` and ``spoke`` (``S001``)
when present. ``cc_id`` is the join key to ``kb.db``; no DB is read here.

The cross-file part (doc -> doc mentions, hub -> spoke, doc -> code file)
needs the whole corpus, so the result carries a ``cc_kb_refs`` payload that
``resolve.py`` consumes. Scope (D6, D11): a ``docs/cc-*.md`` doc, and the
root ``*.md``, ``agents/**/*.md`` and ``skills/**/*.md`` files of a harness
root, which is a folder whose ``docs/`` holds a ``cc-*.md`` file. Only
``docs/cc-*.md`` docs get the attributes and hub -> spoke edges; any other
``.md`` file is returned unchanged.

- ``cc``: every ``cc-XXGGG.SSS[-SNNN]`` mention other than the doc itself,
  with the line of its first occurrence;
- ``code``: every backticked path, optionally ``:line``, that is a file under
  the harness root, root-relative, first line only;
- ``up``: the number of folders from the file up to the harness root.
  ``$CLAUDE_HOME/`` and ``~/.claude/`` prefixes are read as the repo root.

``GRAPHIFY_CC_KB_OFF`` (comma list of ``attrs``, ``cc``, ``hubs``, ``code``)
switches an element off; the S14 value test measures each one.
"""
from __future__ import annotations

import os
import re
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


def _is_root(folder: Path) -> bool:
    """A harness root: ``folder/docs`` holds a ``cc-*.md`` file."""
    try:
        return any(_NAME.fullmatch(e.name) for e in os.scandir(folder / "docs"))
    except OSError:
        return False


def _scope(path: Path) -> tuple[Path, int, bool] | None:
    """(harness root, folders up to it, is a ``docs/cc-*.md`` file) when in scope."""
    parent = path.parent
    if parent.name == "docs" and path.name.startswith("cc-") and _is_root(parent.parent):
        return parent.parent, 2, True
    if _is_root(parent):
        return parent, 1, False
    for up, folder in enumerate(path.parents, 1):
        if folder.name in ("agents", "skills") and _is_root(folder.parent):
            return folder.parent, up + 1, False
    return None


def _code_ref(span: str, root: Path) -> tuple[str, int | None] | None:
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
    try:
        if not (root / path).is_file():
            return None
    except OSError:
        return None
    return path.removeprefix("./"), int(line) if line else None


def augment_cc_kb(path: Path, base: dict) -> dict:
    path = Path(path)
    scope = _scope(path)
    if scope is None:
        return {}
    root, up, kb_doc = scope
    page = next((i for i, n in enumerate(base.get("nodes", []))
                 if n.get("node_kind") == "page"), None)
    if page is None:
        return {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    me = parse_cc_id(path.name) if kb_doc else None
    self_id = me["cc_id"] if me else None
    cc: dict[str, int] = {}
    code: dict[str, int] = {}
    fenced = False
    for no, line in enumerate(lines, 1):
        for m in _MENTION.finditer(line):
            if m.group(0) != self_id:
                cc.setdefault(m.group(0), no)
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in _SPAN.finditer(line):
            ref = _code_ref(m.group(1), root)
            if ref and not path.samefile(root / ref[0]):
                code.setdefault(ref[0], no)
    out: dict = {}
    if me and not off("attrs"):
        out["attrs"] = {base["nodes"][page]["id"]: me}
    refs = {"node": page, "up": up, "cc": [] if off("cc") else sorted(cc.items()),
            "code": [] if off("code") else sorted(code.items()),
            "hubs": bool(me) and not off("hubs")}
    if refs["cc"] or refs["code"] or refs["hubs"]:
        out["cc_kb_refs"] = refs
    return out
