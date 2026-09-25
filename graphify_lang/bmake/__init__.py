"""graphify_lang.bmake - Bentley bmake plugin (.mki, .mke).

- graphify-lang.toml: ``bmake`` (.mki, .mke), single claimant, no sniff
- extract.py: ``extract_bmake``, a line scanner, no grammar (plan 04 D7)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from graphify_lang.bmake.extract import extract_bmake
from graphify_lang.bmake.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the bmake manifest."""
    manifest, errors = LanguageManifest.from_toml(Path(__file__).parent / "graphify-lang.toml")
    if errors:
        raise ValueError(f"graphify-lang.toml: {errors}")
    return replace(manifest, extract=extract_bmake, resolver=RESOLVER)


__all__ = ["extract_bmake", "RESOLVER", "_get_manifest"]
