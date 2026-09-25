# T10 Upstream Proposal - Complete

**Date:** 2026-09-23

## Summary

All T10 upstream proposal tasks have been completed:

| Task | Status | Details |
|------|--------|---------|
| T10.1 | ✅ | `git diff v8...lang-registry -- graphify/` artefact produced |
| T10.2 | ✅ | Issue opened at https://github.com/Graphify-Labs/graphify/issues/3764 |
| T10.3 | ✅ | Cited issues #3180 and #1070 |
| T10.4 | ✅ | `run_language_resolvers` casefold fix in `resolver_registry.py` |
| T10.5 | ✅ | Indefinite carry plan documented in D-002 and D-003 |

## artefact

The upstream proposal artefact is the diff from `v8` to `lang-registry`:

```bash
git diff v8...lang-registry -- graphify/
```

Files changed:
- `graphify/cli.py` - registry integration
- `graphify/detect.py` - registry integration
- `graphify/extract.py` - registry integration + sidecar doc markers
- `graphify/lang_registry.py` - new registry module (84 lines)
- `graphify/resolver_registry.py` - casefix for mixed-case suffixes

Total: 399 insertions, 1263 deletions (extract.py has extensive sidecar doc changes)

## Issue

Issue #3764 opened on Graphify-Labs/graphify:
https://github.com/Graphify-Labs/graphify/issues/3764

The issue includes:
- Problem statement (references #3180 and #1070)
- Proposal for entry-point based plugin system
- Implementation status with the artefact diff
- Key design decisions
- Upstream path

## Verification

- `pytest tests/ -q`: 5468 passed, 12 skipped, 6 warnings
- `guard-core`: PASS (exactly the 5 expected files)
- `guard-tables`: PASS (no hand-added suffixes)

## Carry Plan

**D-002:** Upstream proposal is an ISSUE, not a PR. The fork plans to carry the registry indefinitely — upstreaming is a bonus, and a measured *issue* lands changes more often than a PR. The fork's `lang-registry` branch is the reference implementation.

**D-003:** If upstream accepts this proposal, the fork will rebase onto the accepted implementation and drop its own registry code. Until then, the registry remains in the fork. The AutoLISP plugin (`graphify_lang/autolisp`) is a separate concern and will remain in the fork as a reference implementation.
