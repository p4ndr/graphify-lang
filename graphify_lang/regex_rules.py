"""Regex tier: ``[[rule]]`` tables (S005 F8), ctags-optlib scope semantics.

Keys per rule:

- ``pattern`` (required): Python regex, compiled with ``re.MULTILINE``;
  ``multiline = true`` adds ``re.DOTALL`` so ``.`` crosses lines.
- ``name_group`` (default ``"name"``): group holding the symbol name.
- ``node = "<node_kind>"`` or ``edge = "<relation>"``: a definition or a
  reference. A rule with neither must be ``scope = "pop"``.
- ``scope``: ``push`` (node opens a scope), ``set`` (node replaces the
  current scope), ``pop`` (close the current scope), ``ref`` (default).
- ``target``: group holding an edge's target name (default ``name_group``).
- ``edge_from_scope`` (default true): the edge starts at the current scope;
  false, or no open scope, starts it at the file node.
- ``suffix``: a suffix or list of suffixes the rule is limited to.
- ``kind``: omitted or ``"regex"``; other kinds are not regex rules.

``[extract] comments``: one regex; matched text is blanked (newlines kept)
before any rule runs, so commented-out code emits nothing.

All matches of all rules run in source order, so scopes nest across rules.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SCOPES = ("push", "pop", "set", "ref")


class RegexRules:
    def __init__(self, rules: list[tuple[re.Pattern[str], dict[str, Any]]],
                 comments: re.Pattern[str] | None = None) -> None:
        self.rules = rules
        self.comments = comments

    @classmethod
    def from_manifest(cls, manifest_path: Path, manifest: dict[str, Any]) -> RegexRules | None:
        rules = []
        for i, rule in enumerate(manifest.get("rule", [])):
            if rule.get("kind", "regex") != "regex":
                continue
            where = f"rule[{i}]"
            if not isinstance(rule.get("pattern"), str):
                raise RuntimeError(f"{where}: pattern missing (failed to load)")
            scope = rule.get("scope", "ref")
            if scope not in _SCOPES:
                raise RuntimeError(f"{where}: scope must be one of {_SCOPES} (failed to load)")
            n_kinds = ("node" in rule) + ("edge" in rule)
            if n_kinds > 1 or (n_kinds == 0 and scope != "pop"):
                raise RuntimeError(f"{where}: needs exactly one of node / edge (failed to load)")
            flags = re.MULTILINE | (re.DOTALL if rule.get("multiline") else 0)
            try:
                rx = re.compile(rule["pattern"], flags)
            except re.error as exc:
                raise RuntimeError(f"{where}: bad pattern, failed to load: {exc}") from exc
            suffix = rule.get("suffix", ())
            rules.append((rx, {**rule, "scope": scope,
                               "suffix": {suffix} if isinstance(suffix, str) else set(suffix)}))
        comments = manifest.get("extract", {}).get("comments")
        if comments:
            try:
                comments = re.compile(comments, re.DOTALL)
            except re.error as exc:
                raise RuntimeError(f"extract.comments: bad pattern, failed to load: {exc}") from exc
        if not rules:
            return None
        return cls(rules, comments or None)

    def apply(self, text: str, path: Path, out: Any) -> None:
        if self.comments:
            text = self.comments.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
        suffix = path.suffix.lower()
        hits = sorted((
            (m.start(), i, m, rule)
            for i, (rx, rule) in enumerate(self.rules)
            if not rule["suffix"] or suffix in rule["suffix"]
            for m in rx.finditer(text)
        ), key=lambda h: h[:2])
        stack: list[str] = []
        for start, _, m, rule in hits:
            line = text.count("\n", 0, start) + 1
            scope = rule["scope"]
            if "node" in rule:
                nid = out.node(rule["node"], _group(m, rule.get("name_group", "name")), line)
                if scope == "push" or (scope == "set" and not stack):
                    stack.append(nid)
                elif scope == "set":
                    stack[-1] = nid
            elif "edge" in rule:
                name = _group(m, rule.get("target", rule.get("name_group", "name")))
                src = stack[-1] if stack and rule.get("edge_from_scope", True) else out.file_nid
                out.name_ref(src, name, rule["edge"], line)
            if scope == "pop" and stack:
                stack.pop()


def _group(m: re.Match[str], group: str) -> str:
    return m.group(group) if group in m.re.groupindex else m.group(0)
