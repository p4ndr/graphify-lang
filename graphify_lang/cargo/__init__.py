"""graphify_lang.cargo - Cargo.toml augment (plan 04 S10, D9).

- graphify-lang.toml: ``cargo``, kind ``augment`` on ``.toml``, [match] ``Cargo.toml``
- augment.py: ``augment_cargo``, run on top of core ``extract_package_manifest``
- resolve.py: the cross-file ``RESOLVER`` (registered by the registry)
"""
from __future__ import annotations

from graphify_lang._common import load_manifest
from graphify_lang.cargo.augment import augment_cargo
from graphify_lang.cargo.resolve import RESOLVER
from graphify_lang.manifest import LanguageManifest


def _get_manifest() -> LanguageManifest:
    """Entry point: the cargo augment manifest."""
    return load_manifest(__file__, "graphify-lang.toml", augment=augment_cargo,
                         resolver=RESOLVER)


__all__ = ["augment_cargo", "RESOLVER", "_get_manifest"]
