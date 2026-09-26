"""graphify_lang.cc_kb - harness KB markdown augment (plan 04 S13, D5, D6, D11).

- graphify-lang.toml: ``cc-kb``, kind ``augment`` on ``.md``, [match] ``*.md``,
  narrowed in the augment to ``docs/cc-*.md`` and a harness root's root,
  ``agents/`` and ``skills/`` ``.md`` files
- augment.py: ``augment_cc_kb``, run on top of core ``extract_markdown``, and
  ``watch_cc_kb``, which ``graphify watch`` asks (S5-M2)
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.cc_kb.augment import augment_cc_kb, watch_cc_kb
from graphify_lang.cc_kb.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the cc-kb augment manifest."""
    return load_manifest(__file__, "graphify-lang.toml", augment=augment_cc_kb, resolver=RESOLVER,
                         watch=watch_cc_kb)


__all__ = ["augment_cc_kb", "watch_cc_kb", "RESOLVER", "_get_manifest"]
