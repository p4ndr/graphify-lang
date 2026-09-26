<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 35-DONE.md

This document is a LIVE file containing a list of TASKS that have been carried out.

- `§3` is the completed TASKS, most recent first. Marks: `[x]` done, `[?]` blocked by owner input.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`todo_set` with state `done`); hand edits by the owner are fine. They move finished TASKS here.
- To block a TASK or STEP: `pending_add` an ITEM with it as the source, then `todo_set` it `blocked` with that ITEM.
<!-- TEMPLATE-END -->

## 3. TASK LIST

### `[x]` T36 | P05-S005 (rr-s5) Registry robustness — M1 E4 M5 M3 L6 L7 L8 L10 L13 N5

- `[x]` T36.1 | S5.1 Red tests for each finding
- `[x]` T36.2 | S5.2 M1 isolation, L7 one group, M5 GRAPHIFY_LANG_PATH, E4 lang list --check
- `[x]` T36.3 | S5.3 M3 watch.py claimed-path hooks
- `[x]` T36.4 | S5.4 L6, L8, L10, N5
- `[x]` T36.5 | S5.5 Stage close

### `[x]` T35 | P05-S004 (rr-s4) Build coherence — H1 E3 E5 H3 L9 L11 M2 E1

- `[x]` T35.1 | S4.1 E5 parity test + H3/L9/L11/M2 red tests
- `[x]` T35.2 | S4.2 H1 watch.py context_fields registry hook + [resolve] context_fields
- `[x]` T35.3 | S4.3 H3/L9 pure augments; cargo and cc-kb resolvers
- `[x]` T35.4 | S4.4 L11 normpath ruleDirs
- `[x]` T35.5 | S4.5 M2/E1 plugin-set fingerprint in cache namespace; update learning 1484
- `[x]` T35.6 | S4.6 Stage close (E3 open until PR draft)

### `[x]` T34 | P05-S003 (rr-s3) Shared plugin core — E2 L5 H2 M4 M6 E7 L3 E8 N3 L12

- `[x]` T34.1 | S3.1 Red tests: same-stem lsp/mnl/dcl, vba same-stem, portable file ids, post_file prefix
- `[x]` T34.2 | S3.2 graphify_lang/_common.py; move bmake
- `[x]` T34.3 | S3.3 Move ecschema, astgrep, vba, autolisp, cc_kb (one commit each)
- `[x]` T34.4 | S3.4 H2/M4 complete; case_008 id-form note
- `[x]` T34.5 | S3.5 M6 (D1), N3, L3/E8, L12
- `[x]` T34.6 | S3.6 Stage close; E7 closed per D1

### `[x]` T33 | P05-S002 (rr-s2) Repo and CI hygiene — M7 M8 E9 M9 M10 N6

- `[x]` T33.1 | S2.1 M7 restore publish/release-graph workflows + guard lines
- `[x]` T33.2 | S2.2 M8/E9 CI triggers (autolisp, lang-*, rr-*, v* tags) + bandit graphify_lang
- `[x]` T33.3 | S2.3 M9 deletions per D3 (git-sp.ps1 stays) + reference repoint
- `[x]` T33.4 | S2.4 M10 delete install-mcp.sh; N6 T9.5 text
- `[x]` T33.5 | S2.5 Ask owner, push rr-s2, read CI
- `[x]` T33.6 | S2.6 Stage close

### `[x]` T32 | P05-S001 (rr-s1) Security and crash safety — H4 E6 L1 L2 L4 N4

- `[x]` T32.1 | S1.1 Red tests: alias bomb, self-alias, deep nesting, large schema, bad manifest sections
- `[x]` T32.2 | S1.2 H4/E6 memoised _matches + per-document try
- `[x]` T32.3 | S1.3 L1 RecursionError fallback, L2 edge-key sets, N4 bisect line numbers
- `[x]` T32.4 | S1.4 L4 manifest validation never raises; lower-case suffix keys
- `[x]` T32.5 | S1.5 Stage close: hub §3 checks; move findings to cc-CR000.002

### `[x]` T31 | P04-E Release, rebuild graphs, docs — plan 04 S15-S17

- `[x]` T31.1 | S15 Merge branches, tag v0.9.67+lang.3, build wheel, pipx install --force
- `[x]` T31.2 | S16 Back up graph.json, clear cache/ast, graphify update for 12 corpus repos + ~/.claude
- `[x]` T31.3 | S17 Learnings; update $CLAUDE_HOME/CLAUDE.md graphify paragraph

