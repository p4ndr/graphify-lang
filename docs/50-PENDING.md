<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 50-PENDING.md

This document is a LIVE file containing pending ITEMS.

- `§3` is the pending ITEMS, in priority order.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`pending_add`); hand edits by the owner are fine. They number ITEMS.
- To settle an ITEM: `pending_settle`.
<!-- TEMPLATE-END -->

## 3. ITEMS

### P15 | Accept that fork and stock graphify evict each other's AST cache when run on the same repo? | 2026-09-24

- Source: T26.1
- Context: After T26.1 (version 0.9.55+lang.1) fork and stock use separate dirs (cache/ast/v0.9.55+lang.1-s2 vs v0.9.55-s2) and never read each other's entries (measured on autolithp src/core/err.lsp: fork 33 nodes, stock 1, alternating runs). But upstream cache._cleanup_stale_ast_entries deletes every sibling v*/ dir on first use, so each side wipes the other's cache: alternating runs re-extract everything. Only a cost, never a wrong result.
- Options: (1) Accept: do nothing — correctness holds, and the owner is unlikely to alternate stock and fork on one repo often (2) Point one side at a different graphify-out (GRAPHIFY_OUT env) when both are used on the same repo — no code change (3) Core edit to graphify/cache.py to skip sweeping +lang dirs — needs a new decision; adds a fifth core file

### P16 | Keep, repair or retire the generic TOML rules runtime (graphify_lang/rules.py, queries.py, regex_rules.py, builtins.py, templates/)? | 2026-09-24

- Source: T5.2, T5.3, T5.4, T5.5, T5.6
- Context: Plan 02 moved AutoLISP and DCL to purpose-built walkers, so nothing calls graphify_lang.rules now. Measured 2026-09-24 with a regex+tags.scm manifest on tests/lang/fixtures/src/core/err.lsp: 27 regex nodes, all with no label/source_file/file_type, 0 query nodes (the query tier fails silently), no file node, 0 edges. That is the case-003 failure mode. The tests/lang/test_rules.py checks for T5 loop over empty lists and prove nothing. The templates are not in package-data, so the wheel does not ship them.
- Options: (1) Retire: delete rules/queries/regex_rules/builtins.py, templates/ and the vacuous tests, then mark T5.2-T5.6 superseded by plan 02. Nothing uses them, and a declarative tier can come back with a real second language to measure against (2) Repair to the S005 emission contract (file node, label/source_file/file_type, _file_stem ids, line suffix on collisions, @reference calls, builtins filter), ship the templates and test on a real regex language such as DCL. Large, and no consumer yet (3) Leave as is and document it as experimental

### P17 | Mark the plan 01 steps that plan 02 replaced as superseded: T6.2, T6.4, T7.4 (loads/@doc/target_file), T8.2, T8.4 (@include, load)? | 2026-09-24

- Source: T6.2, T6.4, T7.4, T8.2, T8.4
- Context: These ask for artefacts that plan 02 or A6 rejected: tags.scm definition rules and a post_file package_lit join (the walker does both, tested: 27 defuns and err:trap as one node on the real err.lsp), loads/safe-load and @doc anchors (A6 out), DCL regex rules with tile nodes, pop and @include (plan 02 §3: controls are not nodes). module_depends and @sidecar are done. target_file has no reader: graphify/build.py:1217 drops it. defun-q and .mnl fixtures are now done.
- Options: (1) Mark superseded (done), citing plan 02 and A6. Their outcomes are met or deliberately excluded (2) Reopen A6 for loads (15 safe-load sites with computed paths) and/or DCL tiles and @include, as a new plan (3) Keep them open as roadmap

## 4. RESOLVED ITEMS

### P8 | T15 scope: T14 only or include T13 files? | 2026-09-23

- **Source:** T15
- **Context:** T15 will reconcile duplicate test documentation in docs/testing/. T13 and T14 both cover the autolisp-pvcase test run. Need to know if T13-related files should be included.
- **Options:** 
  1. T14 only — focus on T14-*.md and T14-*.json files
  2. Include T13 — also review T13-related files if they contain relevant duplicate content
- **Resolution:** T14 only — focus on T14-*.md and T14-*.json files
- **Applied to:** T15
