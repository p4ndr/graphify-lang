"""Registry of language plugins: the ``graphify_lang_plugins`` entry points,
then the manifests in each ``GRAPHIFY_LANG_PATH`` folder."""

from __future__ import annotations

import codecs
import functools
import hashlib
import importlib
import importlib.machinery
import importlib.metadata
import importlib.util
import logging
import os
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from graphify_lang.manifest import LanguageManifest, tomllib

_LOG = logging.getLogger(__name__)

# Environment variable to disable the registry entirely
_DISABLE_VAR = "GRAPHIFY_LANG_DISABLE"

# os.pathsep-separated folders of plugin manifests, loaded after the entry points
_PATH_VAR = "GRAPHIFY_LANG_PATH"

# The one entry-point group pyproject.toml ships (cc-CR000.001 L7)
_GROUP = "graphify_lang_plugins"

# Parent package of the per-folder packages path plugins import under (S5-H1)
_PATH_PACKAGE = "graphify_lang_path"


@dataclass
class _RegistryState:
    """Internal registry state, cached per process."""

    # GRAPHIFY_LANG_PATH folders that exist; part of the AST cache fingerprint
    search_paths: list[Path] = field(default_factory=list)
    manifests: dict[str, LanguageManifest] = field(default_factory=dict)
    suffix_to_manifest: dict[str, LanguageManifest] = field(default_factory=dict)
    tie_warned: set[str] = field(default_factory=set)
    # entry point name or manifest path -> load error (``graphify lang list --check``)
    load_errors: dict[str, str] = field(default_factory=dict)
    # manifest path -> a loaded plugin's warning, e.g. a runtime name clash (S5-H1)
    load_warnings: dict[str, str] = field(default_factory=dict)
    # top-level runtime name -> the path folder that first used it (S5-H1)
    runtimes: dict[str, Path] = field(default_factory=dict)
    # ``name=version`` of each loaded entry point's distribution (AST cache fingerprint)
    distributions: set[str] = field(default_factory=set)


# Process-wide cache
_STATE: _RegistryState | None = None


def _init_state() -> _RegistryState:
    """Initialize or return the cached registry state.

    Each plugin loads inside its own ``try``: a failure is logged and recorded,
    and the other plugins still register (cc-CR000.001 M1).
    """
    global _STATE
    if _STATE is not None:
        return _STATE
    # Set before loading, so a plugin that calls back into the registry while
    # it loads sees the partial state instead of starting a second discovery.
    state = _STATE = _RegistryState()
    if os.environ.get(_DISABLE_VAR, "").strip().lower() in ("1", "true", "yes", "on"):
        return state
    try:
        eps = list(importlib.metadata.entry_points(group=_GROUP))
    except Exception as exc:  # corrupt distribution metadata (S5-M1)
        _failed(state, "entry points", "entry points", exc)
        eps = []
    for ep in eps:
        try:
            _process_loader_result(ep.load())
            if ep.dist is not None:
                state.distributions.add(f"{ep.dist.name}={ep.dist.version}")
        except Exception as exc:
            _failed(state, "entry point", ep.name, exc)
    for entry in os.environ.get(_PATH_VAR, "").split(os.pathsep):
        if entry:
            _load_folder(state, entry)
    return state


def _failed(state: _RegistryState, kind: str, source: str, exc: Exception | str) -> None:
    _LOG.warning("failed to load %s %s: %s", kind, source, exc)
    state.load_errors[source] = str(exc)


def _load_folder(state: _RegistryState, entry: str) -> None:
    """Register every manifest in a ``GRAPHIFY_LANG_PATH`` folder (M5).

    The entry must be absolute after ``~`` expansion: a relative one would run
    code from whatever folder graphify starts in (S5-M3). A bad entry is a load
    error of its own and the later folders still load (S5-M1); a folder listed
    twice loads once (S5-L2).
    """
    try:
        folder = Path(entry).expanduser()
        if not folder.is_absolute():
            raise ValueError("must be an absolute path")
        folder = folder.resolve()
    except Exception as exc:
        _failed(state, "plugin folder", entry, exc)
        return
    if folder in state.search_paths:
        return
    if not folder.is_dir():
        _failed(state, "plugin folder", str(folder), "not a directory")
        return
    state.search_paths.append(folder)
    for toml in sorted(folder.glob("*.toml")):
        try:
            if _is_manifest(toml):
                _register_new(_path_manifest(state, folder, toml))
            else:
                _LOG.debug("%s has no [language] table: not a manifest", toml)
        except Exception as exc:
            _failed(state, "manifest", str(toml), exc)


def _is_manifest(toml: Path) -> bool:
    """False for a ``*.toml`` that parses and has no ``[language]`` table
    (``pyproject.toml``, ``ruff.toml``; S5-L3). One that does not parse is a
    manifest, so ``from_toml`` reports the error."""
    try:
        return "language" in tomllib.loads(toml.read_text(encoding="utf-8"))
    except Exception:
        return True


