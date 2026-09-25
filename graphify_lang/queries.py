"""Query tier: tree-sitter ``tags.scm`` rules (S005 F7).

Captures: ``@definition.<node_kind>`` (the definition's span), ``@name`` (its
label), ``@reference.<relation>`` (a use, labelled by the ``@name`` in the
same match). Text predicates (``#eq?``, ``#match?``, ``#any-of?`` and their
``#not-`` forms) are cut from the query before it compiles and evaluated
here: py-tree-sitter 0.23 evaluates ``#not-match?`` inverted and ignores
``#any-of?``, measured against the declared floor.

Fails loudly: a missing grammar, an unimportable module, a missing query file
or a query that does not compile raises at build time, which
``rules.build`` turns into an ``error`` on every extract call.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

from tree_sitter import Language, Parser, Query

try:  # py-tree-sitter 0.25
    from tree_sitter import QueryCursor

    def _matches(query: Query, node: Any) -> list:
        return QueryCursor(query).matches(node)
except ImportError:  # 0.23 / 0.24
    def _matches(query: Query, node: Any) -> list:
        return query.matches(node)


_PREDICATE = re.compile(
    r'\(\s*#(not-)?(eq|match|any-of)\?((?:\s+(?:@[\w.-]+|"(?:[^"\\]|\\.)*"))+)\s*\)')
_ARG = re.compile(r'@[\w.-]+|"(?:[^"\\]|\\.)*"')

Predicate = tuple[bool, str, str, list[str]]           # (negated, op, capture, args)


def _compile(language: Language, text: str) -> tuple[Query, list[list[Predicate]]]:
    """Compile ``text`` with its text predicates blanked; return them per pattern."""
    found = [(m.start(), bool(m.group(1)), m.group(2), [a if a[0] == "@" else json.loads(a)
              for a in _ARG.findall(m.group(3))]) for m in _PREDICATE.finditer(text)]
    query = Query(language, _PREDICATE.sub(lambda m: " " * len(m.group(0)), text))
    starts = [query.start_byte_for_pattern(i) for i in range(query.pattern_count)]
    per_pattern: list[list[Predicate]] = [[] for _ in starts]
    for at, neg, op, args in found:
        i = max(j for j, start in enumerate(starts) if start <= at)
        per_pattern[i].append((neg, op, args[0][1:], args[1:]))
    return query, per_pattern


def _text(node: Any) -> str:
    return node.text.decode("utf-8", errors="replace")


def _holds(preds: list[Predicate], caps: dict[str, list]) -> bool:
    for neg, op, cap, args in preds:
        for node in caps.get(cap, []):
            text = _text(node)
            vals = [_text(caps[a[1:]][0]) if a.startswith("@") and caps.get(a[1:]) else a
                    for a in args]
            if op == "eq":
                ok = text == vals[0]
            elif op == "match":
                ok = re.search(vals[0], text) is not None
            else:
                ok = text in vals
            if ok == neg:
                return False
    return True


class QueryRules:
    def __init__(self, language: Language, queries: list[tuple[Query, list[list[Predicate]]]]) -> None:
        self.parser = Parser(language)
        self.queries = queries

    @classmethod
    def from_manifest(cls, manifest_path: Path, manifest: dict[str, Any]) -> QueryRules | None:
        files = manifest.get("extract", {}).get("queries")
        if not files:
            return None
        grammar = manifest.get("grammar", {})
        module_name = grammar.get("module")
        if not module_name:
            raise RuntimeError("[extract] queries needs [grammar] module (failed to load)")
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise RuntimeError(f"grammar {module_name} not installed: {exc}") from exc
        fn_name = grammar.get("language_fn", "language").removesuffix("()")
        try:
            language = Language(getattr(module, fn_name)())
        except Exception as exc:
            raise RuntimeError(f"grammar {module_name}.{fn_name} failed to load: {exc}") from exc
        queries = []
        for name in [files] if isinstance(files, str) else files:
            path = manifest_path.parent / name
            try:
                queries.append(_compile(language, path.read_text(encoding="utf-8")))
            except Exception as exc:
                raise RuntimeError(f"query {path} failed to load: {exc}") from exc
        return cls(language, queries)

    def apply(self, source: bytes, out: Any) -> Any:
        """Emit definitions and reference edges into ``out``; return the tree."""
        tree = self.parser.parse(source)
        scopes: list[tuple[int, int, str]] = []            # (start, end, node id)
        refs: list[tuple[int, str, str, int]] = []         # (byte, name, relation, line)
        for query, preds in self.queries:
            for i, caps in _matches(query, tree.root_node):
                if not _holds(preds[i], caps):
                    continue
                name = caps.get("name", [None])[0]
                for cap, nodes in caps.items():
                    kind, _, sub = cap.partition(".")
                    if kind not in ("definition", "reference") or not sub:
                        continue
                    span = nodes[0]
                    label = (name or span).text.decode("utf-8", errors="replace").strip()
                    line = span.start_point[0] + 1
                    if kind == "definition":
                        scopes.append((span.start_byte, span.end_byte, out.node(sub, label, line)))
                    else:
                        refs.append((span.start_byte, label, sub, line))
        for byte, label, relation, line in refs:
            inner = [s for s in scopes if s[0] <= byte < s[1]]
            src = min(inner, key=lambda s: s[1] - s[0])[2] if inner else out.file_nid
            out.ref(src, label, relation, line)
        return tree
