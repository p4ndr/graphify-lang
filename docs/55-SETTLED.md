<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 55-SETTLED.md

This document is a LIVE file containing items that have been settled and are no longer pending.

- `§3` is the settled ITEMS, most recent first.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`pending_settle`); hand edits by the owner are fine.
- To add a pending ITEM: `pending_add`.
<!-- TEMPLATE-END -->

## 3. ITEMS

### P10 | Restore upstream CODE_EXTENSIONS in graphify/detect.py (committed in 84d64c9 without 8 suffixes)? | 2026-09-24

- Source: docs/plans/02-autolisp-extractor-fixes-from-case-003.md §3 (Resolver wiring)
- Context: `git diff v8 -- graphify/detect.py`: the moved CODE_EXTENSIONS line drops .cls .trigger .lisp .cl .lsp .asd .robot .resource that v8 has; .lsp returns only via the registry, the other 7 are no longer detected. Also graphify/extract.py at HEAD differs from v8 by ~1,500 lines of comments replaced with `# @doc extract.md#C…` sidecar markers, so it cannot equal v8 except the registry lookup (plan 02 §3). Found during T22; not changed.
- Options: (1) Restore both files to v8 plus only the registry try-blocks (keeps README goal 1 and the upstream-proposal diff small) (2) Keep as is and document the divergence
- Decision: Option 1, partial: restore graphify/detect.py to v8 plus only the registry lookup (brings back the 7 dropped suffixes). Keep the @doc sidecar markers in graphify/extract.py. | 2026-09-24
- Applied to: T26.2, D-004

### P9 | How should the fork stop sharing the AST cache with stock graphify 0.9.55 (D11)? | 2026-09-24

- Source: T24.2
- Context: graphify/cache.py:956 keys AST entries only by content hash under cache/ast/v{graphifyy version}-s{schema}; fork and stock both report 0.9.55, so they read each other's entries. load_cached runs before dispatch (extract.py:5461, 5719) and has no per-extractor hook, so a registry-only key is impossible; any fix edits cache.py. Measured side effect: the fork's own tests used to write into this repo's graphify-out/cache (now given cache_root=tmp_path).
- Options: (1) Fork version string: give the fork a distinct package version (e.g. 0.9.55+lang.1) so _EXTRACTOR_VERSION differs; no code edit, but stock and fork then sweep each other's version dir (cleanup) when sharing one graphify-out (2) Core edit in cache.py: add an optional per-suffix salt (registry-provided plugin name+version) to the AST hash key; propose upstream with the registry issue (3) Accept: document never to share graphify-out between stock and fork
- Decision: Option 1: give the fork a distinct package version (0.9.55+lang.1) so its AST cache dir differs from stock. Owner accepts that this replaces the old 'do not touch pyproject version' rule. | 2026-09-24
- Applied to: T26.1, T24.2, D-007

### P1 | Should T13.1 proceed to T14 review, or are there concerns about the autolisp-pvcase repo or test plan? | 2026-09-23

- Source: T13.1
- Context: T13.1 requires reviewing T14 and confirming ability to find/read all referenced source code and documents. T14 depends on ~/repos/autolisp-pvcase/ repo and docs/testing/case_001_autolisp-pvcase.md.
- Options: (1) Proceed to T14 review (2) Pause - have concerns about autolisp-pvcase repo (3) Pause - need clarification on test plan
- Decision: T14 review completed - autolisp-pvcase repo reviewed as INPUT for graphify-lang testing | 2026-09-23
- Applied to: T13.1, T14

### P7 | Should I proceed with T14.7 (add suggestions) before T14.2-T14.6 are complete? | 2026-09-23

- Source: T14.7
- Context: T14.7 depends on T14.2-T14.6 being complete. The suggestions are based on test results which require the prior steps.
- Options: (1) Wait for T14.2-T14.6 first (2) Proceed with T14.7 preparation now
- Decision: Proceed with T14.7 after T14.2-T14.6 are complete | 2026-09-23
- Applied to: T14.7

### P6 | Should I proceed with T14.6 (summarize test results) before T14.2-T14.5 are complete? | 2026-09-23

- Source: T14.6
- Context: T14.6 depends on T14.2-T14.5 being complete. These are sequential steps in the test workflow.
- Options: (1) Wait for T14.2-T14.5 first (2) Proceed with T14.6 preparation now
- Decision: Proceed with T14.6 after T14.2-T14.5 are complete | 2026-09-23
- Applied to: T14.6

### P5 | Should I proceed with T14.5 (run searches and update test results) before T14.2-T14.4 are complete? | 2026-09-23

- Source: T14.5
- Context: T14.5 depends on T14.2 (test cases), T14.3 (graphify-lang config), and T14.4 (scan) being complete. These are sequential steps.
- Options: (1) Wait for T14.2-T14.4 first (2) Proceed with T14.5 preparation now
- Decision: Proceed with T14.5 after T14.2-T14.4 are complete | 2026-09-23
- Applied to: T14.5