def _folder_package(folder: Path) -> str:
    """``graphify_lang_path._<hash>``: an empty package whose ``__path__`` is
    ``folder``. A path plugin's runtime and its own modules import under it,
    never as top-level names, so two folders cannot share a module and no
    installed or stdlib module is shadowed (S5-H1, S5-L1). ``sys.path`` is
    never changed."""
    name = f"{_PATH_PACKAGE}._{hashlib.sha256(str(folder).encode()).hexdigest()[:16]}"
    for package, where in ((_PATH_PACKAGE, []), (name, [str(folder)])):
        if package not in sys.modules:
            spec = importlib.machinery.ModuleSpec(package, None, is_package=True)
            spec.submodule_search_locations = where
            sys.modules[package] = importlib.util.module_from_spec(spec)
    return name


def _importable(name: str) -> bool:
    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _path_manifest(state: _RegistryState, folder: Path, toml: Path) -> LanguageManifest:
    """The manifest ``toml`` with the callables of its ``[extract] runtime``
    module: ``extract`` (or ``augment`` for an augment) and optional
    ``RESOLVER`` and ``WATCH``, as an entry-point package sets them. The
    module is imported as ``<_folder_package(folder)>.<runtime>``. A runtime
    whose top-level name another folder's runtime or an importable module
    also has still loads, with a clash warning: an absolute ``import`` of that
    name inside the plugin gets the other module."""
    manifest, errors = LanguageManifest.from_toml(toml)
    if errors:
        raise ValueError("; ".join(errors))
    top = manifest.runtime.split(".")[0]
    other = state.runtimes.get(top)
    clash = (f"the runtime of {other}" if other not in (None, folder)
             else "an importable module" if _importable(top) else None)
    module = importlib.import_module(f"{_folder_package(folder)}.{manifest.runtime}")
    attr = "augment" if manifest.kind == "augment" else "extract"
    func = getattr(module, attr, None)
    if not callable(func):
        raise ValueError(f"{manifest.runtime} has no callable {attr!r}")
    state.runtimes.setdefault(top, folder)
    if clash:
        state.load_warnings[str(toml)] = (
            f"runtime name {top!r} clashes with {clash}; loaded from {folder} "
            f"under a private package, so use relative imports inside it")
        _LOG.warning("manifest %s: %s", toml, state.load_warnings[str(toml)])
    return replace(manifest, **{attr: func}, resolver=getattr(module, "RESOLVER", None),
                   watch=getattr(module, "WATCH", None))


def _process_loader_result(result: Any) -> None:
    """Register what an entry point loaded: a manifest, a callable returning
    one (``_get_manifest``), or a list of either."""
    if callable(result):
        result = result()
    if isinstance(result, LanguageManifest):
        _register_new(result)
    elif isinstance(result, (list, tuple)):
        for item in result:
            _process_loader_result(item)
    # Ignore other types silently - the loader may return metadata


def _register_new(manifest: LanguageManifest) -> None:
    """Register a discovered manifest. A name already registered raises, for an
    entry point and a path manifest alike: the first one wins and the second
    is a load error (S5-L2)."""
    if _STATE is not None and manifest.name in _STATE.manifests:
        raise ValueError(f"language {manifest.name!r} is already registered")
    _register_manifest(manifest)


def _register_manifest(manifest: LanguageManifest) -> None:
    """Register a manifest into the registry.

    A manifest registered before discovery ran (tests do this) makes a registry
    of its own: discovery then never runs in this process until ``reset()``.
    A later manifest of the same name replaces it (tests rely on that);
    discovery goes through ``_register_new`` instead.
    """
    global _STATE
    if _STATE is None:
        _STATE = _RegistryState()
    if not manifest.name:
        _LOG.warning("manifest with empty name ignored")
        return
    _STATE.manifests[manifest.name] = manifest
    for suffix in manifest.suffixes:
        # First claimant is the suffix's manifest for metadata (extras). Who
        # extracts a shared suffix is decided by dispatch_table (plan 04 §3.1).
        _STATE.suffix_to_manifest.setdefault(suffix, manifest)

    _register_resolver(manifest.resolver)


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


def hook_suffixes() -> set[str]:
    """Every manifest's ``hook_suffixes``, augments included."""
    return {s for m in _init_state().manifests.values() for s in m.hook_suffixes}


def match_suffixes() -> set[str]:
    """Suffixes claimed only per path (``[match]``): code only via ``claims_file``."""
    return {s for m in _languages() if m.has_match for s in m.suffixes} - registered_suffixes()


