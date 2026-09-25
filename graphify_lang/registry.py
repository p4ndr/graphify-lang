"""Registry for language packages discovered via entry points or namespace."""

from __future__ import annotations

import codecs
import functools
import logging
import os
import re
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from graphify_lang.manifest import LanguageManifest

_LOG = logging.getLogger(__name__)

# Environment variable to disable the registry entirely
_DISABLE_VAR = "GRAPHIFY_LANG_DISABLE"

# Environment variable for additional search paths
_PATH_VAR = "GRAPHIFY_LANG_PATH"


@dataclass
class _RegistryState:
    """Internal registry state, cached per process."""

    enabled: bool = True
    search_paths: list[Path] = field(default_factory=list)
    manifests: dict[str, LanguageManifest] = field(default_factory=dict)
    suffix_to_manifest: dict[str, LanguageManifest] = field(default_factory=dict)
    warned_builtins: set[str] = field(default_factory=set)
    tie_warned: set[str] = field(default_factory=set)


# Process-wide cache
_STATE: _RegistryState | None = None


def _init_state() -> _RegistryState:
    """Initialize or return the cached registry state."""
    global _STATE
    if _STATE is not None:
        return _STATE

    # Check environment
    disabled = os.environ.get(_DISABLE_VAR, "").strip().lower()
    enabled = disabled not in ("1", "true", "yes", "on")

    # Build search paths
    search_paths: list[Path] = []
    if enabled:
        # Entry points first (importlib.metadata)
        try:
            import importlib.metadata as importlib_metadata
        except ImportError:
            import importlib_metadata

        try:
            eps = importlib_metadata.entry_points(group="graphify_lang.plugins")
        except TypeError:
            eps = importlib_metadata.entry_points().get("graphify_lang.plugins", [])

        for ep in eps:
            try:
                loader = ep.load
            except AttributeError:
                continue
            try:
                result = loader()
            except Exception as exc:
                _LOG.warning("failed to load entry point %s: %s", ep.name, exc)
                continue
            _process_loader_result(ep.name, result)

        # Also try graphify_lang_plugins (underscore variant)
        try:
            eps2 = importlib_metadata.entry_points(group="graphify_lang_plugins")
        except TypeError:
            eps2 = importlib_metadata.entry_points().get("graphify_lang_plugins", [])

        for ep in eps2:
            try:
                loader = ep.load
            except AttributeError:
                continue
            try:
                result = loader()
            except Exception as exc:
                _LOG.warning("failed to load entry point %s: %s", ep.name, exc)
                continue
            _process_loader_result(ep.name, result)

        # Then GRAPHIFY_LANG_PATH
        path_env = os.environ.get(_PATH_VAR, "")
        if path_env:
            for p in path_env.split(os.pathsep):
                if p:
                    search_paths.append(Path(p).resolve())

    # Only create new state if _STATE is still None
    # This allows _register_manifest to set _STATE first
    if _STATE is None:
        _STATE = _RegistryState(
            enabled=enabled, search_paths=search_paths
        )
    return _STATE


def _process_loader_result(name: str, result: Any) -> None:
    """Process a loader result into a manifest."""
    if result is None:
        return
    # Call result if it's a callable (like _get_manifest returning a function)
    if callable(result):
        result = result()
    if isinstance(result, LanguageManifest):
        _register_manifest(result)
    elif isinstance(result, (list, tuple)):
        for item in result:
            _process_loader_result(name, item)
    # Ignore other types silently - the loader may return metadata


def _register_manifest(manifest: LanguageManifest) -> None:
    """Register a manifest into the registry."""
    global _STATE
    state = _STATE if _STATE is not None else _RegistryState(enabled=True, search_paths=[])
    
    if not manifest.name:
        _LOG.warning("manifest with empty name ignored")
        return

    state.manifests[manifest.name] = manifest
    for suffix in manifest.suffixes:
        # First claimant is the suffix's manifest for metadata (extras). Who
        # extracts a shared suffix is decided by dispatch_table (plan 04 §3.1).
        state.suffix_to_manifest.setdefault(suffix, manifest)

    _register_resolver(manifest.resolver)

    # Update _STATE if it was None
    if _STATE is None:
        _STATE = state


def _register_resolver(resolver: Any) -> None:
    """Hand a manifest's cross-file resolver to graphify, once per process.

    ``graphify.resolver_registry`` is process-global and outlives ``reset()``,
    so the same resolver name is never registered twice.
    """
    try:
        from graphify.resolver_registry import (
            LanguageResolver,
            register,
            registered_resolvers,
        )
    except ImportError:
        return
    if not isinstance(resolver, LanguageResolver):
        return
    if resolver.name not in {r.name for r in registered_resolvers()}:
        register(resolver)


def get_manifest(name: str) -> LanguageManifest | None:
    """Return the manifest for a language by name, or None if not found."""
    state = _init_state()
    return state.manifests.get(name)


