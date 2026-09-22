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
def apply_dispatch() -> None:
    """Apply registry extractors to _DISPATCH in graphify.extract."""
    global _REGISTRY_AVAILABLE
    if not _REGISTRY_AVAILABLE:
        return
    try:
        import graphify.extract as extract_module
        from graphify_lang import registry as lang_registry
        
        for suffix in _REGISTRY_SUFFIXES:
            manifest = lang_registry.get_manifest_for_suffix(suffix)
            if manifest and manifest.extract:
                # Use the suffix's base name for a stable __name__
                base = suffix.lstrip('.')
                extract_module._DISPATCH[suffix] = manifest.extract
                # Also register case variant
                extract_module._DISPATCH[suffix.upper()] = manifest.extract
                _LOG.debug("registered %s → %s", suffix, manifest.name)
    except Exception as exc:
        _LOG.warning("registry dispatch failed: %s", exc)
        _REGISTRY_AVAILABLE = False


# Expose apply_registry for call sites
apply_registry: Callable[[], None] = _apply_registry
