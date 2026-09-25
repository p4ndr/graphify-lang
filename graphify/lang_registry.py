"""Registry integration layer — merges language extensions from graphify_lang."""
from __future__ import annotations

import logging
from typing import Callable

_LOG = logging.getLogger(__name__)

# Global state
_REGISTRY_AVAILABLE = False
_REGISTRY_SUFFIXES: set[str] = set()


def _apply_registry() -> None:
    """Import and merge registry suffixes into core tables.
    
    Each call site wraps this in try/except so one failure doesn't break graphify.
    """
    global _REGISTRY_AVAILABLE, _REGISTRY_SUFFIXES
    
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
        
        _REGISTRY_AVAILABLE = True
        _LOG.debug("registry integration active, suffixes: %s", sorted(_REGISTRY_SUFFIXES))
    except Exception as exc:
        _LOG.warning("registry merge failed: %s", exc)
        _REGISTRY_AVAILABLE = False


def get_registry_suffixes() -> set[str]:
    """Return all registry suffixes (including case variants)."""
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


# Expose apply_registry for call sites
apply_registry: Callable[[], None] = _apply_registry


def format_languages() -> str:
    """Table of registered plugin languages for ``graphify lang list``.

    ``*`` after a suffix: shared with a built-in or another plugin (sniff-routed).
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
        suffixes = " ".join(shared(s) for s in sorted(m.suffixes))
        rows.append((m.name, suffixes, m.grammar or "-", sniff, resolver))
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    return "\n".join(
        "  ".join(c.ljust(w) for c, w in zip(r[:4], widths)) + "  " + r[4] for r in rows
    )
