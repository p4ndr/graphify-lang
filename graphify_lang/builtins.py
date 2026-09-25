"""Builtins handling for reference resolution (F9, F10).

This module handles builtins_file (one name per line, # comments) plus
builtins_prefixes, applied to @reference captures and regex ref edges,
case-folded when case_insensitive = true.

Applied inside the plugin only; never added to the shared
_LANGUAGE_BUILTIN_GLOBALS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from graphify_lang.queries import QueryRules


class Builtins:
    """Builtins for reference resolution."""

    def __init__(
        self,
        names: set[str],
        prefixes: list[str],
        case_insensitive: bool = False,
    ):
        """Initialize builtins.

        Args:
            names: Set of builtin symbol names
            prefixes: List of builtin prefixes
            case_insensitive: Whether to case-fold comparisons
        """
        self.names = names
        self.prefixes = prefixes
        self.case_insensitive = case_insensitive

    @classmethod
    def from_manifest(cls, manifest_path: Path, manifest: dict[str, Any]) -> Builtins:
        """Build Builtins from a manifest.

        Looks for [extract] builtins_file and builtins_prefixes.
        """
        names: set[str] = set()
        prefixes: list[str] = []
        case_insensitive = manifest.get("case_insensitive", False)

        # Get builtins_file path
        builtins_file = None
        if "extract" in manifest:
            extract_cfg = manifest["extract"]
            if "builtins_file" in extract_cfg:
                builtins_file = Path(extract_cfg["builtins_file"])

        # Load builtins file if present
        if builtins_file:
            if builtins_file.is_absolute():
                builtins_path = builtins_file
            else:
                builtins_path = manifest_path.parent / builtins_file

            if builtins_path.exists():
                try:
                    content = builtins_path.read_text()
                    for line in content.splitlines():
                        line = line.strip()
                        # Skip empty lines and comments
                        if not line or line.startswith("#"):
                            continue
                        if cls._should_fold(case_insensitive):
                            line = line.lower()
                        names.add(line)
                except OSError:
                    pass

        # Get prefixes
        if "extract" in manifest:
            extract_cfg = manifest["extract"]
            if "builtins_prefixes" in extract_cfg:
                px = extract_cfg["builtins_prefixes"]
                if isinstance(px, str):
                    prefixes = [px]
                elif isinstance(px, list):
                    prefixes = list(px)

        # Case-fold prefixes if needed
        if cls._should_fold(case_insensitive):
            prefixes = [p.lower() for p in prefixes]

        return cls(names, prefixes, case_insensitive)

    @staticmethod
    def _should_fold(case_insensitive: bool) -> bool:
        """Check if case-folding is enabled."""
        return case_insensitive

    def is_builtin(self, name: str) -> bool:
        """Check if a name is a builtin."""
        check_name = self._fold(name)
        if check_name in self.names:
            return True
        for prefix in self.prefixes:
            if check_name.startswith(self._fold(prefix)):
                return True
        return False

    def apply_to_results(self, results: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """Apply builtins filtering to extraction results.

        Filters nodes/edges to only include non-builtin references.
        """
        nodes = results.get("nodes", [])
        edges = results.get("edges", [])

        # Filter nodes by builtins
        filtered_nodes = []
        for node in nodes:
            node_kind = node.get("kind", "")
            node_text = node.get("text", "")

            # Check if this is a reference that should be filtered
            if self._is_reference(node_kind):
                if self.is_builtin(node_text):
                    continue

            filtered_nodes.append(node)

        # Filter edges by builtins
        filtered_edges = []
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")

            if self._is_reference(edge.get("kind", "")):
                if self.is_builtin(source) or self.is_builtin(target):
                    continue

            filtered_edges.append(edge)

        return {"nodes": filtered_nodes, "edges": filtered_edges}

    def _is_reference(self, kind: str) -> bool:
        """Check if a node/edge kind represents a reference."""
        reference_kinds = {"reference", "ref", "calls", "depends"}
        return kind.lower() in reference_kinds

    def _fold(self, name: str) -> str:
        """Case-fold a name if enabled."""
        if self.case_insensitive:
            return name.lower()
        return name
