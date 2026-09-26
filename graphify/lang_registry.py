"""Registry integration layer — merges language extensions from graphify_lang."""
from __future__ import annotations

import functools
import logging
from typing import Callable

_LOG = logging.getLogger(__name__)

# Global state
_REGISTRY_AVAILABLE = False
_REGISTRY_SUFFIXES: set[str] = set()
# Suffixes whose edit triggers a graph rebuild: the code suffixes above plus
# every manifest's ``hook_suffixes`` (a ``[match]`` data plugin claims .yml or
# .xml per path, so its suffix is never a code suffix).
_HOOK_SUFFIXES: set[str] = set()


def _apply_registry() -> None:
    """Import and merge registry suffixes into core tables.
    
    Each call site wraps this in try/except so one failure doesn't break graphify.
    """
    global _REGISTRY_AVAILABLE, _REGISTRY_SUFFIXES, _HOOK_SUFFIXES
    
    try:
        from graphify_lang import registry as lang_registry
    except ImportError:
        _LOG.debug("graphify_lang not installed, skipping registry integration")
        _REGISTRY_AVAILABLE = False
        return
    
    try:
        # Get suffixes from registry
        registry_suffixes = lang_registry.registered_suffixes()
        
        # Merge into our set (casefolded for robustness)
        for suffix in registry_suffixes:
            _REGISTRY_SUFFIXES.add(suffix)
            # Also register uppercase variant for case-insensitive filesystems
            _REGISTRY_SUFFIXES.add(suffix.upper())
        for suffix in lang_registry.hook_suffixes():
            _HOOK_SUFFIXES.update((suffix, suffix.upper()))
        _HOOK_SUFFIXES |= _REGISTRY_SUFFIXES

        _REGISTRY_AVAILABLE = True
        _LOG.debug("registry integration active, suffixes: %s", sorted(_REGISTRY_SUFFIXES))
    except Exception as exc:
        _LOG.warning("registry merge failed: %s", exc)
        _REGISTRY_AVAILABLE = False
    try:
        _namespace_ast_cache(lang_registry)
    except Exception as exc:
        _LOG.warning("plugin-set cache namespace failed: %s", exc)


# graphify.cache._EXTRACTOR_VERSION before a plugin fingerprint was appended.
_BASE_CACHE_VERSION: str | None = None


def _namespace_ast_cache(lang_registry) -> None:
    """Give the active plugin set its own AST cache namespace (cc-CR000.001 M2,
    E1). The extractor chosen for a file depends on the plugin set
    (``GRAPHIFY_LANG_DISABLE``, a plugin installed, plugin code changed), but
    the cache key is the file's bytes and the graphify version, so the
    namespace ``v<version>-s<schema>`` gets ``-lang<fingerprint>`` appended at
    run time (no edit to ``cache.py``). Entries written before this, including
    pre-stage-3 results whose refs have no ``node``, are never read again.
    """
    global _BASE_CACHE_VERSION
    import graphify.cache as cache

    if _BASE_CACHE_VERSION is None:
        _BASE_CACHE_VERSION = cache._EXTRACTOR_VERSION
    names = tuple(sorted(m.name for m in lang_registry.iter_manifests()))
    modules = tuple(sorted({getattr(m.augment or m.extract, "__module__", "") or ""
                            for m in lang_registry.iter_manifests()}))
    folders = tuple(str(p) for p in lang_registry.search_paths())
    cache._EXTRACTOR_VERSION = (f"{_BASE_CACHE_VERSION}-lang"
                                f"{_fingerprint(names, modules, folders)}")


@functools.lru_cache(maxsize=8)
def _fingerprint(names: tuple[str, ...], modules: tuple[str, ...],
                 folders: tuple[str, ...] = ()) -> str:
    """Hash of the manifest names, each plugin distribution's version, and the
    ``.py`` / ``.toml`` files of ``graphify_lang``, every plugin package and
    every ``GRAPHIFY_LANG_PATH`` folder (cc-CR000.001 M5)."""
    import hashlib
    import sys
    from importlib import metadata
    from pathlib import Path

    import graphify_lang

    h = hashlib.sha256("\0".join(names).encode())
    dirs = {Path(graphify_lang.__file__).parent} | {Path(f) for f in folders}
    for name in modules:
        mod = sys.modules.get(name)
        if getattr(mod, "__file__", None):
            dirs.add(Path(mod.__file__).parent)
    tops = sorted({m.split(".")[0] for m in modules if m} | {"graphify_lang"})
    dists = metadata.packages_distributions()
    for dist in sorted({d for top in tops for d in dists.get(top, ())}):
        h.update(f"\0{dist}={metadata.version(dist)}".encode())
    for d in sorted(dirs):
        for f in sorted(d.rglob("*")):
            if f.suffix in (".py", ".toml") and f.is_file():
                h.update(b"\0" + f.relative_to(d).as_posix().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:12]


