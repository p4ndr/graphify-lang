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

### P15 | Accept that fork and stock graphify evict each other's AST cache when run on the same repo? | 2026-09-24

- Source: T26.1
- Context: After T26.1 (version 0.9.55+lang.1) fork and stock use separate dirs (cache/ast/v0.9.55+lang.1-s2 vs v0.9.55-s2) and never read each other's entries (measured on autolithp src/core/err.lsp: fork 33 nodes, stock 1, alternating runs). But upstream cache._cleanup_stale_ast_entries deletes every sibling v*/ dir on first use, so each side wipes the other's cache: alternating runs re-extract everything. Only a cost, never a wrong result.
- Options: (1) Accept: do nothing — correctness holds, and the owner is unlikely to alternate stock and fork on one repo often (2) Point one side at a different graphify-out (GRAPHIFY_OUT env) when both are used on the same repo — no code change (3) Core edit to graphify/cache.py to skip sweeping +lang dirs — needs a new decision; adds a fifth core file
- Decision: Moot: plan 03 replaced stock graphify with the fork on this host, so only one AST cache writer exists. Reopen if stock graphify is installed again. | 2026-09-25
- Applied to: plan 03 (no action)

### P17 | Mark the plan 01 steps that plan 02 replaced as superseded: T6.2, T6.4, T7.4 (loads/@doc/target_file), T8.2, T8.4 (@include, load)? | 2026-09-24

- Source: T6.2, T6.4, T7.4, T8.2, T8.4
- Context: These ask for artefacts that plan 02 or A6 rejected: tags.scm definition rules and a post_file package_lit join (the walker does both, tested: 27 defuns and err:trap as one node on the real err.lsp), loads/safe-load and @doc anchors (A6 out), DCL regex rules with tile nodes, pop and @include (plan 02 §3: controls are not nodes). module_depends and @sidecar are done. target_file has no reader: graphify/build.py:1217 drops it. defun-q and .mnl fixtures are now done.
- Options: (1) Mark superseded (done), citing plan 02 and A6. Their outcomes are met or deliberately excluded (2) Reopen A6 for loads (15 safe-load sites with computed paths) and/or DCL tiles and @include, as a new plan (3) Keep them open as roadmap
- Decision: Option 1: mark T6.2, T6.4, T7.4, T8.2, T8.4 superseded by plan 02 and A6; their outcomes are met or deliberately excluded. | 2026-09-25
- Applied to: T6.2, T6.4, T7.4, T8.2, T8.4

### P16 | Keep, repair or retire the generic TOML rules runtime (graphify_lang/rules.py, queries.py, regex_rules.py, builtins.py, templates/)? | 2026-09-24

- Source: T5.2, T5.3, T5.4, T5.5, T5.6
- Context: Plan 02 moved AutoLISP and DCL to purpose-built walkers, so nothing calls graphify_lang.rules now. Measured 2026-09-24 with a regex+tags.scm manifest on tests/lang/fixtures/src/core/err.lsp: 27 regex nodes, all with no label/source_file/file_type, 0 query nodes (the query tier fails silently), no file node, 0 edges. That is the case-003 failure mode. The tests/lang/test_rules.py checks for T5 loop over empty lists and prove nothing. The templates are not in package-data, so the wheel does not ship them.
- Options: (1) Retire: delete rules/queries/regex_rules/builtins.py, templates/ and the vacuous tests, then mark T5.2-T5.6 superseded by plan 02. Nothing uses them, and a declarative tier can come back with a real second language to measure against (2) Repair to the S005 emission contract (file node, label/source_file/file_type, _file_stem ids, line suffix on collisions, @reference calls, builtins filter), ship the templates and test on a real regex language such as DCL. Large, and no consumer yet (3) Leave as is and document it as experimental
- Decision: Option 2: repair the regex rules runtime to the S005 emission contract and keep it as a fallback/utility layer; new plugins use their own extractors and may call it. | 2026-09-25
- Applied to: T28, plan 04 D7 and S7, D-008

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
- Note (plan 05 S2.4, M10): `scripts/install-mcp.sh` was deleted; hook suffixes come from the registry (`graphify/cli.py`), so there is no MCP registration step.
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
