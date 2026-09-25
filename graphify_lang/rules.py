"""Declarative rules runtime: a manifest dict -> an extract callable.

A fallback and utility layer (plan 04 D7): language plugins have their own
extractors and may call this; none depends on it. Two tiers feed one sink:

- query tier (``queries.py``): tree-sitter ``tags.scm`` captures
  ``@definition.<kind>`` / ``@name`` / ``@reference.<relation>``;
- regex tier (``regex_rules.py``): ``[[rule]]`` tables, ctags-optlib scopes.

Emission contract (plan 01 S005, ``.claude/docs/cc-IP000.001.md``): a file
node from ``_file_stem``; every node carries ``label``, ``source_file``,
``file_type = "code"`` and ``node_kind``; symbol ids ``_make_id(stem, label)``
with the definition line appended on a clash (the ``extract_markdown``
recipe); a ``contains`` edge per symbol; reference edges resolved within the
file after the builtins filter. A configuration fault never yields a silent
empty result: every call returns ``error`` carrying ``not installed`` or
``failed to load`` so the core #1745 warning fires.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any, Callable

from graphify.extractors.base import _file_stem, _make_id
from graphify_lang.builtins import Builtins
from graphify_lang.queries import QueryRules
from graphify_lang.regex_rules import RegexRules

log = logging.getLogger(__name__)


class Out:
    """Node / edge sink for one file."""

    def __init__(self, path: Path, builtins: Builtins) -> None:
        self.sf = str(path)
        self.stem = _make_id(_file_stem(path))
        self.builtins = builtins
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._ids: set[str] = set()
        self._by_label: dict[str, str] = {}
        self._refs: list[tuple[str, str, str, int]] = []
        self._edge_keys: set[tuple[str, str, str]] = set()
        self.file_nid = self._add(self.stem, path.name, "file", 1)

    def _add(self, nid: str, label: str, kind: str, line: int) -> str:
        self._ids.add(nid)
        self.nodes.append({"id": nid, "label": label, "file_type": "code", "node_kind": kind,
                           "source_file": self.sf, "source_location": f"L{line}"})
        return nid

    def node(self, kind: str, label: str, line: int) -> str:
        nid = _make_id(self.stem, label)
        if nid in self._ids:
            nid = _make_id(self.stem, label, str(line))
        self._add(nid, label, kind, line)
        self._by_label.setdefault(self.builtins.fold(label), nid)
        self.edge(self.file_nid, nid, "contains", line)
        return nid

    def ref(self, source: str, name: str, relation: str, line: int) -> None:
        if not self.builtins.is_builtin(name):
            self._refs.append((source, name, relation, line))

    def edge(self, src: str, tgt: str, relation: str, line: int) -> None:
        if (src, tgt, relation) in self._edge_keys:
            return
        self._edge_keys.add((src, tgt, relation))
        self.edges.append({"source": src, "target": tgt, "relation": relation,
                           "confidence": "EXTRACTED", "source_file": self.sf,
                           "source_location": f"L{line}", "weight": 1.0})

    def result(self) -> dict:
        # ponytail: in-file resolution only; a cross-file ref needs a plugin resolver.
        for src, name, relation, line in self._refs:
            tgt = self._by_label.get(self.builtins.fold(name))
            if tgt:
                self.edge(src, tgt, relation, line)
        return {"nodes": self.nodes, "edges": self.edges}


def _hook(manifest: dict[str, Any]) -> Callable | None:
    extract_cfg = manifest.get("extract", {})
    spec = extract_cfg.get("post_file") or extract_cfg.get("python", {}).get("post_file")
    if not spec:
        return None
    module, _, fn = spec.partition(":")
    try:
        return getattr(importlib.import_module(module), fn)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(f"post_file hook {spec!r} failed to load: {exc}") from exc


def build(manifest_path: Path, manifest: dict[str, Any]) -> tuple[Callable[[Path], dict], None]:
    """Return ``(extract, resolver)`` for a parsed manifest; the resolver is always None."""
    try:
        queries = QueryRules.from_manifest(manifest_path, manifest)
        regex = RegexRules.from_manifest(manifest_path, manifest)
        builtins = Builtins.from_manifest(manifest_path, manifest)
        hook = _hook(manifest)
    except Exception as exc:  # every manifest fault ends here, loudly
        reason = f"graphify_lang.rules: {manifest_path}: {exc}"
        if "not installed" not in reason:
            reason = reason if "failed to load" in reason else f"{reason} (failed to load)"
        log.warning(reason)

        def failed(path: Path) -> dict:
            return {"nodes": [], "edges": [], "error": reason}

        return failed, None

    def extract(path: Path) -> dict:
        try:
            source = path.read_bytes()
        except OSError as exc:
            return {"nodes": [], "edges": [], "error": f"failed to read {path}: {exc}"}
        out = Out(path, builtins)
        tree = queries.apply(source, out) if queries else None
        if regex:
            regex.apply(source.decode("utf-8", errors="replace"), path, out)
        result = out.result()
        if hook:
            got = hook(path, tree, result["nodes"], result["edges"], manifest)
            if isinstance(got, dict):
                result = {**result, **got}
        return result

    return extract, None
