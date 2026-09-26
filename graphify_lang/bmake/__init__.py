"""graphify_lang.bmake - Bentley bmake plugin (.mki, .mke).

- graphify-lang.toml: ``bmake`` (.mki, .mke), single claimant, no sniff
- extract.py: ``extract_bmake``, a line scanner, no grammar (plan 04 D7)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.bmake.extract import extract_bmake
from graphify_lang.bmake.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the bmake manifest."""
    return load_manifest(__file__, "graphify-lang.toml", extract=extract_bmake, resolver=RESOLVER)


__all__ = ["extract_bmake", "RESOLVER", "_get_manifest"]
