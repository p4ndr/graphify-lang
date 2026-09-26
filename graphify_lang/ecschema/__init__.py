"""graphify_lang.ecschema - Bentley ECSchema XML plugin (plan 04 S12).

- graphify-lang.toml: ``ecschema`` on .xml, claimed when the root is ``<ECSchema``
- extract.py: ``extract_ecschema`` (stdlib expat, no DTD)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.ecschema.extract import extract_ecschema
from graphify_lang.ecschema.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the ecschema manifest."""
    return load_manifest(__file__, "graphify-lang.toml", extract=extract_ecschema, resolver=RESOLVER)


__all__ = ["extract_ecschema", "RESOLVER", "_get_manifest"]
