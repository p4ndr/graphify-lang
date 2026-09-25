"""graphify_lang.ecschema - Bentley ECSchema XML plugin (plan 04 S12).

- graphify-lang.toml: ``ecschema`` on .xml, claimed when the root is ``<ECSchema``
- extract.py: ``extract_ecschema`` (stdlib expat, no DTD)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from graphify_lang.ecschema.extract import extract_ecschema
from graphify_lang.ecschema.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the ecschema manifest."""
    manifest, errors = LanguageManifest.from_toml(Path(__file__).parent / "graphify-lang.toml")
    if errors:
        raise ValueError(f"graphify-lang.toml: {errors}")
    return replace(manifest, extract=extract_ecschema, resolver=RESOLVER)


__all__ = ["extract_ecschema", "RESOLVER", "_get_manifest"]
