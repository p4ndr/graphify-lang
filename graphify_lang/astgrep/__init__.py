"""graphify_lang.astgrep - ast-grep project YAML plugin (plan 04 S11).

- graphify-lang.toml: ``astgrep`` on .yml / .yaml, claimed per path ([match] + sniff)
- extract.py: ``extract_astgrep`` (PyYAML when importable, else a flat line parser)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.astgrep.extract import extract_astgrep
from graphify_lang.astgrep.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the astgrep manifest."""
    return load_manifest(__file__, "graphify-lang.toml", extract=extract_astgrep, resolver=RESOLVER)


__all__ = ["extract_astgrep", "RESOLVER", "_get_manifest"]
