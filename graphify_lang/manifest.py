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

        # Required fields
        if "name" not in data:
            errors.append("missing required field: name")
        if "suffixes" not in data:
            errors.append("missing required field: suffixes")
        if "extract" not in data:
            errors.append("missing required field: extract")

        # Validate suffixes is a list/tuple of strings
        if "suffixes" in data:
            suffixes = data["suffixes"]
            if not isinstance(suffixes, (list, tuple)):
                errors.append("suffixes must be a list or tuple")
                suffixes = []
            elif not all(isinstance(s, str) for s in suffixes):
                errors.append("suffixes must contain only strings")
                suffixes = []

        # Validate hook_suffixes if present
        hook_suffixes = ()
        if "hook_suffixes" in data:
            hs = data["hook_suffixes"]
            if not isinstance(hs, (list, tuple)):
                errors.append("hook_suffixes must be a list or tuple")
            elif not all(isinstance(s, str) for s in hs):
                errors.append("hook_suffixes must contain only strings")
            else:
                hook_suffixes = tuple(hs)

        # Validate extra if present
        extra = data.get("extra")
        if extra is not None and not isinstance(extra, str):
            errors.append("extra must be a string")

        # Validate grammar if present
        grammar = data.get("grammar")
        if grammar is not None and not isinstance(grammar, str):
            errors.append("grammar must be a string")

        if errors:
            return cls._invalid("; ".join(errors))

        # Build the manifest
        manifest = cls(
            name=data["name"],
            suffixes=frozenset(data["suffixes"]),
            extract=data["extract"],
            grammar=grammar,
            extra=extra,
            resolver=data.get("resolver"),
            hook_suffixes=hook_suffixes,
            fixture=Path(data["fixture"]) if "fixture" in data else None,
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
