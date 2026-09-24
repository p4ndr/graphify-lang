"""Language manifest schema and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import tomli


@dataclass(frozen=True)
class LanguageManifest:
    """A language package manifest.

    Fields match the schema defined in docs/plans/cc-IP000.001.md §S003.
    """

    name: str
    suffixes: frozenset[str]
    extract: Callable[[Path], dict]
    grammar: str | None = None
    extra: str | None = None
    resolver: Any | None = None
    hook_suffixes: tuple[str, ...] = ()
    fixture: Path | None = None

    @classmethod
    def from_toml(cls, path: Path) -> tuple[LanguageManifest, list[str]]:
        """Parse a manifest from a TOML file.

        Returns (manifest, list_of_validation_errors).
        Every failure is a one-line reason and a rejected manifest, never an exception.
        """
        errors: list[str] = []

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            return cls._invalid(f"cannot read manifest: {exc}")

        try:
            data = tomli.loads(content)
        except tomli.TOMLDecodeError as exc:
            return cls._invalid(f"TOML parse error: {exc}")

        # Extract nested values - schema v1 uses sections
        language = data.get("language", {})
        grammar = data.get("grammar", {})
        extract = data.get("extract", {})

        # Required fields - check for presence first, then validate value
        if "name" not in language:
            errors.append("missing required field: language.name")
            name = ""
        else:
            name = language.get("name")
            if not name:
                errors.append("name must be non-empty")
        
        if "suffixes" not in language:
            errors.append("missing required field: language.suffixes")
            suffixes = []
        else:
            suffixes = language.get("suffixes")
            if not suffixes:
                errors.append("suffixes must not be empty")
        
        # Validate suffixes is a list/tuple of strings
        if suffixes and not isinstance(suffixes, (list, tuple)):
            errors.append("suffixes must be a list or tuple")
            suffixes = []
        elif suffixes and not all(isinstance(s, str) for s in suffixes):
            errors.append("suffixes must contain only strings")
            suffixes = []
        
        # Validate hook_suffixes if present
        hook_suffixes = language.get("hook_suffixes", ())
        if not isinstance(hook_suffixes, (list, tuple)):
            errors.append("hook_suffixes must be a list or tuple")
            hook_suffixes = ()
        elif not all(isinstance(s, str) for s in hook_suffixes):
            errors.append("hook_suffixes must contain only strings")
            hook_suffixes = ()
        else:
            hook_suffixes = tuple(hook_suffixes)
        
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

        if errors:
            return cls._invalid("; ".join(errors))

        # Build the manifest - extract is the runtime module name
        # The registry will call runtime.build(path, data) to get the extract callable
        manifest = cls(
            name=name,
            suffixes=frozenset(suffixes) if suffixes else frozenset(),
            extract=lambda p: {},  # Placeholder, replaced by runtime.build()
            grammar=grammar_module,
            extra=extra,
            resolver=extract.get("resolver"),
            hook_suffixes=hook_suffixes,
            fixture=None,
        )

        # Additional validation
        if not manifest.name:
            return cls._invalid("name must be non-empty")

        if not manifest.suffixes:
            return cls._invalid("suffixes must not be empty")

        for s in manifest.suffixes:
            if not s.startswith("."):
                return cls._invalid(f"suffix '{s}' must start with '.'")

        return (manifest, [])

    @classmethod
    def _invalid(cls, reason: str) -> tuple[LanguageManifest, list[str]]:
        """Return an invalid manifest with a single error reason."""
        return (cls(name="", suffixes=frozenset(), extract=lambda p: {}), [reason])
