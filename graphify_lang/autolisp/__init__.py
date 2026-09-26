"""graphify_lang.autolisp - AutoLISP (.lsp, .mnl) and DCL (.dcl) plugin.

- graphify-lang.toml / dcl.toml: the two manifests (language, suffixes, grammar)
- extract.py: ``extract_autolisp`` / ``extract_dcl``, one walker, no query rules
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
- data/builtins.txt: AutoLispExt built-in names (Apache-2.0, LICENSE.AutoLispExt)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.autolisp.extract import extract_autolisp, extract_dcl
from graphify_lang.autolisp.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _load(toml_name: str, extract) -> LanguageManifest:
    return load_manifest(__file__, toml_name, extract=extract, resolver=RESOLVER)


def _get_autolisp_manifest() -> LanguageManifest:
    return _load("graphify-lang.toml", extract_autolisp)


def _get_dcl_manifest() -> LanguageManifest:
    return _load("dcl.toml", extract_dcl)


def _get_manifest() -> list[LanguageManifest]:
    """Entry point: the AutoLISP and DCL manifests."""
    return [_get_autolisp_manifest(), _get_dcl_manifest()]


__all__ = ["extract_autolisp", "extract_dcl", "RESOLVER", "_get_manifest",
           "_get_autolisp_manifest", "_get_dcl_manifest"]
