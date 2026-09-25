"""graphify_lang.autolisp - AutoLISP (.lsp, .mnl) and DCL (.dcl) plugin.

- graphify-lang.toml / dcl.toml: the two manifests (language, suffixes, grammar)
- extract.py: ``extract_autolisp`` / ``extract_dcl``, one walker, no query rules
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
- data/builtins.txt: AutoLispExt built-in names (Apache-2.0, LICENSE.AutoLispExt)
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from graphify_lang.autolisp.extract import extract_autolisp, extract_dcl
from graphify_lang.autolisp.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _load(toml_name: str, extract) -> LanguageManifest:
    manifest, errors = LanguageManifest.from_toml(Path(__file__).parent / toml_name)
    if errors:
        raise ValueError(f"{toml_name}: {errors}")
    return replace(manifest, extract=extract, resolver=RESOLVER)


def _get_autolisp_manifest() -> LanguageManifest:
    return _load("graphify-lang.toml", extract_autolisp)


def _get_dcl_manifest() -> LanguageManifest:
    return _load("dcl.toml", extract_dcl)


def _get_manifest() -> list[LanguageManifest]:
    """Entry point: the AutoLISP and DCL manifests."""
    return [_get_autolisp_manifest(), _get_dcl_manifest()]


__all__ = ["extract_autolisp", "extract_dcl", "RESOLVER", "_get_manifest",
           "_get_autolisp_manifest", "_get_dcl_manifest"]