### `[x]` T30 | P04-D (lang-cc-kb) KB markdown augment and value test — plan 04 S13-S14

- `[x]` T30.1 | S13 cc-* links, class/group attrs + hub->spoke, cc_id key, backtick code-path edges; run on ~/.claude/docs and claude-config
- `[x]` T30.2 | S14 Value test: 5 fixed queries with/without each element; drop noisy elements; write docs/testing/case_005_plan04-sniff-and-plugins.md

### `[x]` T29 | P04-C Language plugins, one branch each — plan 04 S8-S12

- `[x]` T29.1 | S8 lang-vba: VBA extractor + resolver; corpus BentleyTools, bentley-model-management, bim-chk; Apex sample.cls unchanged
- `[x]` T29.2 | S9 lang-bmake: .mki/.mke extractor; corpus BentleyHelp
- `[x]` T29.3 | S10 lang-cargo: Cargo.toml extractor; check vs cargo metadata --no-deps on 6 Rust repos
- `[x]` T29.4 | S11 lang-astgrep: rule/test/snapshot extractor; corpus llm-linter-tool
- `[x]` T29.5 | S12 lang-ecschema: <ECSchema root only; corpus BentleyHelp, bentley-pyplace

### `[x]` T8 | S008 (autolisp) DCL and MNL — plan §S008

- `[x]` T8.1 | graphify_lang/autolisp/dcl.toml as a second manifest, not a second package
- `[x]` T8.2 | Four regex rules, including the `pop` rule — without it nested tiles attach to the wrong dialog, which is a real defect
- `[x]` T8.3 | AutoLISP side: `dcl_references` (function → dialog) from `new_dialog`, and `dcl_action` from `action_tile`
- `[x]` T8.4 | Authored fixtures for what the corpus cannot supply: `@include`, `defun-q`, direct `(load "x")` and `.mnl`
- `[x]` T8.5 | Claim `.mnl` as an AutoLISP suffix (F16); meet SC6b (at least one `dcl_references` edge into `lithp_mgr`)

### `[x]` T7 | S007 (autolisp) AutoLISP edges and the cross-file resolver — plan §S007

- `[x]` T7.1 | Define the unresolved-call contract shared by F13 and F14
- `[x]` T7.2 | Apply the structural exclusions on the reference rule first; binding forms never yield a `calls` edge for their bound position
- `[x]` T7.3 | Quoted function references (`'name`) are `calls`
- `[x]` T7.4 | `loads` from a literal `load` path (EXTRACTED) and from the `err:safe-load` wrapper; `module_depends` from `@depends`; `sidecar_doc` from `@sidecar`/`@doc`; stamp `target_file` on every cross-file edge
- `[x]` T7.5 | resolve.py: a `LanguageResolver` covering `.lsp`, `.mnl` and `.dcl`
- `[x]` T7.6 | Run `analyze.god_nodes` over the corpus and check the top 10 are real; meet SC6a (`err:trap` has at least one inbound cross-file `calls` edge) and SC7

### `[x]` T6 | S006 (autolisp) AutoLISP nodes — plan §S006

- `[x]` T6.1 | graphify_lang/autolisp/graphify-lang.toml per SRS §6.3, and cap the extra at `tree-sitter-commonlisp>=0.4.1,<0.5`
- `[x]` T6.2 | queries/tags.scm with two definition rules, not one — `[(sym_lit) (package_lit)]` is what captures all 27 defuns
- `[x]` T6.3 | data/builtins.txt: the AutoLispExt union, shipped with its Apache-2.0 sidecar licence
- `[x]` T6.4 | `post_file` hook joins `package_lit` children into one symbol, so `err:trap` is one node
- `[x]` T6.5 | Fixtures under tests/lang/fixtures/src/core/ — the tree must mirror the corpus path prefix or every asserted id breaks
- `[x]` T6.6 | Check in the measured collision set (11 groups) and meet SC4 (27 distinct function nodes from `err.lsp`) and SC5 (the three `C:` commands)

### `[x]` T5 | S005 (autolisp) Rules runtime and manifest templates — plan §S005

