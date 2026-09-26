"""Language manifest schema and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# The one tomllib shim in the fork; everything else imports it from here.
try:
    import tomllib
except ImportError:  # pragma: no cover  (Python 3.10: tomli is a dependency below 3.11)
    import tomli as tomllib


_FLAGS = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}
_KINDS = ("language", "augment")


@dataclass(frozen=True)
class Sniff:
    """A ``[sniff]`` table: weighted regex rules read on the file head (plan 04 D1).

    Every rule is compiled with ``re.MULTILINE`` so ``^`` anchors a line.
    """

    rules: tuple[tuple[re.Pattern[str], float], ...]
    min_score: float = 1
    head_bytes: int = 4096

    def score(self, head: str) -> float:
        return sum(weight for rx, weight in self.rules if rx.search(head))


def _parse_sniff(table: Any) -> tuple[Sniff | None, list[str]]:
    if not isinstance(table, dict):
        return None, ["[sniff] must be a table"]
    errors: list[str] = []
    raw_rules = table.get("rules", [])
    if "min_score" in table and not raw_rules:
        errors.append("sniff.min_score set without sniff.rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        return None, errors or ["sniff.rules must be a non-empty list"]
    rules = []
    for i, rule in enumerate(raw_rules):
        if not isinstance(rule, dict) or not isinstance(rule.get("re"), str):
            errors.append(f"sniff.rules[{i}] needs a string 're'")
            continue
        weight = rule.get("weight", 1)
        flags = rule.get("flags", "")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            errors.append(f"sniff.rules[{i}].weight must be a number")
            continue
        if not isinstance(flags, str) or set(flags) - set(_FLAGS):
            errors.append(f"sniff.rules[{i}].flags must use only {''.join(_FLAGS)}")
            continue
        bits = re.MULTILINE
        for f in flags:
            bits |= _FLAGS[f]
        try:
            rules.append((re.compile(rule["re"], bits), weight))
        except re.error as exc:
            errors.append(f"sniff.rules[{i}]: bad regex {rule['re']!r}: {exc}")
    head_bytes = table.get("head_bytes", 4096)
    if not isinstance(head_bytes, int) or isinstance(head_bytes, bool) or head_bytes <= 0:
        errors.append("sniff.head_bytes must be a positive integer")
    min_score = table.get("min_score", 1)
    if not isinstance(min_score, (int, float)) or isinstance(min_score, bool):
        errors.append("sniff.min_score must be a number")
    if errors:
        return None, errors
    return Sniff(rules=tuple(rules), min_score=min_score, head_bytes=head_bytes), []


def _str_list(value: Any, field: str, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value):
        errors.append(f"{field} must be a list of strings")
        return ()
    return tuple(value)


def _lower(values) -> tuple[str, ...]:
    """Suffixes lower-cased, order kept, duplicates dropped: the registry compares a
    lower-cased path suffix, so ``.LSP`` would never match (cc-CR000.001 L4)."""
    return tuple(dict.fromkeys(v.lower() for v in values))


@dataclass(frozen=True)
class LanguageManifest:
    """A language package manifest.

    Fields match the schema defined in .claude/docs/cc-IP000.001.md §S003.
    """

    name: str
    suffixes: frozenset[str]
    extract: Callable[[Path], dict]
    grammar: str | None = None
    extra: str | None = None
    resolver: Any | None = None
    hook_suffixes: tuple[str, ...] = ()
    fixture: Path | None = None
    # Plan 04 §3: shared-suffix routing and the augment kind.
    kind: str = "language"
    augments: frozenset[str] = frozenset()
    overrides: frozenset[str] = frozenset()
    priority: int = 0
    sniff: Sniff | None = None
    match_globs: tuple[str, ...] = ()
    match_filenames: tuple[str, ...] = ()
    augment: Callable[[Path, dict], dict] | None = None
    # Node fields the resolver reads on other files' nodes: kept on the
    # context nodes of unchanged files in an incremental build (H1).
    context_fields: tuple[str, ...] = ("node_kind",)
    # ``[extract] runtime``: the module a GRAPHIFY_LANG_PATH plugin is loaded from.
    runtime: str | None = None

    @property
    def has_match(self) -> bool:
        return bool(self.match_globs or self.match_filenames)

    @classmethod
    def from_toml(cls, path: Path) -> tuple[LanguageManifest, list[str]]:
        """Parse a manifest from a TOML file.

        Returns (manifest, list_of_validation_errors).
        Every failure is a one-line reason and a rejected manifest, never an exception.
        """
        errors: list[str] = []

        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return cls._invalid(f"cannot read manifest: {exc}")

        try:
            data = tomllib.loads(content)
        except RecursionError:
            return cls._invalid("TOML parse error: nested deeper than the recursion limit")
        except tomllib.TOMLDecodeError as exc:
            return cls._invalid(f"TOML parse error: {exc}")

        # Extract nested values - schema v1 uses sections
        for section in ("language", "grammar", "extract", "match", "resolve"):
            if not isinstance(data.get(section, {}), dict):
                return cls._invalid(f"[{section}] must be a table")
        language = data.get("language", {})
        grammar = data.get("grammar", {})
        extract = data.get("extract", {})

        schema = data.get("schema", 1)
        if schema != "v1" and not (type(schema) is int and schema == 1):  # not True, not 1.0
            errors.append('schema must be 1 or "v1"')
        kind = language.get("kind", "language")
        if kind not in _KINDS:
            errors.append(f"language.kind must be one of {', '.join(_KINDS)}")
        augments = _lower(_str_list(language.get("augments", ()), "augments", errors))
        overrides = _lower(_str_list(language.get("overrides", ()), "overrides", errors))
        priority = language.get("priority", 0)
        if not isinstance(priority, int) or isinstance(priority, bool):
            errors.append("priority must be an integer")
            priority = 0
        sniff = None
        if "sniff" in data:
            sniff, sniff_errors = _parse_sniff(data["sniff"])
            errors.extend(sniff_errors)
        match = data.get("match", {})
        match_globs = _str_list(match.get("globs", ()), "match.globs", errors)
        match_filenames = _str_list(match.get("filenames", ()), "match.filenames", errors)
        context_fields = _str_list(data.get("resolve", {}).get("context_fields", ("node_kind",)),
                                   "resolve.context_fields", errors)
        if kind == "augment":
            if not augments:
                errors.append("augment kind needs a non-empty language.augments")
            language = {"suffixes": [], **language}  # an augment claims no suffix

        # Required fields - check for presence first, then validate value
        if "name" not in language:
            errors.append("missing required field: language.name")
            name = ""
        else:
            name = language.get("name")
            if not isinstance(name, str):
                errors.append("name must be a string")
                name = ""
            elif not name:
                errors.append("name must be non-empty")
        
        if "suffixes" not in language:
            errors.append("missing required field: language.suffixes")
            suffixes = []
        else:
            suffixes = language.get("suffixes")
            if not suffixes and kind != "augment":
                errors.append("suffixes must not be empty")
        
        # Validate suffixes is a list/tuple of strings
        if suffixes and not isinstance(suffixes, (list, tuple)):
            errors.append("suffixes must be a list or tuple")
            suffixes = []
        elif suffixes and not all(isinstance(s, str) for s in suffixes):
            errors.append("suffixes must contain only strings")
            suffixes = []
        suffixes = _lower(suffixes or ())
        
        # Validate hook_suffixes if present
        hook_suffixes = language.get("hook_suffixes", ())
        if not isinstance(hook_suffixes, (list, tuple)):
            errors.append("hook_suffixes must be a list or tuple")
            hook_suffixes = ()
        elif not all(isinstance(s, str) for s in hook_suffixes):
            errors.append("hook_suffixes must contain only strings")
            hook_suffixes = ()
        else:
            hook_suffixes = _lower(hook_suffixes)
        
        # Validate extra if present
        extra = grammar.get("extra")
        if extra is not None and not isinstance(extra, str):
            errors.append("extra must be a string")
        
        # Validate grammar module if present
        grammar_module = grammar.get("module")
        if grammar_module is not None and not isinstance(grammar_module, str):
            errors.append("grammar.module must be a string")
        
        # Validate runtime is present
        runtime = extract.get("runtime")
        if not runtime:
            errors.append("missing required field: extract.runtime")
        elif not isinstance(runtime, str):
            errors.append("extract.runtime must be a string")
        resolver = extract.get("resolver")
        if resolver is not None and not isinstance(resolver, str):
            errors.append("extract.resolver must be a string")

        if sniff is not None and isinstance(suffixes, (list, tuple)):
            both = sorted(set(overrides) & set(suffixes))
            if both:
                errors.append(f"overrides and [sniff] on the same suffix: {', '.join(both)}")

        if errors:
            return cls._invalid("; ".join(errors))

        # extract / augment / resolver are set by the package's entry point
        # (graphify_lang._common.load_manifest), or from the ``runtime`` module
        # for a GRAPHIFY_LANG_PATH plugin (registry._path_manifest).
        manifest = cls(
            name=name,
            suffixes=frozenset(suffixes) if suffixes else frozenset(),
            extract=lambda p: {},  # placeholder until the entry point sets it
            grammar=grammar_module,
            extra=extra,
            resolver=resolver,
            hook_suffixes=hook_suffixes,
            fixture=None,
            kind=kind,
            augments=frozenset(augments),
            overrides=frozenset(overrides),
            priority=priority,
            sniff=sniff,
            match_globs=match_globs,
            match_filenames=match_filenames,
            context_fields=context_fields,
            runtime=runtime,
        )

        # Additional validation
        if not manifest.name:
            return cls._invalid("name must be non-empty")

        if not manifest.suffixes and kind != "augment":
            return cls._invalid("suffixes must not be empty")

        # S1-L5: a dotless suffix can never equal a Path.suffix, so it would do nothing.
        for s in manifest.suffixes | manifest.augments | manifest.overrides | set(hook_suffixes):
            if not s.startswith("."):
                return cls._invalid(f"suffix '{s}' must start with '.'")

        return (manifest, [])

    @classmethod
    def _invalid(cls, reason: str) -> tuple[LanguageManifest, list[str]]:
        """Return an invalid manifest with a single error reason."""
        return (cls(name="", suffixes=frozenset(), extract=lambda p: {}), [reason])
