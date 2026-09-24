"""Regex rules for full key set extraction (F8).

This module implements regex-based extraction rules with the full key set:
- pattern: regex pattern to match
- name_group: capture group name for the symbol
- node or edge: whether this creates a node or edge
- scope (push/pop/ref/set): scope tracking for edges
- edge_from_scope: source of cross-file edges
- target: target symbol for ref edges
- multiline: whether pattern spans multiple lines
- suffix: file suffix constraint
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class RegexRules:
    """Regex extraction rules."""

    def __init__(
        self,
        rules: list[dict[str, Any]],
    ):
        """Initialize regex rules.

        Args:
            rules: List of rule dictionaries with keys:
                pattern, name_group, type (node/edge), scope,
                edge_from_scope, target, multiline, suffix
        """
        self.rules = rules
        self._compiled: list[tuple[re.Pattern, dict[str, Any]]] = []

        # Compile patterns
        for rule in self.rules:
            pattern = rule.get("pattern", "")
            flags = re.MULTILINE if rule.get("multiline", False) else 0
            try:
                compiled = re.compile(pattern, flags)
                self._compiled.append((compiled, rule))
            except re.error:
                # Skip invalid patterns
                continue

    @classmethod
    def from_manifest(
        cls, manifest_path: Path, manifest: dict[str, Any]
    ) -> RegexRules:
        """Build RegexRules from a manifest.

        Looks for [[rule]] entries in the manifest.
        """
        rules: list[dict[str, Any]] = []

        # Check for [[rule]] entries
        if "rule" in manifest:
            for rule_cfg in manifest["rule"]:
                # Only process regex rules
                if rule_cfg.get("kind") != "regex":
                    continue
                rule = {
                    "name": rule_cfg.get("name", ""),
                    "pattern": rule_cfg.get("pattern", ""),
                    "name_group": rule_cfg.get("name_group", "name"),
                    "type": rule_cfg.get("type", "node"),
                    "scope": rule_cfg.get("scope", "ref"),
                    "edge_from_scope": rule_cfg.get("edge_from_scope", ""),
                    "target": rule_cfg.get("target", ""),
                    "multiline": rule_cfg.get("multiline", False),
                    "suffix": rule_cfg.get("suffix", ""),
                }
                rules.append(rule)

        return cls(rules)

    def apply(self, source: bytes, source_file: str = "") -> dict[str, list[dict]]:
        """Apply regex rules to source code.

        Returns nodes and edges based on regex matches.
        """
        nodes: list[dict] = []
        edges: list[dict] = []

        if not self._compiled:
            return {"nodes": nodes, "edges": edges}

        text = source.decode("utf-8", errors="replace")

        # Track scopes for push/pop semantics
        scope_stack: list[str] = []
        current_scope = ""

        for pattern, rule in self._compiled:
            matches = list(pattern.finditer(text))

            for match in matches:
                # Get the captured name
                name_group = rule.get("name_group", "name")
                if name_group in match.groupdict():
                    symbol = match.group(name_group)
                else:
                    symbol = match.group(0)

                # Determine scope
                scope = rule.get("scope", "ref")
                if scope == "push":
                    scope_stack.append(symbol)
                    current_scope = symbol
                elif scope == "pop":
                    if scope_stack:
                        scope_stack.pop()
                        current_scope = scope_stack[-1] if scope_stack else ""
                elif scope == "set":
                    current_scope = symbol

                # Determine edge_from_scope
                edge_from_scope = rule.get("edge_from_scope", "")
                if edge_from_scope:
                    if scope_stack:
                        source_symbol = scope_stack[-1]
                    else:
                        source_symbol = current_scope
                else:
                    source_symbol = ""
                # Create node or edge
                rule_type = rule.get("type", "node")
                if rule_type == "node":
                    node_dict = self._make_node(symbol, match, rule)
                    nodes.append(node_dict)
                else:
                    target = rule.get("target", "")
                    if not target:
                        target = match.group("target") if "target" in match.groupdict() else ""
                    elif target in match.groupdict():
                        # Use the matched value from the named group
                        target = match.group(target)
                    edge_dict = self._make_edge(
                        source_symbol,
                        target,
                        match,
                        rule,
                        current_scope,
                    )
                    edges.append(edge_dict)

        return {"nodes": nodes, "edges": edges}

    def _make_node(self, symbol: str, match: re.Match, rule: dict) -> dict:
        """Create a node dictionary."""
        start = match.start()
        end = match.end()

        # Calculate line/column from position
        text = match.string
        lines_before = text[:start].count('\n')
        line_start = text.rfind('\n', 0, start) + 1
        col_start = start - line_start

        return {
            "kind": rule.get("name_group", symbol),
            "start_line": lines_before + 1,
            "start_col": col_start,
            "end_line": lines_before + 1,
            "end_col": col_start + (end - start),
            "text": symbol,
            "id": f"{symbol}_{lines_before + 1}_{col_start}",
        }

    def _make_edge(
        self,
        source: str,
        target: str,
        match: re.Match,
        rule: dict,
        current_scope: str,
    ) -> dict:
        """Create an edge dictionary."""
        start = match.start()
        end = match.end()
        text = match.string
        lines_before = text[:start].count('\n')
        line_start = text.rfind('\n', 0, start) + 1
        col_start = start - line_start

        return {
            "kind": rule.get("name_group", "edge"),
            "source": source,
            "target": target,
            "start_line": lines_before + 1,
            "start_col": col_start,
            "end_line": lines_before + 1,
            "end_col": col_start + (end - start),
            "text": match.group(0),
            "id": f"{source}_{target}_{lines_before + 1}_{col_start}",
        }