def get_manifest_for_suffix(suffix: str) -> LanguageManifest | None:
    """Return the manifest for a file suffix, or None if not found."""
    state = _init_state()
    return state.suffix_to_manifest.get(suffix)


def registered_names() -> list[str]:
    """Return the names of all registered languages, in registration order."""
    state = _init_state()
    return list(state.manifests.keys())


def registered_suffixes() -> set[str]:
    """Suffixes a plugin claims whole (no ``[match]``): these are code by suffix."""
    return {s for m in _languages() if not m.has_match for s in m.suffixes}


def match_suffixes() -> set[str]:
    """Suffixes claimed only per path (``[match]``): code only via ``claims_file``."""
    return {s for m in _languages() if m.has_match for s in m.suffixes} - registered_suffixes()


def claimants(suffix: str) -> list[LanguageManifest]:
    """Plugins that list ``suffix``, in registration order."""
    return [m for m in _languages() if suffix in m.suffixes]


def _languages() -> list[LanguageManifest]:
    return [m for m in _init_state().manifests.values() if m.kind == "language"]


# --- content sniffing (plan 04 §3.1-3.2) ------------------------------------

_EMPTY = {"nodes": [], "edges": []}


@functools.lru_cache(maxsize=None)
def _glob_re(glob: str) -> re.Pattern[str]:
    """Glob on the repo-relative path. The path may be absolute, so the glob is
    anchored at any ``/`` boundary: ``rules/*.yml`` matches ``/r/rules/a.yml``.
    """
    # ponytail: a parent dir outside the repo can satisfy the anchor; pass the
    # scan root down if that ever mis-claims a file.
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:[^/]*/)*")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        else:
            out.append({"*": "[^/]*", "?": "[^/]"}.get(glob[i]) or re.escape(glob[i]))
            i += 1
    return re.compile("(?:^|/)" + "".join(out) + "$")


def _path_matches(m: LanguageManifest, path: Path) -> bool:
    if not m.has_match:
        return True
    if path.name in m.match_filenames:
        return True
    posix = path.as_posix()
    return any(_glob_re(g).search(posix) for g in m.match_globs)


def _read_head(path: Path, n: int) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read(n)
    except OSError:
        return b""


def _sniff_score(m: LanguageManifest, path: Path, head: Callable[[int], bytes]) -> float | None:
    """Score of ``m`` for ``path``, or None when ``m`` does not pass."""
    if not _path_matches(m, path):
        return None
    if m.sniff is None:
        return 0
    raw = head(m.sniff.head_bytes)
    if not raw or b"\x00" in raw:  # empty or binary: never code by content
        return None
    text = raw.removeprefix(codecs.BOM_UTF8).decode("utf-8", errors="replace")
    score = m.sniff.score(text)
    return score if score >= m.sniff.min_score else None


def _head_reader(path: Path, size: int) -> Callable[[int], bytes]:
    """Read the head of ``path`` at most once, sliced per plugin."""
    cache: list[bytes] = []

    def head(n: int) -> bytes:
        if not cache:
            cache.append(_read_head(path, size))
        return cache[0][:n]
    return head


def _pick(suffix: str, candidates: list[LanguageManifest], path: Path) -> LanguageManifest | None:
    """Best passing plugin: highest score, then priority, then registration order."""
    size = max((m.sniff.head_bytes for m in candidates if m.sniff), default=0)
    head = _head_reader(path, size)
    best, best_key, tie = None, None, False
    for m in candidates:
        score = _sniff_score(m, path, head)
        if score is None:
            continue
        key = (score, m.priority)
        if best_key is None or key > best_key:
            best, best_key, tie = m, key, False
        elif key == best_key:
            tie = True
    state = _init_state()
    if tie and suffix not in state.tie_warned:
        state.tie_warned.add(suffix)
        _LOG.warning("sniff tie on %s (%s): %s wins by registration order",
                     suffix, path.name, best.name)
    return best


def _router(suffix: str, candidates: list[LanguageManifest],
            fallback: Callable[[Path], dict] | None) -> Callable[[Path], dict]:
    def route(path: Path) -> dict:
        path = Path(path)
        chosen = _pick(suffix, candidates, path)
        if chosen is not None:
            return chosen.extract(path)
        return fallback(path) if fallback is not None else dict(_EMPTY)
    route.__name__ = route.__qualname__ = f"sniff_router[{suffix}]"
    return route


