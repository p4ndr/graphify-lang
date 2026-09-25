"""graphify_lang.cargo - Cargo.toml augment (plan 04 S10, D9).

- graphify-lang.toml: ``cargo``, kind ``augment`` on ``.toml``, [match] ``Cargo.toml``
- augment.py: ``augment_cargo``, run on top of core ``extract_package_manifest``
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from graphify_lang.cargo.augment import augment_cargo
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the cargo augment manifest."""
    manifest, errors = LanguageManifest.from_toml(Path(__file__).parent / "graphify-lang.toml")
    if errors:
        raise ValueError(f"graphify-lang.toml: {errors}")
    return replace(manifest, augment=augment_cargo)


__all__ = ["augment_cargo", "_get_manifest"]
