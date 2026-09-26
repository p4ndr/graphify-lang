# Review remediation (cc-CR000.001)

A six-stage fix of all 35 defects (4 High, 12 Medium, 13 Low, 6 Nit) and the 9 enhancements in `.claude/docs/cc-CR000.001.md`, released as `v0.9.68+lang.4`.

- Status: DONE (2026-09-26, released as `v0.9.68+lang.4` from `rr-fix` `ddefbc7`; one residual in `05-S006` §3)
- Created: 2026-09-26
- Tasks: T32 (S001), T33 (S002), T34 (S003), T35 (S004), T36 (S005), T37 (S006)

This is the HUB. Each stage is a SPOKE file `05-S00N-*.md` in this folder. A spoke holds the design, the steps and the checks for its findings. The hub holds the decisions, the order, the rules that apply to every stage, and the map from each finding to its spoke.

## 1. Goal

Every finding in `cc-CR000.001.md` is fixed, or is closed with a written reason. Each fix has a test that fails before the fix and passes after it. The fork is then released as `v0.9.68+lang.4`, and the affected graphs are rebuilt.

## 2. Decisions

Decisions (owner, 2026-09-26):

| # | Decision |
|:--|:---------|
| D1 | The regex rules engine stays (D-008 wins over M6 and E7). M6 is fixed by giving the engine a user: the shared plugin core (E2) uses its builtins filter and its sink. The import-by-string `post_file` hook accepts only `graphify_lang.*` modules. E7 is closed as "rejected per D-008". |
| D2 | Findings that need a change in upstream code (H1, M3, L13) are fixed in the fork now, with try-wrapped registry lookups, which the repo rules allow. Each also gets a ready upstream PR draft under plan 01 T10 (E3). |
| D3 | M9 cleanup: delete `.sidecar-cache/` (and add it to `.gitignore`), the root scratch files `src_core_test.lsp`, `test_dcl.toml` and `test_pattern.toml`, `docs/testing/archive/`, `.claude/docs/cc-T10-COMPLETE.md` and `scripts/install-mcp.sh`. `git-sp.ps1` STAYS. |
| D4 | M5: implement `GRAPHIFY_LANG_PATH`. Do not delete it. Manifests in those folders are loaded and registered. |
| D5 | (2026-09-26, after stage 1) Rebase the `rr-*` chain onto `upstream/v8` at the start of S006, before the release. Stages 2 to 5 stay on the current base. |

## 3. Rules for every stage

- One branch per stage, chained: `rr-s1` from `autolisp`, then `rr-s2` from `rr-s1`, and so on. Commits that change the engine (`graphify/lang_registry.py`, `graphify_lang/registry.py`, `manifest.py`, core registry-lookup lines) contain no plugin code, so they can go upstream.
- Test first. Each finding gets a test that fails for the stated reason before the fix. The test id names the finding (for example `test_h4_alias_bomb_bounded`).
- Never edit an existing extractor in `graphify/extractors/`, `engine.py`, `resolution.py` or an upstream test file. Change core tables only through a registry lookup.
- Every stage ends with: `.venv/bin/python -m pytest tests/ -q` exits 0; `git diff upstream/v8...HEAD -- graphify/extractors/` is empty (three dots: only the fork's side, because `upstream/v8` moves); `tests/lang_baseline.txt` and `tests/upstream_tables.json` are unchanged, or the change has a written cause in the spoke.
- When a stage is merged, move its findings from `cc-CR000.001.md` to `cc-CR000.002.md` with the commit hash, as the `/code-review` rules require.

## 4. Stages

| Stage | Spoke | Scope | Why this order |
|:------|:------|:------|:---------------|
| 1 | `05-S001-security-and-crash-safety.md` | H4, E6, L1, L2, L4, N4 | A crafted file can hang or crash a build today. Small and independent. |
| 2 | `05-S002-repo-and-ci-hygiene.md` | M7, M8, E9, M9, M10, N6 | Stages 3 to 6 then run under CI on `rr-*` branches. |
| 3 | `05-S003-shared-plugin-core.md` | E2, L5, H2, M4, M6, E7, L3, E8, N3, L12 | One shared sink fixes the id contract (H2, M4) once, not five times. Stage 4 builds on the new ids. |
| 4 | `05-S004-build-coherence.md` | H1, E3, E5, H3, L9, L11, M2, E1 | Incremental and cached builds give the same graph as a clean build. Needs the stage 3 ids. |
| 5 | `05-S005-registry-robustness.md` | M1, E4, M5, M3, L6, L7, L8, L10, L13, N5 | Loader and hook behaviour. Independent of the plugin ids. |
| 6 | `05-S006-tests-docs-and-release.md` | M12, M11, N1, N2, release `v0.9.68+lang.4`, graph rebuild, PR drafts | The docs describe the final state; the release carries every fix. |

## 5. Finding map

Every finding in `cc-CR000.001.md` appears once.

| Finding | Spoke | Finding | Spoke | Finding | Spoke |
|:--|:--|:--|:--|:--|:--|
| H1 | S004 | M7 | S002 | L7 | S005 |
| H2 | S003 | M8 | S002 | L8 | S005 |
| H3 | S004 | M9 | S002 | L9 | S004 |
| H4 | S001 | M10 | S002 | L10 | S005 |
| M1 | S005 | M11 | S006 | L11 | S004 |
| M2 | S004 | M12 | S006 (plus a test in each stage) | L12 | S003 |
| M3 | S005 | L1 | S001 | L13 | S005 |
| M4 | S003 | L2 | S001 | N1 | S006 |
| M5 | S005 | L3 | S003 | N2 | S006 |
| M6 | S003 | L4 | S001 | N3 | S003 |
| | | L5 | S003 | N4 | S001 |
| | | L6 | S005 | N5 | S005 |
| | | | | N6 | S002 |

| Enhancement | Spoke | Enhancement | Spoke |
|:--|:--|:--|:--|
| E1 | S004 | E6 | S001 |
| E2 | S003 | E7 | S003 (closed: rejected per D1) |
| E3 | S004 (fork hook) and S006 (PR draft) | E8 | S003 |
| E4 | S005 | E9 | S002 |
| E5 | S004 | | |

## 6. Acceptance criteria

- `cc-CR000.001.md` holds no open finding. Every finding is in `cc-CR000.002.md` as fixed (with the commit hash) or closed (with the reason).
- The E5 parity test passes for every plugin fixture: a clean build gives the same nodes and edges as a clean build followed by an incremental build of one changed file.
- `graphify --version` reports `0.9.68+lang.4`, and both MCP servers start.
- The rebuilt graphs keep the plan 04 plugin edge counts in `docs/testing/case_007_plan04-sniff-and-plugins.md`, or a spoke records the cause of each difference (M4 changes the file-node ids).

## 7. Risks

| # | Risk | Handling |
|:--|:-----|:---------|
| R1 | M4 changes the file-node ids of every plugin file, so graph diffs and saved queries that name old ids break. | Stage 6 rebuilds all affected graphs. The spoke records the old-to-new id form. |
| R2 | The fork's `watch.py` hooks (D2) conflict on an upstream rebase. | Each hook is a try-wrapped registry lookup of 3 to 6 lines, and the PR drafts ask upstream to take the same seam. |
| R3 | E1 (plugin-set fingerprint) clears every AST cache once. | The first rebuild after `lang.4` costs CPU only, with no LLM tokens. Stage 6 does it deliberately. |
