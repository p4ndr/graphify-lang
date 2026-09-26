"""Bentley bmake (.mki / .mke) extractor for graphify-lang (plan 04 §3.4, D7).

A line scanner, no grammar. ``#`` comments are cut (a full line, or from a
whitespace-preceded ``#``), then lines ending in ``\\`` are joined. Nodes: the
file, one ``macro`` per name defined in the file (``NAME = v``, ``NAME =% v``,
``NAME + v``; located at its first definition) and one ``target`` per
dependency-line target (``always:``, ``$(o)x$(oext) : $(src)x.cpp``). The file
contains its macros and targets. A use ``$(NAME)`` / ``${NAME}`` of a macro
defined in the same file is a ``references`` edge here; the source is the
macro being defined, the target whose dependency line or recipe holds the use,
or else the file. Everything cross-file is left on the result as
``bmake_refs`` for ``resolve.py``: ``%include`` (by basename), target
dependencies (by basename) and macros not defined in the file.

Recipe lines (indented deeper than their target line, up to a blank line or a
``%`` directive) give macro uses only, never definitions or targets.
"""
from __future__ import annotations

import re
from pathlib import Path

from graphify_lang._common import Sink, _make_id

_COMMENT_RE = re.compile(r"(^|\s)#.*$")
_DIRECTIVE_RE = re.compile(r"^%(\w+)\s*(.*)$")
_DEF_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*(=%|=(?!=)|\+)\s*(.*)$")
_TARGET_RE = re.compile(r"^([^\s:=%#][^:=]*?)\s*::?(?=\s|$)(.*)$")
_USE_RE = re.compile(r"\$[({]([A-Za-z_]\w*)[)}]")
_LEAD_MACROS_RE = re.compile(r"^(?:\$[({]\w+[)}])+")
_ONE_MACRO_RE = re.compile(r"\$[({](\w+)[)}]$")


def logical_lines(text: str) -> list[tuple[int, str]]:
    """(first physical line, text) per logical line: comments cut, ``\\`` joined.

    Blank lines are kept (as ``""``): they end a recipe."""
    out: list[tuple[int, str]] = []
    buf, start = "", 0
    for i, physical in enumerate(text.splitlines(), 1):
        if not buf:
            start = i
        line = _COMMENT_RE.sub("", physical).rstrip()
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        out.append((start, buf + line))
        buf = ""
    if buf:
        out.append((start, buf))
    return out


def _tail(path: str) -> str:
    """The last ``/`` or ``\\`` segment of a path, quotes stripped."""
    return re.split(r"[/\\]", path.strip().strip('"<>'))[-1]


def file_name(path: str) -> str | None:
    """Literal basename of a path such as ``$(Src)dir/x.cpp``; None if computed."""
    name = _LEAD_MACROS_RE.sub("", _tail(path))
    return name if name and "$" not in name and "%" not in name else None


def include_name(path: str, values: dict[str, list[tuple[int, str]]], line: int,
                 depth: int = 0) -> tuple[str | None, bool]:
    """(basename, expanded) for an ``%include`` path.

    A path that ends in a macro (``$(PolicyFile)``, ``$(DIR)$(NAME)``) is
    expanded through the last same-file definition above ``line``, up to three
    levels; ``expanded`` is True then (another ``%if`` branch may differ)."""
    name = file_name(path)
    if name or depth >= 3:
        return name, depth > 0
    m = _ONE_MACRO_RE.search(_tail(path))
    before = [v for ln, v in values.get(m.group(1), ()) if ln < line] if m else []
    if not before:
        return None, depth > 0
    return include_name(before[-1], values, line, depth + 1)


def extract_bmake(path: Path) -> dict:
    """Extract one bmake makefile (plan 04 §3.4)."""
    path = Path(path)
    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    lines = logical_lines(text)
    out = Sink(path)
    # Child ids carry the suffix (x.mki and x.mke share a file stem), but not
    # right after the stem: upstream reads <stem>_mki as a legacy id form of
    # the file and repoints cross-file edge endpoints that start with it.
    suffix = path.suffix.lstrip(".").lower()

    # Pass 1: classify lines; macro nodes at their first definition, targets.
    values: dict[str, list[tuple[int, str]]] = {}  # macro -> [(line, value)]
    macros: dict[str, str] = {}                    # macro -> node id
    targets: dict[str, str] = {}                   # target text -> node id
    work: list[tuple[str, int, str, list[str]]] = []  # (kind, line, text, source ids)
    recipe: tuple[int, list[str]] | None = None    # (target indent, target ids)
    for line, raw in lines:
        s = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if not s:
            recipe = None
            continue
        if s.startswith("%"):
            recipe = None
            work.append(("directive", line, s, [out.file_nid]))
            continue
        if recipe is not None and indent > recipe[0]:
            work.append(("recipe", line, s, recipe[1]))
            continue
        recipe = None
        if m := _DEF_RE.match(s):
            name, _, value = m.groups()
            values.setdefault(name, []).append((line, value))
            if name not in macros:
                macros[name] = out.add(_make_id(out.stem, "macro", suffix, name), name, "macro", line)
                out.edge(out.file_nid, macros[name], "contains", line)
            work.append(("use", line, value, [macros[name]]))
        elif m := _TARGET_RE.match(s):
            ids = []
            for t in m.group(1).split():
                if t not in targets:
                    targets[t] = out.add(_make_id(out.stem, "target", suffix, t), t, "target", line)
                    out.edge(out.file_nid, targets[t], "contains", line)
                ids.append(targets[t])
            work.append(("deps", line, m.group(2), ids))
            recipe = (indent, ids)
        else:
            work.append(("use", line, s, [out.file_nid]))

    # Pass 2: includes, dependencies and macro uses.
    for kind, line, s, sources in work:
        if kind == "directive":
            d = _DIRECTIVE_RE.match(s)
            if d and d.group(1).lower() == "include":
                name, expanded = include_name(d.group(2), values, line)
                out.ref("include", out.file_nid, line, name=name, raw=d.group(2).strip(),
                        expanded=expanded)
        if kind == "deps":
            for token in s.split():
                if (name := file_name(token)) and "." in name.strip("."):
                    for src in sources:
                        out.ref("depends", src, line, unique=True, name=name)
        for use in _USE_RE.finditer(s):
            for src in sources:
                if use.group(1) in macros:
                    out.edge(src, macros[use.group(1)], "references", line)
                else:
                    out.ref("macro", src, line, unique=True, name=use.group(1))
    return out.result("bmake_refs")
