"""graphify_lang.vba - VBA plugin (.bas, .cls, .frm; .frx skipped).

- graphify-lang.toml: ``vba`` (.bas, .frm), single claimant, no sniff
- cls.toml: ``vba-cls`` (.cls), sniffed against the built-in extract_apex
- extract.py: ``extract_vba``, a line scanner, no grammar (plan 04 D7)
- resolve.py: the cross-module ``RESOLVER`` (registered by the registry)
- data/builtins.txt: VBA keywords, intrinsic types and VBA-library names
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.manifest import LanguageManifest
from graphify_lang.vba.extract import extract_vba
from graphify_lang.vba.resolve import RESOLVER


def _load(toml_name: str) -> LanguageManifest:
    return load_manifest(__file__, toml_name, extract=extract_vba, resolver=RESOLVER)


def _get_manifest() -> list[LanguageManifest]:
    """Entry point: the module/form and class-module manifests."""
    return [_load("graphify-lang.toml"), _load("cls.toml")]


__all__ = ["extract_vba", "RESOLVER", "_get_manifest"]