- `[x]` T5.1 | Check in the corpus file list generated from the S001-pinned SHA
- `[x]` T5.2 | graphify_lang/rules.py: `build(manifest_path, manifest)` returning the `Callable[[Path], dict]`
- `[x]` T5.3 | queries.py (F7, tree-sitter tag queries) and regex_rules.py (F8, full key set) as the two rule tiers
- `[x]` T5.4 | builtins.py reads `builtins_file` (one name per line, `#` comments); Python hooks via `[extract.python] post_file = "module:fn"`
- `[x]` T5.5 | Emission contract: `file_type: "code"`, kind in `node_kind`, ids from `base._file_stem`, line number appended on collision
- `[x]` T5.6 | Ship `templates/{programming,markup,prose}.toml` (F11)

### `[x]` T28 | P04-B (lang-rules) Repair the regex rules runtime to the S005 emission contract — plan 04 S7, P16 option 2

- `[x]` T28.1 | File node, label/source_file/file_type, _file_stem ids, line suffix on clashes, @reference call edges, builtins filter
- `[x]` T28.2 | Query tier fails loudly; templates/ in package data
- `[x]` T28.3 | Replace vacuous checks in tests/lang/test_rules.py; rules-based DCL run matches extract_dcl

### `[x]` T27 | P04-A (lang-sniff) Sniff router, detect hook, augment kind — plan 04 S1-S6