def dispatch_table(builtins: Mapping[str, Callable[[Path], dict]]) -> dict[str, Callable[[Path], dict]]:
    """Extractor per plugin-claimed suffix, given the core table before plugins.

    Per suffix: an ``overrides`` plugin, else the built-in, else the first plugin
    with no sniff/match is the fallback. Plugins with a sniff or a ``[match]``
    compete through a router in front of that fallback (plan 04 §3.1, D2).
    """
    table: dict[str, Callable[[Path], dict]] = {}
    for suffix in sorted({s for m in _languages() for s in m.suffixes}):
        claim = claimants(suffix)
        overriding = [m for m in claim if suffix in m.overrides]
        conditional = [m for m in claim if m not in overriding and (m.sniff or m.has_match)]
        plain = [m for m in claim if m not in overriding and m not in conditional]
        builtin = builtins.get(suffix)
        if overriding:
            fallback = overriding[0].extract
        elif builtin is not None:
            fallback = builtin
        else:
            fallback = plain[0].extract if plain else None
        ignored = overriding[1:] + (plain if overriding or builtin is not None else plain[1:])
        for m in ignored:
            _LOG.warning("suffix %s: %s has no [sniff] and does not win (%s kept)",
                         suffix, m.name, getattr(fallback, "__name__", fallback))
        if conditional:
            table[suffix] = _router(suffix, conditional, fallback)
        elif fallback is not None and fallback is not builtin:
            table[suffix] = fallback
    augmenters = [m for m in _init_state().manifests.values() if m.kind == "augment"]
    for suffix in sorted({s for m in augmenters for s in m.augments}):
        inner = table.get(suffix) or builtins.get(suffix)
        on_suffix = [m for m in augmenters if suffix in m.augments and m.augment]
        if not on_suffix:
            _LOG.warning("augment on %s skipped: no augment()", suffix)
            continue
        if inner is None:
            # A file routed by name before _DISPATCH (a package manifest) is
            # augmented through augment_extractor; nothing to wrap here.
            _LOG.debug("augment on %s: no suffix extractor, per-path only", suffix)
            continue
        table[suffix] = _augmented(suffix, inner, on_suffix)
    return table


# --- augment kind (plan 04 §3.3, D5) ------------------------------------------

def _augmented(suffix: str, inner: Callable[[Path], dict],
               augmenters: list[LanguageManifest]) -> Callable[[Path], dict]:
    """Run ``inner`` (built-in or router), then each augment whose match passes."""
    size = max((m.sniff.head_bytes for m in augmenters if m.sniff), default=0)

    def augmented(path: Path) -> dict:
        path = Path(path)
        result = inner(path)
        head = _head_reader(path, size)
        for m in augmenters:
            if _sniff_score(m, path, head) is not None:
                result = _merge(m, result, m.augment(path, result) or {})
        return result
    augmented.__name__ = augmented.__qualname__ = f"augmented[{suffix}]"
    return augmented


def augment_extractor(path: Path, inner: Callable[[Path], dict]) -> Callable[[Path], dict]:
    """``inner`` wrapped by the augments that claim ``path``, else ``inner`` itself.

    For an extractor that core picks by file name before ``_DISPATCH`` (package
    manifests), so the suffix wrapper in ``dispatch_table`` never sees the file.
    """
    suffix = path.suffix.lower()
    on_suffix = [m for m in _init_state().manifests.values()
                 if m.kind == "augment" and m.augment and suffix in m.augments]
    size = max((m.sniff.head_bytes for m in on_suffix if m.sniff), default=0)
    head = _head_reader(path, size)
    claiming = [m for m in on_suffix if _sniff_score(m, path, head) is not None]
    return _augmented(suffix, inner, claiming) if claiming else inner


def _merge(m: LanguageManifest, base: dict, extra: dict) -> dict:
    """Add an augment's nodes, edges and attrs; never delete, rename or overwrite."""
    prefix = re.sub(r"\W+", "_", m.name).lower() + "_"
    nodes = list(base.get("nodes", []))
    ids = {n.get("id") for n in nodes}
    for node in extra.get("nodes", []):
        nid = node.get("id", "")
        if nid in ids or not nid.startswith(prefix):
            _LOG.info("augment %s: node %r dropped (existing id or no %s prefix)",
                      m.name, nid, prefix)
            continue
        nodes.append(node)
        ids.add(nid)
    attrs = extra.get("attrs") or {}
    for i, node in enumerate(nodes):
        add = attrs.get(node.get("id"))
        if not add:
            continue
        clash = sorted(k for k in add if k in node)
        for key in clash:
            _LOG.info("augment %s: attr %s on %s kept (not overwritten)", m.name, key, node["id"])
        nodes[i] = {**node, **{k: v for k, v in add.items() if k not in node}}
    edges = list(base.get("edges", [])) + list(extra.get("edges", []))
    return {**base, "nodes": nodes, "edges": edges}


def claims_file(path: Path) -> bool:
    """True when a ``[match]`` plugin's glob and sniff both pass for ``path`` (D3)."""
    suffix = path.suffix.lower()
    if suffix not in match_suffixes():
        return False
    candidates = [m for m in claimants(suffix) if m.has_match]
    size = max((m.sniff.head_bytes for m in candidates if m.sniff), default=0)
    head = _head_reader(path, size)
    return any(_sniff_score(m, path, head) is not None for m in candidates)


def iter_manifests() -> Iterator[LanguageManifest]:
    """Iterate over all registered manifests."""
    state = _init_state()
    return iter(list(state.manifests.values()))


def reset() -> None:
    """Clear the registry cache so discovery runs again."""
    global _STATE
    _STATE = None
