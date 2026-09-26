"""Declarative rules runtime: a manifest dict -> an extract callable.

A fallback and utility layer (plan 04 D7, plan 05 D1): language plugins have
their own extractors, but share this engine's builtins filter (``builtins.py``)
and its sink (``graphify_lang._common.Sink``). A ``post_file`` hook is imported
from ``graphify_lang.*`` or from the ``package`` the caller of ``build`` names
(its own package), never from another module a manifest names (S3-L1). The
threat model: a manifest is data that may sit in a GRAPHIFY_LANG_PATH folder
or a third-party package; the caller of ``build`` is code that already runs,
so it vouches for its own package and nothing else. Two tiers feed one sink:

- query tier (``queries.py``): tree-sitter ``tags.scm`` captures
  ``@definition.<kind>`` / ``@name`` / ``@reference.<relation>``;
- regex tier (``regex_rules.py``): ``[[rule]]`` tables, ctags-optlib scopes.

Emission contract (plan 01 S005, ``.claude/docs/cc-IP000.001.md``; the shared
``graphify_lang._common.Sink``): a file node ``_make_id(str(path))``; every node carries ``label``, ``source_file``,
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

from graphify_lang._common import Sink, _make_id
from graphify_lang.builtins import Builtins
from graphify_lang.queries import QueryRules
from graphify_lang.regex_rules import RegexRules

log = logging.getLogger(__name__)


class Out(Sink):
    """The shared sink plus in-file resolution of reference names."""

    def __init__(self, path: Path, builtins: Builtins) -> None:
        super().__init__(path, builtins)
        self._by_label: dict[str, str] = {}
        self._names: list[tuple[str, str, str, int]] = []

    def node(self, kind: str, label: str, line: int) -> str:
        nid = _make_id(self.stem, label)
        if nid in self._ids:
            nid = _make_id(self.stem, label, str(line))
        self.add(nid, label, kind, line)
        self._by_label.setdefault(self.builtins.fold(label), nid)
        self.edge(self.file_nid, nid, "contains", line)
        return nid

    def ref(self, source: str, name: str, relation: str, line: int) -> None:
        if not self.builtins.is_builtin(name):
            self._names.append((source, name, relation, line))

    def result(self) -> dict:
        # ponytail: in-file resolution only; a cross-file ref needs a plugin resolver.
        for src, name, relation, line in self._names:
            tgt = self._by_label.get(self.builtins.fold(name))
            if tgt:
                self.edge(src, tgt, relation, line)
        return {"nodes": self.nodes, "edges": self.edges}


def _hook(manifest: dict[str, Any], package: str | None = None) -> Callable | None:
    extract_cfg = manifest.get("extract", {})
    spec = extract_cfg.get("post_file") or extract_cfg.get("python", {}).get("post_file")
    if not spec:
        return None
    module, _, fn = spec.partition(":")
    allowed = ("graphify_lang.",) + ((f"{package}.",) if package else ())
    if not (module + ".").startswith(allowed):  # a manifest never names arbitrary code
        raise RuntimeError(f"post_file hook {spec!r} rejected: only modules under "
                           f"{', '.join(p + '*' for p in allowed)} (failed to load)")
    try:
        return getattr(importlib.import_module(module), fn)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(f"post_file hook {spec!r} failed to load: {exc}") from exc


def build(manifest_path: Path, manifest: dict[str, Any], *,
          package: str | None = None) -> tuple[Callable[[Path], dict], None]:
    """Return ``(extract, resolver)`` for a parsed manifest; the resolver is always None.
    ``package``: the caller's own top-level package, whose modules a
    ``post_file`` hook may also name (``__package__`` of the calling plugin)."""
    try:
        queries = QueryRules.from_manifest(manifest_path, manifest)
        regex = RegexRules.from_manifest(manifest_path, manifest)
        builtins = Builtins.from_manifest(manifest_path, manifest)
        hook = _hook(manifest, package)
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
