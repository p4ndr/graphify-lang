"""graphify_lang.cc_kb - harness KB markdown augment (plan 04 S13, D5, D6).

- graphify-lang.toml: ``cc-kb``, kind ``augment`` on ``.md``, [match] ``**/docs/cc-*.md``
- augment.py: ``augment_cc_kb``, run on top of core ``extract_markdown``
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from graphify_lang.cc_kb.augment import augment_cc_kb
from graphify_lang.cc_kb.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the cc-kb augment manifest."""
    manifest, errors = LanguageManifest.from_toml(Path(__file__).parent / "graphify-lang.toml")
    if errors:
        raise ValueError(f"graphify-lang.toml: {errors}")
    return replace(manifest, augment=augment_cc_kb, resolver=RESOLVER)


__all__ = ["augment_cc_kb", "RESOLVER", "_get_manifest"]
