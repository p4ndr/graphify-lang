<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 40-DECISIONS.md

This document is a LIVE file containing DECISIONS made during the project.

- `§3` is the DECISIONS in order of creation, most recent first.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`decision_add`); hand edits by the owner are fine. They number DECISIONS.
<!-- TEMPLATE-END -->

## 3. DECISIONS
### `D-003` | Carry plan for upstream registry | 2026-09-22

If upstream accepts the registry proposal, the fork will rebase onto the accepted implementation and drop its own registry code. Until then, the registry remains in the fork. The AutoLISP plugin (`graphify_lang/autolisp`) is a separate concern and will remain in the fork as a reference implementation.

**Source:** T10.5 (upstream proposal).

### `D-002` | Upstream proposal format: ISSUE, not PR | 2026-09-22

The fork plans to carry the registry indefinitely — upstreaming is a bonus, and a measured *issue* lands changes more often than a PR. The fork's `lang-registry` branch is the reference implementation, and `git diff v8...lang-registry -- graphify/` is the artefact an upstream maintainer can read and apply.

**Source:** T10.2 (issue #3764 on Graphify-Labs/graphify).

### `D-001` | Fork CI and release safety | 2026-09-21

- Add `.github/workflows/graphify-lang-ci.yml` (new file; ci.yml stays unedited).
- Add `if: github.repository == 'Graphify-Labs/graphify'` to every job in publish.yml and release-graph.yml.
- Add `addopts = "-m 'not perf'"` and register the `perf` marker.
- ~~Do not touch `pyproject.toml` `version`~~ — superseded by D-007 (version set to `0.9.55+lang.<n>` in pyproject.toml); fork releases are git tags `0.9.55+lang.<n>`.

**Source:** T2.1-T2.4.

### `D-000` | Language extension layer: branch split | 2026-09-21

Three branches, per SRS §4.2 Workflow 5:

| Branch | Off | Carries | Ends at |
|:-------|:----|:--------|:--------|
| `v8` | `upstream/v8` | nothing of the fork's; only ever fast-forwards | — |
| `lang-registry` | `v8` | `graphify/lang_registry.py`, three core call sites, `tests/test_lang_registry.py`, the `ARCHITECTURE.md` row, and the fork's CI/release/pytest infrastructure | S004 |
| `autolisp` | `lang-registry` | `graphify_lang/`, `tests/lang/`, packaging, corpus fixtures | S009 |

Nothing on `lang-registry` mentions AutoLISP.

**Source:** `cc-IP000.001.md` §1.2.

## D-005a — dcl_references also from dialog names passed to wrapper calls (INFERRED)

Plan 02 §5 requires >=1 dcl_references into lithp_mgr, but autolithp reaches it only via `(dtk:dcl-exec dcl-file "lithp_mgr" ...)` (src/ui/manager.lsp:256), never a literal `(new_dialog "lithp_mgr")`. So: new_dialog literal -> EXTRACTED; an identifier-shaped string argument of any other call inside a defun -> INFERRED dcl_references, emitted only when it names exactly one dialog node in the corpus. Extends A6 (does not reopen it); pinned by tests/lang/test_autolisp_plan02.py::test_dcl_references.

## D-005b — AutoLISP resolver: a name defined in several files resolves to the copy nearest the caller (INFERRED); ties are dropped

autolithp defines err:trap twice (src/core/err.lsp and Import-Refactor/Archive/core/err_mod_main.lsp). Plan 02 §3's drop-ambiguous rule gave 0 inbound cross-file calls to err:trap (measured, tools/measure_autolisp.py), failing §5. Rule now: one candidate -> EXTRACTED; several -> the candidate sharing the longest leading directory path with the caller, confidence INFERRED; equal best prefix -> dropped (god-node guard kept). Measured after: 88 inbound cross-file calls to err:trap in autolithp. Complements A4 (.graphifyignore for archives), does not replace it. Pinned by test_duplicate_definition_resolves_to_nearest_copy.

## D-007 — The fork's package version is 0.9.55+lang.<n> (set in pyproject.toml), so its extraction cache never mixes with stock graphify's cache.

Option 1: give the fork a distinct package version (0.9.55+lang.1) so its AST cache dir differs from stock. Owner accepts that this replaces the old 'do not touch pyproject version' rule. (owner, 2026-09-24). Settles P9: How should the fork stop sharing the AST cache with stock graphify 0.9.55 (D11)?

## D-004 — graphify/detect.py equals v8 except the registry lookup; the @doc comment-sidecar markers in graphify/extract.py are an accepted fork divergence.

Option 1, partial: restore graphify/detect.py to v8 plus only the registry lookup (brings back the 7 dropped suffixes). Keep the @doc sidecar markers in graphify/extract.py. (owner, 2026-09-24). Settles P10: Restore upstream CODE_EXTENSIONS in graphify/detect.py (committed in 84d64c9 without 8 suffixes)?

## D-005 — Owner approves ag-build's AutoLISP resolver rules: wrapper dialog refs and nearest-copy calls

Approved 2026-09-24 after case 005 (docs/testing/case_005_rerun-fork-vs-stock.md). (1) A dialog name passed as a string to a wrapper call gives an INFERRED dcl_references edge when it names exactly one dialog node (autolithp reaches lithp_mgr only via dtk:dcl-exec, src/ui/manager.lsp:256). (2) A name defined in several files resolves to the copy with the longest shared directory path with the caller, INFERRED; ties dropped (88 inbound cross-file calls into err:trap in autolithp vs 0). These are the two entries ag-build wrote with numbers D-005a and D-005b (first written as colliding D-001 / D-002).

## D-006 — Add a `graphify lang list` subcommand (reverses plan 01 out-of-scope note)

Owner decision 2026-09-24, settling legacy P7-P13 (7 copies of SRS F26 / F18.4-F18.10). The subcommand lists registered languages, suffixes, grammar and resolver. It is a core edit in graphify/cli.py and must be try-wrapped like the other registry call sites. Tracked as T26.3.

## D-008 — The regex rules runtime is kept as a fallback/utility layer; language plugins use purpose-built extractors and do not depend on it.

Option 2: repair the regex rules runtime to the S005 emission contract and keep it as a fallback/utility layer; new plugins use their own extractors and may call it. (owner, 2026-09-25). Settles P16: Keep, repair or retire the generic TOML rules runtime (graphify_lang/rules.py, queries.py, regex_rules.py, builtins.py, templates/)?