def augment_suffixes() -> set[str]:
    """Suffixes an augment adds to (``language.augments``)."""
    return {s for m in _init_state().manifests.values() if m.kind == "augment" for s in m.augments}


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
    name = path.name.casefold()                # cargo.toml on a case-insensitive FS (N5)
    if any(name == f.casefold() for f in m.match_filenames):
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
    if raw[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):  # NULs are the encoding here
        text = raw[: len(raw) // 2 * 2].decode("utf-16", errors="replace").removeprefix("\ufeff")
    elif not raw or b"\x00" in raw:  # empty or binary: never code by content
        return None
    else:
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
    # Augments are applied per path by augment_extractor (from _get_extractor),
    # so _DISPATCH keeps the built-in itself (upstream pins _DISPATCH['.md']).
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
            if _sniff_score(m, path, head) is None:
                continue
            try:
                extra = m.augment(path, result) or {}
            except Exception as exc:  # an augment bug must not cost the base result
                _LOG.warning("augment %s failed on %s: %s", m.name, path, exc)
                continue
            result = _merge(m, result, extra)
        return result
    augmented.__name__ = augmented.__qualname__ = f"augmented[{suffix}]"
    augmented.__wrapped__ = inner
    return augmented


def _claiming_augments(path: Path) -> list[LanguageManifest]:
    suffix = path.suffix.lower()
    on_suffix = [m for m in _init_state().manifests.values()
                 if m.kind == "augment" and m.augment and suffix in m.augments]
    size = max((m.sniff.head_bytes for m in on_suffix if m.sniff), default=0)
    head = _head_reader(path, size)
    return [m for m in on_suffix if _sniff_score(m, path, head) is not None]


def augment_extractor(path: Path, inner: Callable[[Path], dict]) -> Callable[[Path], dict]:
    """``inner`` wrapped by the augments that claim ``path``, else ``inner`` itself.

    Called by ``_get_extractor`` on the extractor it picked (by file name for a
    package manifest, else from ``_DISPATCH``), so a file the augment's
    ``[match]`` does not claim keeps the plain built-in.
    """
    claiming = _claiming_augments(path)
    return _augmented(path.suffix.lower(), inner, claiming) if claiming else inner


def augment_watch_claims(path: Path, inner: Callable[[Path], dict]) -> bool:
    """True when an augment that claims ``path`` makes it code for ``graphify
    watch`` (S5-M2): its ``watch`` predicate says so, or, with none, it adds
    anything to ``inner``'s result. A failing check claims the file (a rebuild
    too many, never a stale graph)."""
    base = None
    for m in _claiming_augments(path):
        try:
            if m.watch is not None:
                hit = m.watch(path)
            else:
                base = inner(path) if base is None else base
                hit = _merge(m, base, m.augment(path, base) or {}) != base
        except Exception as exc:
            _LOG.warning("augment %s: watch check failed on %s: %s", m.name, path, exc)
            hit = True
        if hit:
            return True
    return False


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
    # Any other key (a resolver payload such as ``<plugin>_refs``) rides along
    # when the base result does not already carry it.
    carried = {k: v for k, v in extra.items()
               if k not in ("nodes", "edges", "attrs") and k not in base}
    return {**base, **carried, "nodes": nodes, "edges": edges}


def claims_file(path: Path) -> bool:
    """True when a ``[match]`` plugin's glob and sniff both pass for ``path`` (D3)."""
    suffix = path.suffix.lower()
    if suffix not in match_suffixes():
        return False
    candidates = [m for m in claimants(suffix) if m.has_match]
    size = max((m.sniff.head_bytes for m in candidates if m.sniff), default=0)
    head = _head_reader(path, size)
    return any(_sniff_score(m, path, head) is not None for m in candidates)


def context_fields() -> tuple[str, ...]:
    """Every manifest's ``[resolve] context_fields``, sorted: the node fields an
    incremental build keeps on the context nodes of unchanged files (H1)."""
    return tuple(sorted({f for m in _init_state().manifests.values() for f in m.context_fields}))


def load_errors() -> dict[str, str]:
    """Plugins that failed to load: entry point name or manifest path -> error."""
    return dict(_init_state().load_errors)


def load_warnings() -> dict[str, str]:
    """Plugins that loaded with a warning (a runtime name clash): manifest path -> text."""
    return dict(_init_state().load_warnings)


def distributions() -> list[str]:
    """``name=version`` of the distributions whose entry points loaded, sorted."""
    return sorted(_init_state().distributions)


def search_paths() -> list[Path]:
    """The ``GRAPHIFY_LANG_PATH`` folders that were loaded."""
    return list(_init_state().search_paths)


def iter_manifests() -> Iterator[LanguageManifest]:
    """Iterate over all registered manifests."""
    state = _init_state()
    return iter(list(state.manifests.values()))


def reset() -> None:
    """Clear the registry cache so discovery runs again."""
    global _STATE
    _STATE = None
