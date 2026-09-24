"""Query rules for tree-sitter tag queries (F7).

This module implements query rules that extract nodes and edges
using tree-sitter tag queries (tags.scm format).

Predicates (#eq?, #match?, #not-match?, #any-of?) are implemented in Python
since the C library does not run them.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

from tree_sitter import Language, Parser, Query, QueryCursor


class QueryRules:
    """Query rules extracted from a manifest."""

    def __init__(
        self,
        queries: list[str],
        captures: dict[str, str],
        predicates: dict[str, list[tuple[str, str]]],
    ):
        """Initialize query rules."""
        self.queries = queries
        self.captures = captures
        self.predicates = predicates
        self._compiled_queries: list[Query] = []
        # Grammar is set by the registry - we use a placeholder here
        self._grammar: str | None = None

    @staticmethod
    def _split_queries(content: str) -> list[str]:
        """Split tags.scm content into individual query blocks."""
        lines = content.split("\n")
        queries: list[str] = []
        current_query: list[str] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                i += 1
                continue

            current_query.append(line)

            ends_query = stripped.endswith(")") or bool(
                re.search(r"[\)\]]\s+@\w+", stripped)
            )

            if ends_query:
                query_text = "\n".join(current_query)
                queries.append(query_text)
                current_query = []
                i += 1
                continue

            # Predicates continue the query - don't clear current_query
            is_predicate = stripped.startswith("#")
            if is_predicate:
                i += 1
                continue

            i += 1

        if current_query:
            queries.append("\n".join(current_query))

        return queries

    @classmethod
    def from_manifest(
        cls, manifest_path: Path, manifest: dict[str, Any]
    ) -> QueryRules:
        """Build QueryRules from a manifest.

        Looks for [extract.queries] section and loads tags.scm files.
        """
        queries: list[str] = []
        captures: dict[str, str] = {}
        predicates: dict[str, list[tuple[str, str]]] = {}

        extract = manifest.get("extract", {})
        if "queries" in extract:
            queries_cfg = extract["queries"]
            if isinstance(queries_cfg, str):
                queries_path = manifest_path.parent / queries_cfg
                if queries_path.exists():
                    content = queries_path.read_text()
                    queries = cls._split_queries(content)
            elif isinstance(queries_cfg, list):
                for qf in queries_cfg:
                    queries_path = manifest_path.parent / qf
                    if queries_path.exists():
                        content = queries_path.read_text()
                        queries.extend(cls._split_queries(content))

        for q in queries:
            capture_pattern = r"@([a-zA-Z_][a-zA-Z0-9_\-.]+)"
            for match in re.finditer(capture_pattern, q):
                name = match.group(1)
                if "." in name:
                    cap_name, kind = name.split(".", 1)
                    captures[cap_name] = kind

        predicate_pattern = r'#(eq|match|not-match|any-of)\?\s+@([a-zA-Z_][a-zA-Z0-9_.-]*)\s+("([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\')'
        for q in queries:
            for match in re.finditer(predicate_pattern, q, re.MULTILINE):
                pred_type = match.group(1)
                cap_name = match.group(2)
                value = match.group(3).strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                predicates.setdefault(cap_name, []).append((pred_type, value))

        return cls(queries, captures, predicates)

    def apply(self, source: bytes, source_file: str = "") -> dict[str, list[dict]]:
        """Apply query rules to source code."""
        nodes: list[dict] = []
        edges: list[dict] = []

        if not self.queries:
            return {"nodes": nodes, "edges": edges}

        language = self._load_language()
        if language is None:
            return {"nodes": nodes, "edges": edges}

        parser = Parser(language)
        tree = parser.parse(source)

        if not self._compiled_queries:
            for query_text in self.queries:
                try:
                    query = Query(language, query_text)
                    self._compiled_queries.append(query)
                except Exception:
                    pass

        for query in self._compiled_queries:
            query_cursor = QueryCursor(query)
            captures = query_cursor.captures(tree.root_node)

            for cap_name, node_list in captures.items():
                for node in node_list:
                    # Extract base capture name (before the dot)
                    base_cap_name = cap_name.split('.')[0] if '.' in cap_name else cap_name
                    node_kind = self.captures.get(base_cap_name, node.type)

                    node_data = self._node_from_tree_sitter(node, node_kind, source, source_file)
                    node_data["capture"] = cap_name

                    # Apply predicates
                    if cap_name in self.predicates:
                        if not self._apply_predicates(
                            [node], source, cap_name
                        ):
                            continue

                    nodes.append(node_data)

        return {"nodes": nodes, "edges": edges}

    def _load_language(self) -> Language | None:
        """Load the tree-sitter language from the grammar name."""
        if not self._grammar:
            return None

        try:
            if callable(self._grammar):
                return Language(self._grammar())
            elif isinstance(self._grammar, str):
                try:
                    mod = importlib.import_module(self._grammar)
                    language_fn = getattr(mod, "language", None)
                    if language_fn and callable(language_fn):
                        return Language(language_fn())
                    else:
                        return Language(mod)
                except Exception:
                    return None
            elif isinstance(self._grammar, dict):
                # Handle dict format: {'kind': 'tree-sitter', 'module': '...', 'language_fn': '...', ...}
                if self._grammar.get("kind") == "tree-sitter":
                    module_name = self._grammar.get("module")
                    if module_name:
                        try:
                            mod = importlib.import_module(module_name)
                            language_fn = getattr(mod, "language", None)
                            if language_fn and callable(language_fn):
                                return Language(language_fn())
                            else:
                                return Language(mod)
                        except Exception:
                            return None
            return None
        except Exception:
            return None

    def _apply_predicates(
        self, nodes: list, source: bytes, cap_name: str
    ) -> list:
        """Filter nodes by predicate rules."""
        result = []
        for node in nodes:
            text = self._node_text(node, source)
            for pred_type, value in self.predicates.get(cap_name, []):
                if pred_type == "eq":
                    if text != value:
                        break
                elif pred_type == "match":
                    if not re.match(value, text):
                        break
                elif pred_type == "not-match":
                    if re.match(value, text):
                        break
                elif pred_type == "any-of":
                    if text not in value:
                        break
            else:
                result.append(node)
        return result

    def _node_text(self, node: Any, source: bytes) -> str:
        """Get the text of a node."""
        start = node.start_byte
        end = node.end_byte
        return source[start:end].decode("utf-8")

    def _node_from_tree_sitter(self, node: Any, kind: str, source: bytes, source_file: str = "") -> dict:
        """Convert a tree-sitter node to our node format."""
        text = source[node.start_byte:node.end_byte].decode("utf-8")
        # Generate id from source_file and text
        from graphify.extractors.base import _file_stem, _make_id
        from pathlib import Path
        stem = _file_stem(Path(source_file)) if source_file else ""
        label = text.strip()
        if stem:
            node_id = _make_id(stem, label.replace("\\", "/"))
        else:
            node_id = _make_id(label.replace("\\", "/"))
        return {
            "id": node_id,
            "label": label,
            "text": text,
            "node_kind": kind,
            "start_line": node.start_point[0] + 1,
            "start_col": node.start_point[1],
            "end_line": node.end_point[0] + 1,
            "end_col": node.end_point[1],
            "source_file": source_file,
            "capture": "",
            "file_type": "code",
        }

def build_extractor(manifest_path: Path, manifest: dict[str, Any]) -> QueryRules:
    """Build a QueryRules instance from a manifest."""
    return QueryRules.from_manifest(manifest_path, manifest)