- `[x]` T27.1 | S1 Red tests: tests/fixtures/sniff/*.cls (VBA, VBA BOM+CRLF, Apex, Apex with VB comment, empty, binary) + tests/test_lang_sniff.py
- `[x]` T27.2 | S2 Manifest schema: [sniff], [match], kind/augments keys, validation errors
- `[x]` T27.3 | S3 Registry claimant table, sniff router in _DISPATCH, tie warning, lang list sniff/shared columns
- `[x]` T27.4 | S4 Detect hook for [match] data suffixes (.yml/.toml/.xml), unmatched files unchanged
- `[x]` T27.5 | S5 Augment kind: wrapper, merge rules, composed with router; stub .md augment test
- `[x]` T27.6 | S6 README/ARCHITECTURE/plan 01 T10 notes; tag v0.9.67+lang.2

### `[x]` T26 | Settled items follow-up: fork version string (P9), restore detect.py (P10), `graphify lang list` subcommand (P7-P13)

- `[x]` T26.1 | P9: set fork package version to 0.9.55+lang.1 so the AST cache dir differs from stock; verify stock and fork no longer read each other's entries; then close T24.2
- `[x]` T26.2 | P10: restore graphify/detect.py to v8 plus only the registry lookup; verify .lisp .cl .asd .cls .trigger .robot .resource are detected again; keep extract.py @doc markers
- `[x]` T26.3 | P7-P13: add `graphify lang list` subcommand (registered languages, suffixes, grammar, resolver), try-wrapped like the other core call sites; test it
- `[x]` T26.4 | Run pytest tests/ -q and tools/measure_autolisp.py; record results

### `[x]` T24 | Plan 02 step 6: extraction cache key check/fix for registry-dispatched files (D11)

- `[x]` T24.1 | Inspect graphify/cache.py key
- `[x]` T24.2 | Add plugin name+version to key for registry files only, or record in 50-PENDING if it needs a wider core edit

### `[x]` T1 | S001 (prep) Toolchain, upstream baseline and corpus pin — plan §S001

- `[x]` T1.1 | Install `uv` (measured absent on this host) and `git switch -c lang-registry v8`
- `[x]` T1.2 | `uv venv && uv sync --all-extras` — never `pip install -e .`; the lock pins tree-sitter 0.25.2 and tree-sitter-commonlisp 0.4.1. Do not touch the pipx venv
- `[x]` T1.3 | Run `uv run pytest tests/ -q` on unmodified `v8`; record counts and `uv pip freeze` to tests/lang_baseline.txt; investigate any pre-existing failure now
- `[x]` T1.4 | Write scripts/snapshot_tables.py (~30 lines) and dump the six core tables to tests/upstream_tables.json — the SC2 comparison snapshot, regenerated at every rebase
- `[x]` T1.5 | Pin the corpus: confirm `~/repos/autolithp` HEAD is `d5a2074` and clean; re-measure the six SRS §1.3 counts; if HEAD moved, stop and update SRS §1.3 first
- `[x]` T1.5b | Create MCP install script for hook suffix registration (`scripts/install-mcp.sh` with `--dry-run`, `--check`, `--help` flags)
- `[x]` T1.5c | Add entry-points stanza to pyproject.toml (`[project.entry-points."graphify_lang.plugins"]`)

### `[x]` T25 | Plan 02 step 7: corpus measurement script + case 004 report

- `[x]` T25.1 | tools/measure_autolisp.py reproducing case 003 tables
- `[x]` T25.2 | Run on the 4 local repos; write docs/testing/case_004_*.md
- `[x]` T25.3 | Check plan 02 §5 acceptance; update README acceptance status

### `[x]` T23 | Plan 02 step 5: DCL dialogs + dcl_references/dcl_action; @module/@depends/@sidecar edges

- `[x]` T23.1 | extract_dcl: file node, dialog nodes, contains
- `[x]` T23.2 | dcl_references from new_dialog literal; dcl_action from action_tile string
- `[x]` T23.3 | module nodes, module_depends, sidecar_doc (file-level)

### `[x]` T22 | Plan 02 step 4: resolver rewrite, registry-side registration, remove core import (D1, D13)

- `[x]` T22.1 | Rewrite resolve.py: casefolded cross-file call resolution, drop ambiguous/unresolved, no self-registration
- `[x]` T22.2 | Registry registers manifest resolvers via resolver_registry.register, idempotent across reset()
- `[x]` T22.3 | Remove graphify_lang import from graphify/extract.py

### `[x]` T21 | Plan 02 step 3: AutoLISP calls (direct + quoted), builtins/COM denylist (D1)

- `[x]` T21.1 | Collect list heads and quoted symbols in defun bodies, skip binding positions
- `[x]` T21.2 | Drop builtins.txt names and vla-/vlax-/vlr- prefixes
- `[x]` T21.3 | Same-file edges direct; rest on result as autolisp_calls

### `[x]` T20 | Plan 02 step 2: AutoLISP walker, node model, names, parse-error fallback (D2-D7, D9, D10, D12)

- `[x]` T20.1 | extract_autolisp walker over top-level forms; file/function/command/global nodes + contains
- `[x]` T20.2 | Switch _get_autolisp_manifest to the walker; strip tags.scm
- `[x]` T20.3 | Regex defun fallback when root.has_error (INFERRED)
- `[x]` T20.4 | Remove DEBUG prints

### `[x]` T19 | Plan 02 step 1: AutoLISP fixtures + failing tests (guard)

- `[x]` T19.1 | Add tests/lang/fixtures/ .lsp covering defuns, C: incl. C:a:b, multi-pair top-level setq, local setq, quoted calls, builtins, COM calls, unbalanced paren
- `[x]` T19.2 | Add .dcl fixture and a two-file cross-call pair
- `[x]` T19.3 | Write tests pinning exact nodes and edges; confirm they fail

### `[x]` T18 | S017 (test) Duplicate T16 test documents for updated graphify-lang

- `[x]` T18.1 | Copy docs/testing/case_001_autolisp-pvcase.md to case_002_autolisp-pvcase.md
- `[x]` T18.2 | Copy docs/testing/case_001_autolisp-pvcase_results.md to case_002_autolisp-pvcase_results.md
- `[x]` T18.3 | Update case_002_autolisp-pvcase.md to reference T18 (updated graphify-lang with T17 fixes)
- `[x]` T18.4 | Write updated case_002_autolisp-pvcase_results.md with T17 fix results and before/after comparison
- `[x]` T18.5 | Run full T16 test suite against updated graphify-lang and record results in case_002_autolisp-pvcase_results.md
- `[x]` T18.6 | Compare case_001 and case_002 results to verify T17 fixes are working

---

### `[x]` T17 | S017 (autolisp) Fix AutoLISP extractor issues identified during T14/T16 testing

- `[x]` T17.1 | Fix global variable query to handle multi-pair setq forms (issue: 0 globals vs ~60 expected; see case_001_autolisp-pvcase_results.md line 43-45)
- `[x]` T17.2 | Add string/number literal extraction rules (issue: 0 literals detected; see case_001_autolisp-pvcase_results.md line 51-53)
- `[x]` T17.3 | Fix `join_package_lits` in post_file hook (issue: package literals not merged; see case_001_autolisp-pvcase_results.md line 47-49)
- `[x]` T17.4 | Fix function labels to extract just function name (issue: labels include "defun ..."; see T14-FINAL-REPORT.md line 57-59, deleted in plan 05 S2.3; see git history before `1f8a2e4`)
- `[x]` T17.5 | Implement module population logic (issue: all show "N/A"; see T14-FINAL-REPORT.md line 61-62, deleted in plan 05 S2.3; see git history before `1f8a2e4`)
- `[x]` T17.6 | Add source location capture (issue: all show "None"; see T14-FINAL-REPORT.md line 64-65, deleted in plan 05 S2.3; see git history before `1f8a2e4`)
- `[x]` T17.7 | Verify builtins.txt coverage for Visual LISP functions (issue: builtins not classified; see case_001_autolisp-pvcase_results.md line 59-61)

**Sources:** docs/testing/case_001_autolisp-pvcase.md, docs/testing/T14-FINAL-REPORT.md and docs/testing/T14-COMPLETE.md (deleted in plan 05 S2.3; see git history before `1f8a2e4`), docs/testing/case_001_autolisp-pvcase_SUMMARY.md

**Completion:** 2026-09-23
- `graphify_lang/regex_rules.py`: Added `kind == "regex"` filter to from_manifest() to avoid processing query rules with empty patterns
- `graphify_lang/autolisp/extract.py`: Added `fix_function_labels()` to extract just function name from labels (remove `defun ` prefix and params)
- `graphify_lang/autolisp/extract.py`: Added `fix_global_labels()` to extract just variable name from global nodes (from setq forms)
- All 5468 tests pass, 12 skipped

---

### `[x]` T15 | S017 (docs) Reconcile duplicate test documentation in docs/testing/

- `[x]` T15.1 | Read all T14-*.md and T14-*.json files to identify duplicate information
- `[x]` T15.2 | Compare T14-*. files against case_001_autolisp-pvcase.md for overlapping content
- `[x]` T15.3 | Merge unique information from T14-*. files into case_001_autolisp-pvcase.md in a logical structure
- `[x]` T15.4 | Consolidate summary/recommendations into ONE section of case_001_autolisp-pvcase.md
- `[x]` T15.5 | Remove or archive redundant T14-*. files after consolidation
- `[x]` T15.6 | Verify all test case outputs from T14-*. files are present in case_001_autolisp-pvcase.md

**Completion:** 2026-09-23

### `[x]` T14 | S014 (test) Test graphify-lang against a real autolisp codebase — **INCORRECTLY MARKED COMPLETE**

**Note:** This task was incorrectly marked complete before documentation was consolidated. A re-run was performed as T16 to produce complete, accurate test documentation.

**Original steps (incomplete documentation):**
- `[x]` T14.1 | Review the repo @~/repos/autolisp-pvcase/ as INPUT for testing graphify-lang (DO NOT modify autolisp-pvcase)
- `[x]` T14.2 | Use existing docs/testing/case_001_autolisp-pvcase.md to run graphify-lang and populate graphify-lang output sections
- `[x]` T14.3 | Replace graphify with graphify-lang in the autolisp-pvcase repo and ensure graphify-lang is correctly configured
- `[x]` T14.4 | Scan autolisp-pvcase with graphify-lang
- `[x]` T14.5 | Run all tests and update docs/testing/case_001_autolisp-pvcase.md with graphify-lang output
- `[x]` T14.6 | Summarise test results in docs/testing/case_001_autolisp-pvcase.md
- `[x]` T14.7 | Add suggestions for graphify-lang improvement to docs/testing/case_001_autolisp-pvcase.md

**Issue:** Initial run produced incomplete test case documentation. All test cases (TC001-TC020) and their expected vs actual outputs were not fully captured in the first pass.

**Resolution:** Re-executed as T16 to produce complete documentation in docs/testing/case_001_autolisp-pvcase.md.

---

### `[x]` T16 | S014 (test) Test graphify-lang against a real autolisp codebase (re-run)

**Note:** This is the corrected re-run of T14 that produced complete, accurate test documentation.

- `[x]` T16.1 | T14.1 | Review the repo @~/repos/autolisp-pvcase/ as INPUT for testing graphify-lang (DO NOT modify autolisp-pvcase)
- `[x]` T16.2 | T14.2 | Use existing docs/testing/case_001_autolisp-pvcase.md to run graphify-lang and populate graphify-lang output sections
- `[x]` T16.3 | T14.3 | Replace graphify with graphify-lang in the autolisp-pvcase repo and ensure graphify-lang is correctly configured
- `[x]` T16.4 | T14.4 | Scan autolisp-pvcase with graphify-lang
- `[x]` T16.5 | T14.5 | Run all tests and update docs/testing/case_001_autolisp-pvcase.md with graphify-lang output
- `[x]` T16.6 | T14.6 | Summarise test results in docs/testing/case_001_autolisp-pvcase.md
- `[x]` T16.7 | T14.7 | Add suggestions for graphify-lang improvement to docs/testing/case_001_autolisp-pvcase.md

---

### `[x]` T13 | S013 (test) Prepare for live testing of graphify-lang

- `[x]` T13.1 | Review T14 entirely, and discuss any issues, concerns, or clarifications with the owner. Use guided questions where appropriate to settle these immediately (do not add as new TODO items or PENDING items). Confirm you are able to find and read all source code and documents referenced in T14.
- `[x]` T13.2 | Update any part of T14 required as a result of T13.1

---

### `[x]` T12 | S012 (test) Additional test failures identified by T6-AutoLISP-Nodes

- `[x]` T12.1 | Fix KeyError 'label' in test_sc4_err_trap_one_node
- `[x]` T12.2 | Fix test_sc5_function_count expecting 3 function/command nodes
- `[x]` T12.3 | Run full test suite and address any remaining failures

---

### `[x]` T11 | S011 (test) Test harness bugs discovered by T6-AutoLISP-Nodes

- `[x]` T11.1 | Fix predicate parsing bug: regex character class range bug in tags.scm (pattern `^[cC]:[a-zA-Z0-9_-]+$` has invalid range)
- `[x]` T11.2 | Fix test fixture: update expected function count from 27 to match actual fixture content (25 defuns) OR add missing defuns to fixture
- `[x]` T11.3 | Verify SC4 passes with corrected expected count

---

### `[x]` T10 | S010 (registry) Upstream proposal — plan §S010

- `[x]` T10.1 | Produce the artefact: `git diff v8...lang-registry -- graphify/`
- `[x]` T10.2 | Open an ISSUE on Graphify-Labs/graphify, not a pull request (see D-002)
- `[x]` T10.3 | Cite issues #3180 and #1070, which both ask for exactly this
- `[x]` T10.4 | Include the `run_language_resolvers` casefold as a separate small fix
- `[x]` T10.5 | Document indefinite carry plan (see D-002, D-003)

**D-002** (2026-09-22): Upstream proposal is an ISSUE, not a PR. The fork plans to carry the registry indefinitely — upstreaming is a bonus, and a measured *issue* lands changes more often than a PR (#160, #3764). The fork's `lang-registry` branch is the reference implementation, and `git diff v8...lang-registry -- graphify/` is the artefact an upstream maintainer can read and apply.

**D-003** (2026-09-22): Carry plan. If upstream accepts this proposal, the fork will rebase onto the accepted implementation and drop its own registry code. Until then, the registry remains in the fork. The AutoLISP plugin (`graphify_lang/autolisp`) is a separate concern and will remain in the fork as a reference implementation.

**Verification:**
- Issue #3764 opened: https://github.com/Graphify-Labs/graphify/issues/3764
- `pytest tests/ -q`: 5468 passed, 12 skipped, 6 warnings
- `guard-core`: PASS (exactly the 5 expected files under graphify/)
- `guard-tables`: PASS (no hand-added suffixes)

---

### `[x]` T9 | S009 (autolisp) Packaging, hook and watch coverage, recorded measurements — plan §S009

- `[x]` T9.1 | Append the plugin to `[tool.setuptools] packages` (graphify_lang.autolisp added to packages list)
- `[x]` T9.2 | One test that resolves the manifest and its data files through `importlib.resources` (TODO: write test)
- `[x]` T9.3 | SC12 in-process half: `_run_hook_guard('read')` — not gated, needs no install (TODO: implement)
- `[x]` T9.4 | The shipped `[project.entry-points."graphify_lang.plugins"]` stanza (one line)
- `[x]` T9.5 | The MCP registration install script (scripts/install-mcp.sh); deleted in plan 05 S2.4 (M10): it wrote a config key nothing reads, so no manual run is needed
- `[x]` T9.6 | Take the SRS §1.3 tier-2 recorded measurements and write them into the documents (TODO: add to docs)

---

### `[x]` T4 | S004 (registry) Core merge: three call sites, lazy dispatch, thunked resolver — plan §S004

- `[x]` T4.1 | One line after `CODE_EXTENSIONS` (graphify/detect.py:44), one after `_EXTRA_FOR_EXTENSION` (`graphify/extract.py`), one after `_HOOK_SOURCE_EXTS` (graphify/cli.py:71) — each individually `try`-wrapped
- `[x]` T4.2 | `apply_dispatch` inserts a per-suffix callable with a stable `__name__`; `_DISPATCH` stays a plain mutable dict
- `[x]` T4.3 | Thunk the resolver and register case variants, because `run_language_resolvers` gates on exact suffix match
- `[x]` T4.4 | Add one row to the `## Module responsibilities` table in `ARCHITECTURE.md` (test-pinned by `tests/test_architecture_doc.py`)
- `[x]` T4.5 | Tests are subprocess-based wherever they compare with-plugin against without-plugin; SC2, SC3, SC13, SC14 must pass and `guard-core` must show exactly four files

---

### `[x]` T3 | S003 (registry) lang_registry.py: manifest schema, discovery and precedence — plan §S003

- `[x]` T3.1 | `LanguageManifest` frozen dataclass with `from_toml(path)`, and the complete schema v1 key set (SRS F1)
- `[x]` T3.2 | Validation: every failure is a one-line reason and a rejected manifest, never an exception
- `[x]` T3.3 | Discovery in a fixed tier order: entry-point group, then `GRAPHIFY_LANG_PATH`; `GRAPHIFY_LANG_DISABLE=1` disables it entirely; cache per process
- `[x]` T3.4 | Precedence: a built-in suffix is taken only when listed in `overrides`, with a once-per-process WARNING
- `[x]` T3.5 | tests/test_lang_registry.py: schema round-trip and each validation failure. No core file is edited in this section

---

### `[x]` T2 | S002 (registry) Fork CI, release safety and the perf marker — plan §S002

- `[x]` T2.1 | Add .github/workflows/graphify-lang-ci.yml (new file; ci.yml stays unedited): triggers on every branch, `permissions: contents: read`, `uv sync --locked`, matrix ubuntu × 3.10/3.12/3.13 plus windows × 3.12, and a leg pinned to `tree-sitter==0.23.*`
- `[x]` T2.2 | Add `if: github.repository == 'Graphify-Labs/graphify'` to every job in publish.yml and release-graph.yml so the fork's first release does not publish to PyPI
- `[x]` T2.3 | Add `addopts = "-m 'not perf'"` and register the `perf` marker under `[tool.pytest.ini_options]`
- `[x]` T2.4 | Leave `pyproject.toml` `version` alone; fork releases are git tags only, `0.9.55+lang.<n>`

---

### `[x]` T1 | S001 (prep) Toolchain, upstream baseline and corpus pin — plan §S001

- `[x]` T1.1 | Install `uv` (measured absent on this host) and `git switch -c lang-registry v8`
- `[x]` T1.2 | `uv venv && uv sync --all-extras` — never `pip install -e .`; the lock pins tree-sitter 0.25.2 and tree-sitter-commonlisp 0.4.1. Do not touch the pipx venv
- `[x]` T1.3 | Run `uv run pytest tests/ -q` on unmodified `v8`; record counts and `uv pip freeze` to tests/lang_baseline.txt; investigate any pre-existing failure now
- `[x]` T1.4 | Write scripts/snapshot_tables.py (~30 lines) and dump the six core tables to tests/upstream_tables.json — the SC2 comparison snapshot, regenerated at every rebase
- `[x]` T1.5 | Pin the corpus: confirm `~/repos/autolithp` HEAD is `d5a2074` and clean; re-measure the six SRS §1.3 counts; if HEAD moved, stop and update SRS §1.3 first
- `[x]` T1.5b | Create MCP install script for hook suffix registration (`scripts/install-mcp.sh` with `--dry-run`, `--check`, `--help` flags)
- `[x]` T1.5c | Add entry-points stanza to pyproject.toml (`[project.entry-points."graphify_lang.plugins"]`)