### P4 | Should I proceed with T14.4 (scan autolisp-pvcase with graphify-lang) before T14.2/T14.3 are complete? | 2026-09-23

- Source: T14.4
- Context: T14.4 depends on T14.2 (test case creation) and T14.3 (graphify-lang configuration) being complete. These are sequential steps in T14.
- Options: (1) Wait for T14.2/T14.3 first (2) Proceed with T14.4 preparation now
- Decision: Proceed with T14.4 after T14.2/T14.3 are complete | 2026-09-23
- Applied to: T14.4

### P3 | Should I proceed to implement T14.3 (replace graphify with graphify-lang in autolisp-pvcase repo) before P2 is settled? | 2026-09-23

- Source: T14.3
- Context: T14.3 depends on T14.2 being complete. P2 (T14.2 blocker) asks whether to create 20 test cases. If yes, T14.3 requires modifying the autolisp-pvcase repo's configuration.
- Options: (1) Wait for P2 settlement first (2) Proceed with T14.3 preparation now
- Decision: Proceed with T14.3 after T14.2 is complete | 2026-09-23
- Applied to: T14.3

### P2 | Should I proceed to create docs/testing/case_001_autolisp-pvcase.md with 20 test cases for graphify-lang? | 2026-09-23

- Source: T14.2
- Context: T14.2 requires creating test cases for graphify-lang against ~/repos/autolisp-pvcase. I have reviewed the repo structure, source files (18 .lsp modules), test fixtures, and the test harness. The existing case template is at docs/testing/case_001-autolisp-pvcase.md.
- Options: (1) Proceed with 20 test cases (2) Pause - need clarification on test scope (3) Pause - have concerns about test feasibility
- Decision: Proceed with T14.2 - create docs/testing/case_001_autolisp-pvcase.md with 20 test cases for graphify-lang | 2026-09-23
- Applied to: T14.2, T14.3, T14.4, T14.5, T14.6, T14.7

### `[S]` P1 | SRS §1.4, F18.1 — Which build do the agents reach (installed hook, MCP server)?

**Settled:** 2026-09-21

- Owner answer: The fork uses `uv` for development (`.venv`), not the pipx venv. MCP registration is a manual step via `scripts/install-mcp.sh --help`.
- Item source: `cc-RS000.001.md` §1.4 Q7; `cc-IP000.001.md` §S009 Q7.

### `[S]` P2 | SRS §1.4, F18.2 — Is the global `.lsp` claim an accepted loss?

**Settled:** 2026-09-21

- Owner answer: The global `.lsp` claim in the shipped entry-point stanza is acceptable. Development and tests discover the plugin through `GRAPHIFY_LANG_PATH`, which is deterministic and needs no packaging.
- Item source: `cc-RS000.001.md` §1.4 Q8; `cc-IP000.001.md` §S009 Q8.

### `[S]` P3 | SRS §1.4, F18.3 — Should the fork ship `overrides = ['.lsp']` in the default entry-point stanza?

**Settled:** 2026-09-21

- Owner answer: No override is shipped by default. Users who want AutoLISP to override the built-in CommonLISP extractor must explicitly set `overrides = ['.lsp']` in their `graphify_lang.toml`.
- Item source: `cc-RS000.001.md` §1.4 Q9; `cc-IP000.001.md` §S009 Q9.

### `[S]` P4 | SRS §1.4, F19 — Should the upstream proposal be a PR or an ISSUE?

**Settled:** 2026-09-22

- Owner answer: ISSUE, not PR. The fork plans to carry the registry indefinitely — upstreaming is a bonus, and a measured *issue* lands changes more often than a PR.
- Item source: `cc-RS000.001.md` §1.4 F19; `cc-IP000.001.md` §S010.
- Resolution: Issue #3764 opened on Graphify-Labs/graphify with the artefact `git diff v8...lang-registry -- graphify/`.

### `[S]` P5 | SRS §1.4, F25 — Should the fork edit existing language extractors?

**Settled:** 2026-09-21

- Owner answer: No. The fork follows the rule: never edit an existing language extractor, `graphify/extractors/engine.py`, or `graphify/extractors/resolution.py`.
- Item source: `cc-RS000.001.md` §1.4 F25.

### `[S]` P6 | SRS §1.4, F26 — Should the fork add a `graphify lang list` subcommand?

**Settled:** 2026-09-21

- Owner answer: No. The registry's own log line ships instead. The `graphify lang list` subcommand would be a fourth core edit; the registry's own log line is a Should Have, not a Must Have.
- Item source: `cc-RS000.001.md` §1.4 F26.

### P7-P13 | Should the fork add a `graphify lang list` subcommand? (7 duplicate legacy entries, SRS F26 / F18.4-F18.10) | 2026-09-24

- Decision: Yes, add it (owner, 2026-09-24). Reverses plan 01 §2 out-of-scope note.
- Applied to: T26.3; D-006

### P14 | T15 scope: T14 only or include T13 files? | 2026-09-24

- Decision: already resolved as "T14 only" (duplicate of resolved P8); removed from open items.
- Applied to: T15
