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
        
        # Lower-case only: manifests lower-case their suffixes, and every core
        # lookup lower-cases the path suffix first (cc-CR000.001 L6).
        _REGISTRY_SUFFIXES.update(registry_suffixes)
        _HOOK_SUFFIXES.update(lang_registry.hook_suffixes())
        _HOOK_SUFFIXES |= _REGISTRY_SUFFIXES

        _REGISTRY_AVAILABLE = True
        _LOG.debug("registry integration active, suffixes: %s", sorted(_REGISTRY_SUFFIXES))
    except Exception as exc:
        _LOG.warning("registry merge failed: %s", exc)
        _REGISTRY_AVAILABLE = False
    _namespace_ast_cache(lang_registry)


# graphify.cache._EXTRACTOR_VERSION before a plugin fingerprint was appended.
_BASE_CACHE_VERSION: str | None = None


def _namespace_ast_cache(lang_registry) -> None:
    """Give the active plugin set its own AST cache namespace (cc-CR000.001 M2,
    E1). The extractor chosen for a file depends on the plugin set
    (``GRAPHIFY_LANG_DISABLE``, a plugin installed, plugin code changed), but
    the cache key is the file's bytes and the graphify version, so the
    namespace ``v<version>-s<schema>`` gets ``-lang<fingerprint>`` appended at
    run time (no edit to ``cache.py``). Entries written before this, including
    pre-stage-3 results whose refs have no ``node``, are never read again. A
    failed fingerprint gives ``-langerr``, never the plain namespace (S4-L1).
    """
    global _BASE_CACHE_VERSION
    import graphify.cache as cache

    if _BASE_CACHE_VERSION is None:
        _BASE_CACHE_VERSION = cache._EXTRACTOR_VERSION
    try:
        manifests = list(lang_registry.iter_manifests())
        names = tuple(sorted(m.name for m in manifests))
        modules = tuple(sorted({getattr(m.augment or m.extract, "__module__", "") or ""
                                for m in manifests}))
        folders = tuple(str(p) for p in lang_registry.search_paths())
        fp = _fingerprint(names, modules, folders, tuple(lang_registry.distributions()))
    except Exception as exc:
        _LOG.warning("plugin-set cache fingerprint failed, using the -langerr namespace: %s", exc)
        fp = "err"
    cache._EXTRACTOR_VERSION = f"{_BASE_CACHE_VERSION}-lang{fp}"


@functools.lru_cache(maxsize=8)
def _fingerprint(names: tuple[str, ...], modules: tuple[str, ...],
                 folders: tuple[str, ...] = (), dists: tuple[str, ...] = ()) -> str:
    """Hash of the manifest names, the plugin distributions (``name=version``,
    from their entry points), and the ``.py`` / ``.toml`` files of
    ``graphify_lang``, every plugin package and every ``GRAPHIFY_LANG_PATH``
    folder (cc-CR000.001 M5). A plugin shipped as a top-level module hashes
    that file only, not its folder (S4-M1)."""
    import hashlib
    import sys
    from pathlib import Path

    import graphify_lang

    h = hashlib.sha256("\0".join(names + dists).encode())
    dirs = {Path(graphify_lang.__file__).parent} | {Path(f) for f in folders}
    files: set[Path] = set()
    for top in {m.split(".")[0] for m in modules if m}:
        mod = sys.modules.get(top)
        if getattr(mod, "__path__", None) is not None:
            dirs.update(Path(p) for p in mod.__path__)
        elif getattr(mod, "__file__", None):
            files.add(Path(mod.__file__))
    for d in sorted(dirs):
        for f in sorted(d.rglob("*")):
            if f.suffix in (".py", ".toml") and f.is_file():
                h.update(b"\0" + f.relative_to(d).as_posix().encode() + b"\0" + f.read_bytes())
    for f in sorted(files):
        h.update(b"\0" + f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:12]


def get_registry_suffixes() -> set[str]:
    """Suffixes whose edit should rebuild the graph (lower-case).

    The code suffixes plus every manifest's ``hook_suffixes``. ``graphify.cli``
    merges this into ``_HOOK_SOURCE_EXTS``; ``detect`` uses ``get_code_suffixes``.
    """
    return _HOOK_SUFFIXES.copy()


def get_code_suffixes() -> set[str]:
    """Suffixes a plugin claims whole: code by suffix (lower-case)."""
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


def watch_claims(path, augments: bool = True) -> bool:
    """True when a plugin makes ``path`` code for ``graphify watch`` (cc-CR000.001
    M3): a ``[match]`` plugin claims it, or (``augments``) an augment adds to
    what the built-in extracts from it. A deleted path counts by its suffix, so
    the rebuild's reconcile drops its nodes."""
    if not _REGISTRY_AVAILABLE:
        return False
    from pathlib import Path

    from graphify_lang import registry as lang_registry

    path = Path(path)
    suffixes = lang_registry.match_suffixes()
    if augments:
        suffixes |= lang_registry.augment_suffixes()
    if path.suffix.lower() not in suffixes:
        return False
    if not path.is_file():
        return True
    if lang_registry.claims_file(path):
        return True
    if not augments:
        return False
    from graphify.extract import _get_extractor

    extractor = _get_extractor(path)
    inner = getattr(extractor, "__wrapped__", None)
    # ponytail: extracts the file twice to see whether an augment adds anything
    # (cc-kb matches every .md); fine for a debounced watch batch.
    return inner is not None and extractor(path) != inner(path)


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


def check_languages() -> tuple[str, bool]:
    """``graphify lang list --check`` (cc-CR000.001 E4): one row per plugin,
    ``ok`` or the load error, and whether every plugin loaded."""
    from graphify_lang import registry as lang_registry

    rows = [(m.name, "ok") for m in lang_registry.iter_manifests()]
    errors = lang_registry.load_errors()
    rows += [(source, f"error: {err}") for source, err in errors.items()]
    if not rows:
        return "No plugin languages registered.", True
    width = max(len(name) for name, _ in rows)
    return "\n".join(f"{name.ljust(width)}  {status}" for name, status in rows), not errors
