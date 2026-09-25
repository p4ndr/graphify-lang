# Upstream state relevant to a plugin/registry layer

What upstream (Graphify-Labs/graphify) already does about plugins and registries, and which of its tests constrain the fork's design.

- Status: FINAL
- Created: 2026-09-21
- Full document: `.claude/docs/cc-RF010.002.md` (425 lines, 6 sections)

## 1. Question

Is a registry layer wanted upstream, what has already been proposed, and what in upstream's test suite constrains how the fork may implement it?

## 2. Findings

Measured 2026-09-08 against upstream head `67f99bd` ("release: 0.9.56"); the fork was 16 commits behind. [VERIFIED]

Constraints that shape the design (full document §6):

| # | Constraint | Consequence |
|---:|---|---|
| 1 | Upstream merged 0 PRs in 60 days (135 of 1,658 ever; 656 open; last merge 2026-07-08) | plan to carry the registry indefinitely; upstreaming is a bonus, and a measured *issue* lands changes more often than a PR |
| 2 | `tests/test_extractors_registry.py:24-38` forbids a plugin extractor in `LANGUAGE_EXTRACTORS` | the manifest `name` must key a separate structure |
| 3 | `test_collect_files_parity_with_legacy_on_fixtures` re-derives the walk from `set(_DISPATCH.keys())` | merge registered suffixes into `_DISPATCH` at import time (issue #1084's shape); `collect_files` stays untouched |
| 4 | `_DISPATCH` must stay a plain mutable dict (6 tests `monkeypatch.setitem` it) | no `MappingProxyType`, no property, no wrapper |
| 5 | Precedent is against suffix stealing: #1084 protects built-in names; `.lsp` is owned by `extract_commonlisp` | override must be explicit, opt-in, and loudly logged |
| 6 | `file_type` is a closed enum (`build.py:856` rewrites the rest to `concept`) | fork node kinds go in `node_kind` with `file_type: "code"` |
| 7 | `relation` is unvalidated and open; `confidence` is the closed part | `dcl_references`, `loads`, `module_depends` etc. need no core change |
| 8 | Cross-file edges need the `target_file` stamp or they drop on incremental runs | `loads`, `sidecar_doc`, `dcl_references` must stamp it; the variable-argument `load_dialog` case stays dangling |
| 9 | `_LANGUAGE_BUILTIN_GLOBALS` is one union across every language | the `vla-`/`vlax-` filter is local to the AutoLISP extractor, never added to the shared union |
| 10 | 324 commits / 30 days on `v8`; ~32% touch `extract.py` or `extractors/` | keep each core lookup to one line next to a stable anchor |
| 11 | `detect.py`, `watch.py`, `cli.py`, `resolver_registry.py` unchanged 0.9.55 → 0.9.56 | only the `extract.py` line citations need the +59/+60 correction |
| 14 | Issue #2851: do not only append suffixes to `CODE_EXTENSIONS` | classification and extraction must land together for `.lsp`, `.dcl`, `.mnl` |
| 16 | PR #2951 (a sibling package, zero core change) sat 17 days unanswered | a zero-core-diff shape is worth considering as the fallback |

## 3. Implications for this repo

1. Roadmap phase 6 (upstream PR) is a Should Have, not a gate — recorded as D-002.
2. Core edits are held to three call sites plus one new file; guard commands in the plan enforce it.
3. Suffix override is explicit and warned; the shipped default is still an open item (P3).

## 4. Sources

`gh` CLI (issues, PRs, search API) plus a local clone of `upstream/v8`, 2026-09-08. Details in `.claude/docs/cc-RF010.002.md`.
