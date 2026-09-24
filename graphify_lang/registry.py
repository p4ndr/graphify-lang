"""Registry for language packages discovered via entry points or namespace."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
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
        # Precedence: built-in suffix is taken only when listed in overrides
        # For now, we just register the first manifest that claims each suffix
        if suffix not in state.suffix_to_manifest:
            state.suffix_to_manifest[suffix] = manifest
        else:
            # Already claimed - warn once per process
            existing = state.suffix_to_manifest[suffix]
            if manifest.name not in state.warned_builtins:
                _LOG.warning(
                    "suffix %s claimed by %s; already registered by %s",
                    suffix,
                    manifest.name,
                    existing.name,
                )
                state.warned_builtins.add(manifest.name)

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
    """Return all suffixes claimed by registered languages."""
    state = _init_state()
    return set(state.suffix_to_manifest.keys())


def iter_manifests() -> Iterator[LanguageManifest]:
    """Iterate over all registered manifests."""
    state = _init_state()
    return iter(list(state.manifests.values()))


def reset() -> None:
    """Clear the registry cache so discovery runs again."""
    global _STATE
    _STATE = None