def get_registry_suffixes() -> set[str]:
    """Suffixes whose edit should rebuild the graph (including case variants).

    The code suffixes plus every manifest's ``hook_suffixes``. ``graphify.cli``
    merges this into ``_HOOK_SOURCE_EXTS``; ``detect`` uses ``get_code_suffixes``.
    """
    return _HOOK_SUFFIXES.copy()


def get_code_suffixes() -> set[str]:
    """Suffixes a plugin claims whole: code by suffix (including case variants)."""
    return _REGISTRY_SUFFIXES.copy()


def get_registry_manifest(suffix: str) -> object | None:
    """Return the manifest for a suffix, or None if not found in registry."""
    if not _REGISTRY_AVAILABLE:
        return None
    try:
        from graphify_lang import registry as lang_registry
        return lang_registry.get_manifest_for_suffix(suffix)
    except Exception as exc:
        _LOG.warning("registry manifest lookup failed for %s: %s", suffix, exc)
        return None
# The core extractor table as it was before any plugin changed it: the
# built-in claimant of each suffix for the sniff router (plan 04 §3.1).
_BUILTIN_DISPATCH: dict | None = None


def apply_dispatch() -> None:
    """Apply registry extractors and sniff routers to _DISPATCH in graphify.extract."""
    global _REGISTRY_AVAILABLE, _BUILTIN_DISPATCH
    if not _REGISTRY_AVAILABLE:
        return
    try:
        import graphify.extract as extract_module
        from graphify_lang import registry as lang_registry

        if _BUILTIN_DISPATCH is None:
            _BUILTIN_DISPATCH = dict(extract_module._DISPATCH)
        for suffix, extractor in lang_registry.dispatch_table(_BUILTIN_DISPATCH).items():
            extract_module._DISPATCH[suffix] = extractor
            extract_module._DISPATCH[suffix.upper()] = extractor
            _LOG.debug("registered %s -> %s", suffix, extractor.__name__)
    except Exception as exc:
        _LOG.warning("registry dispatch failed: %s", exc)
        _REGISTRY_AVAILABLE = False


def claims_file(path) -> bool:
    """True when a plugin's ``[match]`` and sniff claim this data file as code."""
    if not _REGISTRY_AVAILABLE:
        return False
    from graphify_lang import registry as lang_registry
    return lang_registry.claims_file(path)


def augment_extractor(path, extractor):
    """``extractor`` wrapped by any augment plugin whose ``[match]`` claims ``path``."""
    if not _REGISTRY_AVAILABLE:
        return extractor
    from graphify_lang import registry as lang_registry
    return lang_registry.augment_extractor(path, extractor)


def context_fields() -> tuple[str, ...]:
    """Node fields the plugin resolvers read on unchanged files' nodes."""
    if not _REGISTRY_AVAILABLE:
        return ()
    from graphify_lang import registry as lang_registry
    return lang_registry.context_fields()


# Expose apply_registry for call sites
apply_registry: Callable[[], None] = _apply_registry


def format_languages() -> str:
    """Table of registered plugin languages for ``graphify lang list``.

    ``*`` after a suffix: shared with a built-in or another plugin (sniff-routed).
    ``+`` before a suffix: an augment that adds to that suffix's extractor.
    """
    try:
        from graphify_lang import registry as lang_registry
    except ImportError:
        return "No plugin languages registered (graphify_lang not installed)."
    manifests = list(lang_registry.iter_manifests())
    if not manifests:
        return "No plugin languages registered."
    import graphify.extract  # noqa: F401  (fills _BUILTIN_DISPATCH)
    builtins = _BUILTIN_DISPATCH or {}

    def shared(suffix: str) -> str:
        many = suffix in builtins or len(lang_registry.claimants(suffix)) > 1
        return suffix + ("*" if many else "")

    rows = [("language", "suffixes", "grammar", "sniff", "resolver")]
    for m in manifests:
        resolver = getattr(m.resolver, "name", None) or "-"
        sniff = "+".join(k for k, on in (("sniff", m.sniff), ("match", m.has_match)) if on) or "-"
        suffixes = (" ".join(shared(s) for s in sorted(m.suffixes))
                    or " ".join("+" + s for s in sorted(m.augments)))
        rows.append((m.name, suffixes, m.grammar or "-", sniff, resolver))
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    return "\n".join(
        "  ".join(c.ljust(w) for c, w in zip(r[:4], widths)) + "  " + r[4] for r in rows
    )
