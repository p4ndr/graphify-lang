#!/usr/bin/env python3
"""Print the six core tables of SRS §1.1 as sorted JSON (SC2 snapshot).

Regenerate tests/upstream_tables.json from upstream at every rebase, without
switching branches:

    rm -rf /tmp/v8 && mkdir /tmp/v8 && git archive v8 graphify | tar -x -C /tmp/v8
    GRAPHIFY_LANG_DISABLE=1 PYTHONPATH=/tmp/v8 .venv/bin/python \
        scripts/snapshot_tables.py > tests/upstream_tables.json
"""
from __future__ import annotations

import json

import graphify.cli as cli
import graphify.detect as detect
import graphify.extract as extract
import graphify.resolver_registry as resolver_registry
import graphify.watch as watch


def snapshot() -> dict:
    return {
        "_DISPATCH": {k: getattr(v, "__name__", repr(v)) for k, v in sorted(extract._DISPATCH.items())},
        "_EXTRA_FOR_EXTENSION": dict(sorted(extract._EXTRA_FOR_EXTENSION.items())),
        "CODE_EXTENSIONS": sorted(detect.CODE_EXTENSIONS),
        "_WATCHED_EXTENSIONS": sorted(watch._WATCHED_EXTENSIONS),
        "_HOOK_SOURCE_EXTS": sorted(cli._HOOK_SOURCE_EXTS),
        "registered_resolvers": sorted(r.name for r in resolver_registry.registered_resolvers()),
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=1, sort_keys=True))
