# Plan 05 spoke reviews

Review record for the six spokes of plan 05 (hub `docs/plans/05-review-remediation-cc-cr000-001.md`). One H2 section per spoke. Finding ids are `S<n>-<sev><k>`: `C` Critical, `H` High, `M` Medium, `L` Low, `N` Nit, `E` Enhancement. A builder marks an item actioned by appending `- **Actioned**: <commit> <one line>` under it and setting the spoke's Status to `actioned` once every item is closed. Closed out 2026-09-26: every item carries its status from `docs/testing/case_009_plan05-review-fixes.md`.

| Spoke | Critical | High | Medium | Low | Nit | Enhancements | Status |
|:------|:--------:|:----:|:------:|:---:|:---:|:------------:|:-------|
| S001 security and crash safety | 0 | 1 | 1 | 6 | 4 | 2 | actioned |
| S002 repo and CI hygiene | 0 | 0 | 2 | 1 | 5 | 2 | actioned |
| S003 shared plugin core | 0 | 0 | 1 | 3 | 5 | 2 | actioned |
| S004 build coherence | 0 | 0 | 1 | 5 | 4 | 1 | actioned |
| S005 registry robustness | 0 | 1 | 3 | 3 | 3 | 1 | actioned |
| S006 tests, docs and release | 0 | 0 | 2 | 5 | 4 | 1 | actioned |

## S001 security and crash safety

### Scope

- **Range**: `git diff autolisp..rr-s1`, commits `1e678c5..773022d` (8 commits) on `rr-s1`.
- **Spoke**: `docs/plans/05-S001-security-and-crash-safety.md`; findings H4, E6, L1, L2, L4, N4 of `cc-CR000.001.md` (resolutions in `cc-CR000.002.md`).
- **Code**: `graphify_lang/astgrep/extract.py`, `graphify_lang/autolisp/extract.py`, `graphify_lang/ecschema/extract.py`, `graphify_lang/manifest.py`; tests `tests/lang/test_s1_safety.py`, `tests/test_lang_manifest_safety.py`.
- **Verification**: detached worktree of `rr-s1`, `PYTHONPATH` confirmed to import `graphify` and `graphify_lang` from the worktree, Python 3.12.3. Full suite `pytest tests/ -q`: 6154 passed, 14 skipped. S1 tests alone and `test_l1_deep_nesting_falls_back` in isolation: pass. Red-first history checked: `029c35e` and `1e678c5` add strict `xfail(raises=...)` markers; `f3357fb`, `10f235b`, `d498a6f` remove them. Corpus byte-identity claims (llm-linter-tool, AutoLISP, BentleyHelp) were not re-run.
- **Verdict on the six findings**: L2 and N4 (AutoLISP) are correct and complete. H4 is incomplete (S1-H1). L1 is correct at both the test limit (1000) and the production limit (10 000, overflow and fallback measured at 6000 and 50 000 levels) but misses one walk (S1-L1). L4 still raises on two inputs (S1-L4). Good patterns: the child-process timeout harness and `xfail(strict=True, raises=...)` make each red test fail for the stated reason only.

### Critical

None.

### High

- **S1-H1** `graphify_lang/astgrep/extract.py:214,261,250` - Alias expansion still unbounded through `str()` of `id` and `testDir`.
  - **Problem**: `_matches` is now memoised, but `rid = str(doc["id"])` (`:214`, rule/util), `str(doc["id"])` (`:261`, test/snapshot) and `str(t["testDir"])` (`:250`, sgconfig) call `str()` on any YAML value. `str()` of a list built from shared aliases expands every reference, so the H4 billion-laughs vector is still open through these three sinks. The expanded string also becomes the node label and is fed to `_make_id`.
  - **Failure scenario (measured, worktree)**: `rules/b.yml` with 7 alias levels and `id: *g` (302 bytes) takes 2.65 s and emits a 92 MB node label; 8 levels (340 bytes) runs 10.3 s and hits `MemoryError` under a 2 GB address-space limit; 9 levels needs about 9 GB and, without a limit, can OOM-kill `graphify update`. Same scaling for `valid:` test files and `testConfigs: [{testDir: *g}]`.
  - **Fix**: accept only scalars at these sinks, as `_dirs` and `attrs` already do: in `_document`, `if not isinstance(doc.get("id"), (str, int)): return` before the role branch; in the `test_dirs` comprehension, require `isinstance(t.get("testDir"), (str, int))`. Add bomb tests for `id: *alias` (rule and test role) and `testDir: *alias` next to `test_h4_alias_bomb_bounded` (see S1-E1).
  - **Actioned**: `548b209` test, `b282fce` fix — A non-scalar `id` skips the document; `testDir` kept only when `str`/`int`. (case 009)

### Medium

- **S1-M1** `graphify_lang/astgrep/extract.py:225-226,153-155` - Per-util `_key_line` rescans the document: O(utils x document size).
  - **Problem**: for each local util, `_key_line(text, first, rf"^[ \t]+{re.escape(uid)}:")` runs a fresh `re.search` from the start of the document. The N4 change swapped `str.count` for a bisect but left the search itself linear per call, so the loop stays quadratic. The spoke's goal ("no input file can hang a build") covers this path; the spoke did not list it.
  - **Failure scenario (measured)**: one rule document with 5000 utils: 1.38 s; 20 000 utils (about 480 KB): 19.8 s (4x input, 14x time). 100 000 utils would take minutes.
  - **Fix**: build `{key: line}` for indented keys once per document (one `re.finditer(r"^[ \t]+([\w.-]+):", chunk, re.M)` pass, first occurrence wins, which is what `re.search` returns today) and look each `uid` up in it. Add a timed case to `test_s1_safety.py` (for example 20 000 utils under 2 s).
  - **Actioned**: `4bf2374` test, `79ca519` fix, `8065360` test (scaling ratio, not wall clock) — One pass over indented keys per document; 20 000 utils 18.93 s -> 0.94 s locally; llm-linter-tool 82 YAML files output identical. (case 009)

### Low

- **S1-L1** `graphify_lang/autolisp/extract.py:331-333,249-256` - `action_callees` recursion is outside the L1 guard.
  - **Problem**: the `try/except RecursionError` covers only the main walk. `action_callees` parses each `action_tile` string and walks it with the same recursive `_Walker`, after the guard.
  - **Failure scenario (measured, limit 1000)**: `(defun c:x () (action_tile "k" "(foo (foo ... 1200 levels ...)))"))`: the main walk passes (the string is a leaf), then `RecursionError` escapes `extract_autolisp` and upstream `_safe_extract` drops the whole file. At the production limit the depth needed is about 5000.
  - **Fix**: in `action_callees`, catch `RecursionError` and return `[]` (or the callees collected so far); add a test beside `test_l1_deep_nesting_falls_back`.
  - **Actioned**: `59909c2` test, `b0b4af3` fix — `action_callees` returns no callees on `RecursionError`. (case 009)

- **S1-L2** `graphify_lang/astgrep/extract.py:276-281` - The widened `except Exception` leaves partial documents and hides programming errors.
  - **Problem**: `_document` mutates `out` as it goes, so an error midway keeps the rule and util nodes and `contains` edges already added, while the log says "document skipped (YAML does not parse or is malformed)". Any bug (`KeyError`, `TypeError`) in `_rule_doc` is now reported as bad YAML.
  - **Failure scenario (measured)**: `_matches` patched to raise `RuntimeError("bug")`: output is `['file', 'rule', 'util']` with 2 edges and the warning blames the YAML.
  - **Fix**: log `type(exc).__name__` and say "partly extracted" (or snapshot `len(out.nodes)`, `len(out.edges)`, `len(out.refs)` and truncate back on error so "skipped" is true). Keep `except Exception`; the crash-safety goal is right.
  - **Actioned**: `401de76` test, `3c4de2d` fix — `yaml.YAMLError` keeps "document skipped (YAML does not parse)"; any other exception is logged by type with "nodes added before it are kept". (case 009)

- **S1-L3** `graphify_lang/autolisp/extract.py:292-293`; `tests/lang/test_s1_safety.py:95-102` - The L1 fallback drops every call edge in the file, and the test does not pin it.
  - **Problem**: on overflow the whole walker is discarded, so calls, dialogs and actions of every defun in the file are lost, not only those of the deep defun. The test asserts node labels only.
  - **Failure scenario (measured)**: the test file at the production limit gives 3 edges at 3000 levels (including `c:other -> deep` `calls`) and 2 edges at 6000 levels (no `calls`).
  - **Fix**: accept the degradation but state it in the `extract_autolisp` docstring and assert the edge set in `test_l1_deep_nesting_falls_back`, so a later change to the fallback is deliberate.
  - **Actioned**: `6580837` — Docstring states the fallback loss; test pins `contains`-only edges and no refs. (case 009)

- **S1-L4** `graphify_lang/manifest.py:126-134` - `from_toml` still raises; the "never an exception" contract (`:122`) is not met.
  - **Problem**: `path.read_text(encoding="utf-8")` raises `UnicodeDecodeError` (a `ValueError`, not `OSError`) on a non-UTF-8 manifest, and `tomllib.loads` raises `RecursionError` on deeply nested arrays; neither is caught.
  - **Failure scenario (measured)**: a manifest with `name = "caf\xe9"` (Latin-1) raises `UnicodeDecodeError`; `x = [[[...5000...]]]` raises `RecursionError`. The exception then escapes the loader path already tracked as `cc-CR000.001` M1 (stage S005).
  - **Fix**: `except (OSError, UnicodeDecodeError)` on the read; `except (tomli.TOMLDecodeError, RecursionError)` on the parse. Add both inputs to `test_l4_bad_sections_never_raise`.
  - **Actioned**: `bba2f84` test, `d5793c2` fix — `UnicodeDecodeError` and `RecursionError` give a one-line error. (case 009)

- **S1-L5** `graphify_lang/manifest.py:186-203,215-218,255-257` - Remaining manifest fields accept wrong types or shapes.
  - **Problem**: `extract.runtime` is checked for truthiness only (`runtime = 7` is accepted); `extract.resolver` is not checked; `hook_suffixes` and `overrides` are lower-cased but not checked for a leading `.` (the dot check at `:255` covers `suffixes | augments` only).
  - **Failure scenario (measured)**: `hook_suffixes = ["LSP"]`, `overrides = ["DCL"]` load without error as `('lsp',)` and `{'dcl'}`; these can never equal a `Path.suffix`, so the hook or override silently does nothing.
  - **Fix**: require `isinstance(runtime, str)`; extend the dot check to `hook_suffixes` and `overrides`.
  - **Actioned**: `4950b5c` test, `d6f0285` fix — `runtime` / `resolver` must be strings; `hook_suffixes` and `overrides` dot-checked. (case 009)

- **S1-L6** `tests/lang/test_s1_safety.py:19` - Module-level PyYAML skip also skips the L1 and L2 tests.
  - **Problem**: `pytestmark = pytest.mark.skipif(astgrep_extract._yaml is None, ...)` applies to `test_l1_deep_nesting_falls_back` (AutoLISP) and `test_l2_large_schema_linear` (ECSchema), which do not use YAML.
  - **Failure scenario**: in an environment without PyYAML (it is not a graphify dependency), the L1 and L2 regressions go untested.
  - **Fix**: apply the `skipif` to the four astgrep tests only (a named marker), or split the file per plugin.
  - **Rejected**: Already resolved by `87f78fa` (plan 05 S3.5): PyYAML is a runtime dependency and the module-level `skipif` was deleted. (case 009)

### Nit

- **S1-N1** `tests/lang/test_s1_safety.py:85-87`; `.claude/docs/cc-CR000.002.md` (L1 resolution) - "graphify.extract raises the limit to 10 000 on import" is wrong. The limit is raised by `_raise_recursion_limit()` (`graphify/extract.py:180-182`) when extraction runs; measured: after `import graphify.extract` the limit is still 1000. The fixture is still needed (an earlier test that ran extraction leaves 10 000); correct the wording in both places.
  - **Actioned**: `0b8e5ba` (fixture), `0d1f41d` (`cc-CR000.002.md`) — The limit is raised by `_raise_recursion_limit()` when extraction runs, not on import. (case 009)
- **S1-N2** `graphify_lang/autolisp/extract.py:117-125`, `graphify_lang/astgrep/extract.py:142-150` - `_newlines` / `_line_of` are duplicated, and the module-level `lru_cache(maxsize=4)` keeps up to four whole file texts (the cache keys) and their offset tuples alive for the life of the process. Compute the offsets once as a local in `extract_autolisp` / `extract_dcl` and pass them down, or move one helper into the stage 3 shared core (S003) together with the third copy of the `_edge_keys` sink.
  - **Actioned**: `3782129` — `_common.line_index(text)`, built per extraction and passed down; no module `lru_cache`. (case 009)
- **S1-N3** commit `029c35e`, `tests/lang/test_s1_safety.py` - The red L1 test had no recursion-limit pin; its `xfail(raises=RecursionError)` held only when no earlier test had run extraction (otherwise it failed with `AssertionError`). The pin arrived with the fix in `10f235b`. For S002 to S006: pin the environment in the red commit.
  - **Rejected**: Process advice, no code change; followed in this pass (the S1-L1 and S1-L4 red tests pin the recursion limit in the red commit). (case 009)
- **S1-N4** `tests/lang/test_s1_safety.py:33-41` - `_timed` uses `check=True` with captured output, so a child crash surfaces as a bare `CalledProcessError` without the child's traceback. Run without `check` and `pytest.fail(proc.stderr)` on a non-zero exit.
  - **Actioned**: `0b8e5ba` — `_timed` runs without `check=True` and fails with the child's stderr. (case 009)

### Enhancements

- **S1-E1** `tests/lang/test_s1_safety.py` - Extend the H4 bomb generator to put the alias at `id:` (rule and test roles) and at `testConfigs[].testDir`, and assert that `matches:` under a shared alias is still credited once (the memoised `_matches` has no test that it finds anything). — Effort: LOW | Benefit: HIGH
  - **Actioned**: `548b209` — Bombs at rule `id`, test `id` and `testConfigs[].testDir`; shared `matches:` credited once. (case 009)
- **S1-E2** `graphify_lang/astgrep/extract.py:267-275` - Defence in depth: skip an ast-grep YAML document above a size cap (real rule files are a few KB; for example 1 MB) with a warning. This bounds every present and future per-document cost (S1-H1, S1-M1, deep nesting: a 400 KB `[[[...]]]` document takes 5.3 s in PyYAML before failing). — Effort: TRIVIAL | Benefit: NEUTRAL
  - **Actioned**: `954a22b` test, `e5d5c99` fix — Documents over 1 000 000 characters skipped with a warning. (case 009)

## S002 repo and CI hygiene

### Scope

- **Range**: `git diff rr-s1..rr-s2`, commits `711dfc6..8e3354c` (7 commits) on `rr-s2`.
- **Spoke**: `docs/plans/05-S002-repo-and-ci-hygiene.md`; findings M7, M8, E9, M9, M10, N6 of `cc-CR000.001.md` (resolutions in `cc-CR000.002.md`).
- **Code**: `.github/workflows/{publish,release-graph,graphify-lang-ci}.yml`, `.gitignore`, `tests/lang/test_rules.py`; 40 deleted files (`.sidecar-cache/`, root scratch files, `docs/testing/archive/`, `.claude/docs/cc-T10-COMPLETE.md`, `scripts/install-mcp.sh`, `docs/16-MCP-SETUP.md`); task and review documents.
- **Verification**: read via `git show rr-s2:` only. `git diff upstream/v8 rr-s2 -- .github/` (upstream `.github/` unchanged since the merge base `4c73561`). Detached worktree of `rr-s2`, imports confirmed to resolve into it, repo `.venv`: all 4 workflows pass `yaml.safe_load`; `bandit -r graphify_lang` 0 issues at any severity; `bandit -r graphify graphify_lang -lll` gives the same 4 High B324 as CI; `pip-audit` probes (S2-M1). `gh run view 36219115105 -R p4ndr/graphify-lang --log` (head `3d3b99f`); run 36219696955 on `8e3354c` also succeeded. `gh api repos/p4ndr/graphify-lang/actions/permissions/workflow`: `default_workflow_permissions: read`. The full test suite was not re-run (CI numbers accepted).
- **Verdict on the six findings**: M7 is fixed faithfully: against `upstream/v8` the only delta in `publish.yml` and `release-graph.yml` is the one `if: github.repository == 'Graphify-Labs/graphify'` job line (in `release-graph.yml` it moved above `permissions:`, same job). M9, M10 and N6 are complete: no live reference to any deleted file (`docs/16-MCP-SETUP.md` included) remains outside history notes (one stale citation, S2-N4). The `tomllib`/`tomli` fallback is correct (`tomli` is declared for `< 3.11` at `pyproject.toml:18`) and CI 3.10 passes. M8 and E9 are closed in trigger terms, but the security job they extended cannot report or fail (S2-M1, S2-M2), and the resolution record's "security-scan success" is wrong: in run 36219115105 both the bandit and the pip-audit step exited 1, hidden by `continue-on-error`. Safe on the other axes: the fork CI uses `pull_request` (not `pull_request_target`), references no secrets, and the repository token defaults to read. Good pattern: the S2.5 CI run found a real 3.10 break that no local run could.

### Critical

None.

### High

None.

### Medium

- **S2-M1** `.github/workflows/graphify-lang-ci.yml:59-61` - `pip-audit --strict` fails on every fork run before it reports anything.
  - **Problem**: `uv sync` installs the project editable as `graphifyy 0.9.67+lang.N`, which is not on PyPI. With `--strict`, pip-audit treats that as a fatal skip and exits 1. `continue-on-error: true` turns the job green, so the dependency audit has never produced a result in the fork. `cc-CR000.002.md` (M8 resolution) and the spoke's S2.5 row record "security-scan success".
  - **Failure scenario (measured)**: CI log of run 36219115105: `ERROR:pip_audit._cli:graphifyy: Dependency not found on PyPI and could not be audited: graphifyy (0.9.67+lang.3)`, then `Process completed with exit code 1`. Locally, `pip-audit --strict --skip-editable` also exits 1 ("distribution marked as editable"). `pip-audit --skip-editable` (no `--strict`) runs and reports 14 known vulnerabilities in 4 packages (anyio 4.13.0, cryptography 49.0.0, pip 26.1.1, soupsieve 2.8.3). The lock pins those same versions, so CI would report them too. None of this is visible today.
  - **Fix**: run `uv run --frozen pip-audit --skip-editable` (drop `--strict`, since the only skip is the project itself). Alternatively, audit the locked set: `uv export --frozen --no-emit-project --no-hashes -o req.txt` then `pip-audit -r req.txt --strict` [UNCERTAIN: not probed]. Correct the "security-scan success" wording in `cc-CR000.002.md` M8 and the spoke S2.5 row. Triage the 14 advisories as a separate task (lock bumps are upstream-owned; record them, do not silently fix).
  - **Actioned**: `89b12ff` test, `2352a06` lock, `3a8f0dc` fix, `cc729db` docs — `pip-audit --skip-editable`, gating, job syncs all extras. (case 009)

- **S2-M2** `.github/workflows/graphify-lang-ci.yml:55-57` - bandit over `graphify_lang` cannot fail or even change colour.
  - **Problem**: the step is `continue-on-error: true`, and upstream code already makes it exit 1 on every run (4 High B324, 8 Medium at `-ll`). A new High or Medium in `graphify_lang` leaves the job green and the step red, exactly as before. E9's stated benefit (a security gate over the fork layer) is not delivered.
  - **Failure scenario**: a future plugin adds `xml.etree.ElementTree.fromstring` on repository files (B314, Medium) or `yaml.load` (B506). CI stays green, and the log shows 9 Medium instead of 8, which no one reads.
  - **Fix**: add a separate gating step without `continue-on-error`: `uv run --frozen bandit -r graphify_lang -ll` (measured: 0 issues at any severity today). Keep the combined `graphify graphify_lang` scan as the informational step. Or pass a `--baseline` of the 4 upstream B324 findings.
  - **Actioned**: `89b12ff` test, `644cc9c` fix — Gating `bandit -r graphify_lang -ll`; combined scan kept informational. (case 009)

### Low

- **S2-L1** `.github/workflows/graphify-lang-ci.yml:14-16` - Fail-fast matrix hides failures on the other Python versions.
  - **Problem**: `strategy` has no `fail-fast: false`, so the first failing Python version cancels the others.
  - **Failure scenario (measured)**: run 36219014956 failed on 3.10 (bare `tomllib` import), and 3.12 and 3.13 were cancelled, so that commit was never tested on them. A version-specific break on 3.13 would be masked in the same way by any 3.10 failure.
  - **Fix**: `strategy: {fail-fast: false, matrix: ...}`.
  - **Actioned**: `89b12ff` test, `50363e0` fix — `fail-fast: false`. (case 009)

### Nit

- **S2-N1** `.github/workflows/graphify-lang-ci.yml:1-9` - No `permissions:` block. Safe today only because the repository default is `read` (measured). Add `permissions: {contents: read}` at the top level so a settings change, or a copy into another repository, cannot give PR-triggered jobs a write token. Same file: actions are pinned by mutable tag (`actions/checkout@v6`, `astral-sh/setup-uv@v8.1.0`). This is acceptable while the workflow has no secrets and a read token; pin by SHA if either changes.
  - **Actioned**: `89b12ff` test, `50363e0` fix — Top-level `permissions: {contents: read}`. (case 009)
- **S2-N2** `.github/workflows/graphify-lang-ci.yml:6` - `tags: ["v*"]` also matches every upstream release tag (`v0.9.68`, `v1.0.0` are in the local tag list). Pushing one of them to `origin` runs the fork CI on upstream code. Narrow it to the fork's scheme, `'v*\+lang.*'` (`+` is a filter metacharacter and needs the escape).
  - **Actioned**: `89b12ff` test, `50363e0` fix — `tags: ['v*\+lang.*']`. (case 009)
- **S2-N3** `.claude/docs/cc-CR000.001.md` `## Metrics`, `## Suggestion plan` item 6 - Still lists M7-M10, E9 and N6, and the stage 1 items, as open. The Metrics table (Nit 6, Enhancements 9, Style/docs/CI 6) contradicts the header table (Nit 4, Enhancements 7). This file's rule is "open findings only": recount the Metrics table and the category line, and drop the closed items from the plan.
  - **Actioned**: `39fce02` — Suggestion plan and Metrics show open findings only (all 0). (case 009)
- **S2-N4** `docs/35-DONE.md:179-184` - T17.4-T17.6 and the `**Sources:**` line cite `docs/testing/T14-FINAL-REPORT.md` and `T14-COMPLETE.md`, both now deleted. The S2.3 acceptance grep (`testing/archive`) does not match these paths. Append "(deleted in plan 05 S2.3; see git history before `1f8a2e4`)".
  - **Actioned**: `6614b24` — T17.4-T17.6 and Sources marked deleted in S2.3 (`1f8a2e4`). (case 009)
- **S2-N5** `tests/lang/test_rules.py:8-11`, `graphify_lang/cargo/augment.py:23-26`, `graphify_lang/manifest.py:10-13` - Three copies of the `tomllib`/`tomli` shim. `manifest.py` binds the name inverted (`import tomllib as tomli`). Move one shim into the S003 shared core and import it from the three sites.
  - **Actioned**: `333a33d` test, `b12630a` engine, `76cbe8f` cargo — One shim in `manifest.py`, bound as `tomllib`; kept there, not `_common.py`, because `_common` imports `manifest` (circular otherwise). (case 009)

### Enhancements

- **S2-E1** `.github/workflows/graphify-lang-ci.yml` - On `v*` tag pushes, run `uv build`, install the wheel into a clean venv, and check that every plugin loads (for example `graphify lang list` lists all shipped languages). The current tag run tests the source tree, so M8's "a released wheel is never CI-tested" is only half closed (missing package data would still ship). — Effort: LOW | Benefit: HIGH
  - **Actioned**: `89b12ff` test, `3232862` fix — `wheel` job on tags (and `workflow_dispatch`): `uv build --wheel`, clean `uv venv`, `graphify lang list --check`. (case 009)
- **S2-E2** `tests/` - A regression guard for the M7 class: one test that runs `yaml.safe_load` on every `.github/workflows/*.yml` and asserts a dict with `jobs`. `actionlint` is not installed on the host, and nothing else parses the workflows before a release event. — Effort: TRIVIAL | Benefit: MINOR
  - **Actioned**: `89b12ff` — `test_s2_e2_every_workflow_parses` over all 4 workflows. (case 009)

## S003 shared plugin core

### Scope

- **Range**: `git diff rr-s2..rr-s3`, commits `542f417..b6426db` (22 commits) on `rr-s3`.
- **Spoke**: `docs/plans/05-S003-shared-plugin-core.md`; findings E2, L5, H2, M4, M6, E7 (closed per D1), L3, E8, N3, L12 of `cc-CR000.001.md` (resolutions in `cc-CR000.002.md`); case `docs/testing/case_008_plan05-remediation.md`.
- **Code**: new `graphify_lang/_common.py`; the six plugins' `__init__.py`, `extract.py`, `resolve.py` and manifests; `rules.py`, `builtins.py`, `manifest.py`, `registry.py`, `cc_kb/{augment,resolve}.py`, templates; tests `tests/lang/test_s3_shared_core.py`, `test_rules.py`, `test_astgrep.py`, `test_s1_safety.py`.
- **Verification**: read via `git show rr-s3:` / `git diff` only. Detached worktrees of `rr-s2` and `rr-s3`, imports confirmed to resolve into each worktree (run from outside the repo so `''` on `sys.path` does not shadow `PYTHONPATH`), repo `.venv`, Python 3.12. Full suite on `rr-s3`: 6178 passed, 14 skipped (matches the spoke). Before/after corpus builds, `extract(git ls-files, cache_root=<fresh>, root=repo)`, edges compared id-free as `(source_file, label, node_kind)` and node dicts compared minus `id`: autolithp (`.lsp .mnl .dcl .md`), BentleyTools (vba), BentleyHelp (bmake, ecschema), llm-linter-tool (astgrep). Stale-cache probe with `graphify.cache._EXTRACTOR_VERSION` pinned (the builder's concurrent reinstalls flip the `.venv` version between `+lang.2` and `+lang.3`, which otherwise namespaces the cache apart). Builtins sets compared per plugin. `ruff check --select F,B graphify_lang`: no unused import or name left by the refactor.
- **Verdict**: the refactor preserves behaviour. autolithp re-measured exactly as case 008 (before 10691 nodes / 10630 ids / 25522 edges, after 10691 / 10691 / 25584). The `sidecar_doc` 1 -> 63 change is correct, not a regression: the corpus has 63 `; @sidecar` headers and now has 63 `sidecar_doc` edges, every one file -> `page`, 62 to the same-stem `.md`; the only other id-free delta is 3272 `contains` edges moved from the formerly merged `.lsp`+`.md` node to the split nodes, with 0 `contains` edges crossing files. vba, bmake, ecschema and astgrep corpora: identical id-free edges and node attributes. The id contract holds: refs carry `node`, upstream never rebinds a `per_file[i]["nodes"]` list between extraction and the resolvers (only whole results are replaced, on read failure or cache hit), and `test_m4_file_ids_portable` pins root-free, unique, root-independent ids. No bypass of the `post_file` prefix found (S3-L1). S1-L6 is closed as a side effect of L12 (the module-level PyYAML skip is gone). Good patterns: one sink and one prefix rule instead of five copies, and case 008's id-free before/after comparison is the right instrument for an id-changing refactor.

### Critical

None.

### High

None.

### Medium

- **S3-M1** `graphify_lang/_common.py:94-102` - A same-version AST cache written before S3 makes the autolisp and vba resolvers fail outright.
  - **Problem**: `resolve_ref_id` reads `ref["node"]`. Before S3 the autolisp and vba sinks stored `source`, not `node`. Upstream's AST cache is namespaced only by the installed `graphifyy` version and `_AST_CACHE_SCHEMA` (`graphify/cache.py:30-39`), and `rr-s3`'s `pyproject.toml:7` still says `0.9.67+lang.3`, the version of the released tag `v0.9.67+lang.3` that is installed today. Any `graphify-out/cache/ast/v0.9.67+lang.3-s4/` written by that release is read back by an S3 build with the same version string.
  - **Failure scenario (measured)**: fixture `app/x.lsp` -> `sub/lib.lsp` and `app/x.bas` -> `sub/lib.bas`; build with `rr-s2` into a cache, then with `rr-s3` on the same cache (version pinned): `WARNING graphify.resolver_registry: autolisp resolution failed, skipping: 'node'`, same for vba; the graph drops from 2 `calls` edges to 0. On a real corpus every cross-file autolisp / vba edge (`calls`, `dcl_references`, `dcl_action`, `module_depends`, `sidecar_doc`) disappears with one warning. Cached pre-S3 file ids (stem form) would also mix with the new form.
  - **Fix**: make `refs_of` / `resolve_ref_id` tolerate a ref without `node` (fall back to `r.get("source")`, or skip the ref) so a stale entry degrades one file, not the whole pass; and bump the fork version (`+lang.4`) before any build from this branch is installed, so the cache namespace changes (upstream's `_AST_CACHE_SCHEMA` is not ours to bump). Add a test that feeds `refs_of` a node-less ref.
  - **Actioned**: `80f5d33` test, `bf00dbd` fix — `resolve_ref_id` falls back to a pre-S3 ref's `source` id, else None; `refs_of` and the ecschema resolver drop a ref with none. (case 009)

### Low

- **S3-L1** `graphify_lang/rules.py:73-75`; `graphify_lang/templates/{programming,markup}.toml` - The `post_file` prefix rule guards no boundary and makes the hook usable only in-tree.
  - **Problem**: nothing in `graphify` or `graphify_lang` calls `rules.build` (registry dispatch never reads `extract.runtime`; `manifest.py:231`), so a rules manifest only runs when an entry-point package's own code calls `build`, and that code already runs arbitrarily. No bypass exists: `graphify_lang` is a regular package, so `graphify_lang.<x>` resolves only under its installed `__path__`, and `fn` is a single `getattr` (the only stdlib names re-exported by `graphify_lang` modules, `os` and `importlib`, are modules, not callables). But `graphify_lang` is this repo's package, so the templates, whose audience is out-of-tree language authors, now advertise a hook such an author cannot use.
  - **Failure scenario**: a third-party package `mylang` following `templates/programming.toml` sets `post_file = "mylang.hooks:post"`; every file of that language returns `{"nodes": [], "error": "... rejected: only graphify_lang.* modules"}`.
  - **Fix**: either say in the templates and the `rules.py` docstring that `post_file` is for in-tree modules only (and record the threat model in D1), or allow the calling package's own prefix (pass the entry-point package name into `build`).
  - **Actioned**: `80f5d33` test, `ab276d1` fix — `rules.build(..., package=)`: a `post_file` hook may name `graphify_lang.*` or the caller's own package, nothing else. (case 009)

- **S3-L2** `graphify_lang/_common.py:72`; `graphify_lang/rules.py:1-25` - `rules.Out` now drops recursive self-calls, unlike the built-in extractors.
  - **Problem**: `Sink.edge` returns on `src == tgt`, which `rules.Out` inherits. The spoke records it as a deviation, but the `rules.py` emission contract, which is written against the built-ins' contract, does not mention it, and no test pins it.
  - **Failure scenario (measured)**: `rules.Out` with `f` referencing `f`: `rr-s2` emits `('r_a_f_f', 'calls', 'r_a_f_f')`, `rr-s3` emits none. The upstream Python extractor on `def f(n): return f(n-1)` emits `('a_f', 'calls', 'a_f')`. A rules-tier language therefore reports recursion differently from a built-in one.
  - **Fix**: pick one and pin it: either let `rules.Out.edge` keep self-loops for reference relations (matching upstream), or state "no self-loops" in the `rules.py` docstring and add a test.
  - **Actioned**: `80f5d33` test, `8c02786` fix — `rules.Out` keeps a recursive reference's self-loop (`Sink.edge(self_loop=True)`), as upstream's built-ins do; plugin sinks still drop `src == tgt`. (case 009)

- **S3-L3** `graphify_lang/cc_kb/augment.py:65-72` - `_is_root` is cached for the life of the process, including negative results.
  - **Problem**: `lru_cache(maxsize=256)` on `folder -> bool`. `graphify watch` rebuilds in-process (`graphify/watch.py:1475` imports `extract`), so a folder that gains a `docs/cc-*.md` after its first scan stays "not a root", and one that loses it stays a root, until restart. Not measured; follows from the code.
  - **Failure scenario**: in a watch session, creating the first `docs/cc-RF000.000.md` in a new harness folder: the cc-kb pages of that folder keep resolving against the wrong root.
  - **Fix**: S004 H3 already moves this scan into the resolver; make sure the cache moves to per-build scope there (a dict local to one `resolve` call), and do not ship a release between S003 and S004 without it, or clear the cache at the start of each augment pass.
  - **Rejected** (moot): `953efd6` (plan 05 S4.3, H3) deleted the `lru_cache` on `_is_root`: harness roots are derived from the graphed nodes inside each `resolve` call, and `graphify_lang/cc_kb/` holds no process cache. (case 009)

### Nit

- **S3-N1** `graphify_lang/builtins.py:36` - Treating `#` as a comment for every builtins file removes the AutoLISP builtin `#&/` (`autolisp/data/builtins.txt:6`); measured `is_builtin('#&/')` True -> False, every other AutoLISP and VBA name unchanged. Harmless in practice (the walker is unlikely to see it as a call), but it is a silent data change the commit (`1d2eb29`, which only mentions `;`) does not state. Either drop the line from the data file with a note, or document it.
  - **Actioned**: `80f5d33` test, `115e717` fix — `#` starts a builtins comment only before a space or the line end; `is_builtin('#&/')` True again. (case 009)
- **S3-N2** `graphify_lang/manifest.py:144-145` - `data.get("schema", 1) not in (1, "v1")` accepts `schema = true` and `schema = 1.0` (`True == 1`), and the message says "must be 1" while `"v1"` is also valid. Add `not isinstance(v, bool)` and say "must be 1 or \"v1\"".
  - **Actioned**: `80f5d33` test, `a716186` fix — `schema` must be the integer 1 or `"v1"` (`true`, `1.0` rejected); message says `must be 1 or "v1"`. (case 009)
- **S3-N3** `tests/lang/test_s3_shared_core.py:111-145` - `test_n3_every_manifest_key_is_read` checks manifest keys against `_READ`, a list kept in the test, not against what the code reads; a key added to both a manifest and `_READ` passes with no reader. `extract.runtime` is in `_READ` although it is only checked for presence (`manifest.py:217-220,231`) and never used to dispatch, so a wrong runtime string passes. State in `_READ` which keys are "validated only", or make the check read the code (for example, the manifest dataclass fields plus the `rules` engine's reads).
  - **Actioned**: `80f5d33` — `test_s3_n3_every_read_key_has_a_reader_in_code`: each `_READ` key's leaf must be a string literal in `graphify_lang`. (case 009)
- **S3-N4** `graphify_lang/rules.py:54,58` vs `graphify_lang/_common.py:79,90` - `rules.Out.ref(source, name, relation, line)` and `Out.result()` override `Sink.ref(kind, source, line, ...)` and `Sink.result(refs_key)` with incompatible signatures, so an `Out` is not usable where a `Sink` is expected. Rename the engine's methods (for example `name_ref`, `resolved`) or hold a `Sink` instead of subclassing it.
  - **Actioned**: `80f5d33` test, `0aaf7f0` fix — `Out.ref` -> `name_ref`, `Out.result` -> `resolved`, `Out.node` takes `**attrs`; test pins no signature clash with `Sink`. (case 009)
- **S3-N5** `graphify_lang/astgrep/extract.py:69-76`, `graphify_lang/autolisp/extract.py:59-67`; `graphify_lang/manifest.py:11`, `graphify_lang/cargo/augment.py:23-26`, `tests/lang/test_rules.py:8-11` - The shared core did not absorb the two duplications earlier reviews named it as the home for: `_newlines` / `_line_of` (with the process-lifetime `lru_cache(maxsize=4)` on whole texts, S1-N2) and the `tomllib` / `tomli` shim (three copies, S2-N5). `_common.py:25` now re-exports manifest's inverted `tomli` name. Move both into `_common.py`, or close S1-N2 and S2-N5 explicitly as not doing.
  - **Rejected** (done): Both duplications were absorbed by earlier parts: S1-N2 `3782129` (`_common.line_index`, no module cache) and S2-N5 `333a33d`/`b12630a`/`76cbe8f` (one `tomllib` shim in `manifest.py`, re-exported as `tomllib`). (case 009)

### Enhancements

- **S3-E1** `tests/lang/test_s3_shared_core.py` - Unit tests for the shared core itself: `pick_by_prefix` (one candidate, longest-prefix win as INFERRED, tie -> None), `Sink.ref(unique=True)` de-dup, `Sink.add` clash salting, and a stale-cache regression for S3-M1 (a node-less ref degrades, does not raise). Today these are covered only through plugin fixtures. — Effort: LOW | Benefit: HIGH
  - **Actioned**: `80f5d33` — `test_s3_e1_pick_by_prefix`, `test_s3_e1_sink_ref_unique_and_add_salting`, and the stale-cache regression `test_s3_m1_stale_cache_ref_degrades`. (case 009)
- **S3-E2** `tools/` - Keep case 008's before/after instrument (id-free edge triples plus node dicts minus `id`, over `git ls-files` per plugin, fresh cache) as a script, so S004-S006 can re-run the same comparison in one command instead of rebuilding it. — Effort: LOW | Benefit: MINOR
  - **Actioned**: `32c510f` — `tools/compare_corpus.py --before <ref> [--after <ref>] PLUGIN=REPO ...`; exits 1 on any difference. (case 009)

## S004 build coherence

### Scope

- **Range**: `git diff rr-s3..rr-s4`, commits `a5961fe..8b81821` (8 commits) on `rr-s4`.
- **Spoke**: `docs/plans/05-S004-build-coherence.md`; findings H1, E5, H3, L9, L11, M2, E1 of `cc-CR000.001.md` (resolutions in `cc-CR000.002.md`); E3 stays open for S006; case `docs/testing/case_008_plan05-remediation.md` §3-4; ltm learnings 1490, 1491.
- **Code**: upstream `graphify/watch.py`, `graphify/cli.py` (incremental context hooks); fork-owned `graphify/lang_registry.py` (`context_fields`, `_namespace_ast_cache`, `_fingerprint`); `graphify_lang/{_common,manifest,registry}.py`; `cargo/{augment,resolve}.py` (new resolver), `cc_kb/{augment,resolve}.py`, `bmake/{extract,resolve}.py`, `astgrep/resolve.py`; six manifests (`[resolve] context_fields`); tests `tests/lang/test_s4_build_coherence.py`, `test_cargo.py`, `test_cc_kb.py`.
- **Verification**: read via `git show rr-s4:` / `git diff` only. Detached worktrees of `rr-s3` and `rr-s4`, imports confirmed to resolve into each worktree, repo `.venv`, Python 3.12. Full suite on `rr-s4`: 6195 passed, 14 skipped (matches the spoke). Probes, all s3 vs s4:
  - **CLI incremental path** (not covered by E5): per fixture tree and per plugin file, `python -m graphify extract <tree> --code-only --no-cluster`, append a newline to the file, re-run (incremental), compare with a clean build of the edited tree: `rr-s3` 13 differing files (bmake 2, astgrep 5, vba 4, ecschema 1, plan02 1), `rr-s4` 0 on bmake, astgrep, vba, ecschema, plan02, cargo. cc-kb is not reachable on this path (`--code-only` skips `.md`).
  - **Watch path, full attributes**: the E5 loop with node dicts and edge dicts compared whole (minus `_origin`, `community`, `weight`): 0 differing files on all 8 trees. No `_lang_source_file` reaches any `graph.json`, full or incremental.
  - **Full builds**: `extract()` over `git ls-files '*.md'` of `~/repos/claude-config` (871 files, harness) and `~/repos/BentleyTools` (2105 files, 2002 of them outside any harness root): id-free edge sets identical s3 vs s4 (51134 and 33868 keys), node and edge counts identical, wall time 2.3 -> 2.0 s and 2.5 -> 2.4 s, AST cache size unchanged (37 MB, 39 MB). New field cost: `cc_kb_links` on 296 nodes / 28 KB (claude-config), 36 nodes / 47 KB (BentleyTools), 0.1-0.2 % of `graph.json`. All three new fields hold relative or raw strings (`cc_kb_links` relative to the doc's folder, `bmake_includes` raw include names, `cargo_ws_deps` `key=package[@path]`), so no absolute path is persisted.
  - **Add-file probe** (open question a): `_rebuild_code(changed_paths=[new file])` vs a clean build, `rr-s4`: cargo misses `has_member` to the new crate, cc-kb misses both `cites` from the unchanged hub to a new spoke, AutoLISP misses `calls` to a new callee, and upstream Python misses `imports` + `calls` from an unchanged `a.py` to a new `b.py`.
  - **Fingerprint cost**: `python -X importtime -c "import graphify.detect"`: 40 ms (`rr-s3`) -> 175-220 ms (`rr-s4`); `importlib.metadata.packages_distributions()` alone 133 ms in the 195-distribution `.venv`, `_namespace_ast_cache` 152 ms. Listing and reading every `.py`/`.toml` under the `.venv` `site-packages` (16442 files, 206 MB): 5.3 s.
- **Verdict**: the stage does what it claims. H1 is fixed on both incremental paths, including the untested CLI one, with full attribute parity on every fixture; H3 and L9 hold (augments read only their own file, resolvers see only graphed nodes) and clean-build output is byte-for-byte equivalent id-free on two real Markdown corpora; E1 / M2 work as specified. The `context_fields` design is the right shape: a declared, per-manifest field list, a read-only context (the new fields ride on dicts that upstream never emits), and a hook that degrades to pre-S4 behaviour when the registry is absent. Good patterns: moving cross-file facts from payloads onto declared node fields, `source_of` as the one place that reconciles the two path forms, and red-first strict xfails for every finding. The one real cost is the import-time fingerprint (S4-M1).

### Critical

None.

### High

None.

### Medium

- **S4-M1** `graphify/lang_registry.py:61-106` - The cache fingerprint runs a full-environment metadata scan on every graphify import, and hashes all of `site-packages` for a single-module plugin.
  - **Problem**: `_apply_registry` runs at import of `graphify.detect`, `graphify.cli` and `graphify.extract`, so `_fingerprint` runs in every graphify process, including `graphify query`, the MCP servers and `watch`. It calls `metadata.packages_distributions()`, which reads the `RECORD` / `top_level.txt` of every installed distribution, only to find the version of the plugin distributions the registry already found through their entry points. It then hashes `Path(mod.__file__).parent` for each plugin module: for a plugin shipped as a top-level module (`site-packages/mylang.py`), that directory is `site-packages` itself. Under a spawn or forkserver start method (Windows; the Linux default from Python 3.14) each `ProcessPoolExecutor` worker re-imports graphify and pays it again.
  - **Failure scenario (measured)**: `import graphify.detect` goes from 40 ms to 175-220 ms (`packages_distributions` 133 ms of it) in the repo `.venv`. A third-party single-file plugin adds a read of 16442 files / 206 MB (5.3 s before hashing) to every graphify process, and its cache namespace, so the whole AST cache, is wiped whenever any package in the environment changes.
  - **Fix**: take each plugin's distribution from its entry point (`ep.dist.name`, `ep.dist.version`, already enumerated in `graphify_lang/registry.py`) instead of `packages_distributions()`; hash a module's own file when it is not a package (`mod.__spec__.submodule_search_locations is None`), else its package directory; keep the result `lru_cache`d. Pin it with a test that times or mocks `packages_distributions` (must not be called).
  - **Actioned**: `0975dff` test, `1990154` fix — Distributions from `ep.dist` (`registry.distributions()`), no `packages_distributions()`; a plugin package hashes its top-level package dir, a top-level module only its file; `lru_cache` kept. (case 009)

### Low

- **S4-L1** `graphify/lang_registry.py:51-54` - A fingerprint failure leaves the plain upstream cache namespace in place, so the stale entries E1 was meant to make unreachable are read again.
  - **Problem**: `_namespace_ast_cache` is wrapped in `except Exception: _LOG.warning(...)`; on any error (`OSError` reading a plugin file mid-install, `PackageNotFoundError` from `metadata.version`) `_EXTRACTOR_VERSION` stays `v<version>`, the namespace a pre-S3 build of the same version wrote.
  - **Failure scenario**: a same-version cache written before S3 plus one unreadable plugin file: the autolisp and vba resolvers fail on `'node'` again (S3-M1) and all their cross-file edges drop, with one warning.
  - **Fix**: in the `except`, still append a constant suffix (for example `-langerr`), so a failed fingerprint never lands in the plain namespace; the cost is one re-extraction.
  - **Actioned**: `0975dff` test, `1990154` fix — `_namespace_ast_cache` catches its own failure: `-langerr` namespace plus a warning. (case 009)

- **S4-L2** `tests/lang/test_s4_build_coherence.py:45-77` - The E5 parity test covers one of the two hooked paths and one of three change kinds.
  - **Problem**: it drives only `watch._rebuild_code`; the `cli.py` hook (`graphify extract` incremental) has no test. It rewrites a file's bytes unchanged, so an edit that changes a file's payload, and an added or deleted file, are never exercised. It compares `(source, target, relation)` only, so a changed `confidence`, `context`, `external_deps`, `unresolved_includes` or `dangling_cc_refs` would pass. The two exclusions (dangling edges, same-stem salting) are justified and documented in case 008 §4.
  - **Failure scenario**: an upstream rebase that renames `_ctx_node` in `cli.py` turns the hook into dead code (or a `NameError` swallowed by upstream's fail-open `except`, dropping all context), and no test fails. Measured today: the CLI path has parity on `rr-s4` (0 differing files) and not on `rr-s3` (13), and full attribute parity holds on the watch path, so the stronger assertions pass now.
  - **Fix**: parametrize the test over both paths (`graphify extract --code-only` via `cli.main` or a subprocess, for the non-Markdown trees); compare node and edge dicts minus `_origin` / `community` / `weight`; append a byte (a comment or newline) instead of rewriting the same bytes; add a strict xfail for the add-file class (S4-E1).
  - **Actioned**: `0975dff` — Parametrized over `watch` and `cli` (`dispatch_command("extract")` in-process, `--code-only`; cc-kb watch only); a byte appended per file; whole node and edge dicts minus `_origin` / `community` / `weight` vs a clean build of the edited tree. (case 009)

- **S4-L3** `graphify/watch.py:1717-1747`, `graphify/cli.py:3869-3898` - The hooks sit inside upstream's context loops and fail silently.
  - **Problem**: minimal (9 lines each) and fail-safe in the sense that matters (import or registry failure -> no fields -> pre-S4 behaviour), but the per-node `update` sits between upstream's marker loop and its metadata block, the code upstream edits most often (#2437, #2438, #3714 each added keys there), so a rebase conflict is likely and must be resolved twice. `except Exception: lang_fields = ()` logs nothing, so a broken registry silently reverts H1.
  - **Failure scenario**: a registry exception after an upstream change: incremental builds lose every changed -> unchanged plugin edge, with no log line.
  - **Fix**: move the work into one fork-owned function called once after each loop, for example `resolution_context_nodes = lang_registry.enrich_context(resolution_context_nodes, ctx_graph, identity)` (map context ids back to the persisted nodes), so each upstream file carries a single call line outside the loop; log the swallowed exception at debug level. E3's upstream PR (S006) should propose the same single extension point.
  - **Actioned**: `0975dff` test, `151ae36` fix — One `enrich_context(nodes, graph, identity)` call after each upstream loop (maps context nodes to persisted nodes by id); failure logged as a warning. (case 009)

- **S4-L4** ltm learning 1490 - Overstates that no `+lang.N` bump is needed for cache correctness.
  - **Problem**: the fingerprint hashes `graphify_lang` and the plugin packages only. The fork's own edits under `graphify/` that shape a per-file result (`lang_registry.augment_extractor` dispatch, the registry lookups in `extract.py`, `detect.py`) are covered only by the package version.
  - **Failure scenario**: a fork change to `graphify/lang_registry.py` dispatch shipped under an unchanged version string serves the old dispatch's cached results.
  - **Fix**: add a superseding learning: the fingerprint covers plugin code; fork edits under `graphify/` still need a version bump (which a release makes anyway). Optionally hash `graphify/lang_registry.py` into the fingerprint too.
  - **Actioned**: `bf76df9` test, `d21f7b2` fix, `f215fb0` docs — `graphify/lang_registry.py` hashed into the fingerprint; the other fork lines under `graphify/` still need a version change. (case 009)

- **S4-L5** `graphify_lang/templates/`, `README.md` - The incremental contract for resolvers is not documented where an out-of-tree author reads.
  - **Problem**: `[resolve] context_fields` and `_common.source_of` are described only in the spoke, case 008 and learning 1491. A third-party resolver that reads a field other than `node_kind` from another file's node, or compares `source_file` strings, works on full builds and loses its edges on every incremental one.
  - **Failure scenario**: a plugin following `templates/programming.toml` indexes callees by a custom `mylang_kind` field: `graphify watch` drops every changed -> unchanged edge, and nothing warns.
  - **Fix**: add the `[resolve]` section to both templates and a short "incremental builds" paragraph to the README's plugin-author section (context nodes: declared fields only, no refs, no edges but `contains` / `method` / `inherits`; compare paths via `source_of`). S006 may carry it; record it there if so.
  - **Actioned**: `f215fb0` — `[resolve] context_fields` with the context-node contract in all three templates; README plugin contract extended (fields read on other files' nodes, edges, `enrich_context`). (case 009)

### Nit

- **S4-N1** `graphify_lang/cc_kb/augment.py:137-150` - `cc_kb_links` is set on every Markdown page with a link to an existing `.md` file, in any repo, while the spoke's deviation says out-of-scope files "keep base nodes and edges". Measured: 36 non-harness pages / 47 KB on BentleyTools, and the field reaches JSON and GraphML exports. Harmless (needed for pair suppression when such a page is a cite target) but say so in the deviation and case 008 §3.
  - **Actioned**: `f215fb0` — Spoke deviation and case 008 §3 say `cc_kb_links` is set in any repo, with the measured sizes. (case 009)
- **S4-N2** `tests/lang/test_s4_build_coherence.py:208-212` - `test_h1_context_fields_union` omits `cargo_ws_deps`, the one field the cargo manifest declares; add it.
  - **Actioned**: `0975dff` — `cargo_ws_deps` in the union test. (case 009)
- **S4-N3** `docs/plans/05-S004-build-coherence.md:13` - §1 names the parity test `tests/lang/test_parity.py`; it landed in `tests/lang/test_s4_build_coherence.py`, and the deviations list does not say so.
  - **Actioned**: `f215fb0` — Spoke deviation names the real test file. (case 009)
- **S4-N4** `graphify_lang/registry.py:431-434` - The union of all manifests' fields is copied onto every context node of every language, and the names are generic (`version`, `visibility`, `accessor`): cargo's `pkg_*` nodes carry `version`, so ecschema's declaration forwards it for cargo too. Read-only and harmless today; upstream deliberately bounds what it forwards. Either scope the fields per manifest (by suffix of `source_file`) or prefix plugin-specific fields, as `bmake_includes` and `cc_kb_links` already are.
  - **Rejected**: `0975dff` (red test), removed in `151ae36` — Every resolver filters by its own suffixes before reading a field, so the union is a read-only superset; scoping by claimed suffix drops fields for a plugin split across manifests (vba declares `visibility` / `accessor`, `vba-cls` owns `.cls`), and prefixing renames persisted fields. (case 009)

### Enhancements

- **S4-E1** `tests/lang/test_s4_build_coherence.py`; `README.md` - Record the add-file class as a known incremental limit, not a cargo defect: an edge owned by an unchanged file to a newly added target appears only on the next full or cached build. Measured on `rr-s4` for cargo (`has_member`), cc-kb (`cites`), AutoLISP (`calls`) and upstream Python (`imports`, `calls`), so it is upstream's incremental semantics. Pin it with one strict-xfail parametrized test over those four and a README line. — Effort: LOW | Benefit: MINOR
  - **Actioned**: `0975dff`, `f215fb0` — Strict xfail `test_s4_e1_add_file_limit` over cargo `has_member`, cc-kb `cites`, AutoLISP `calls`, Python `calls` (each asserts that relation's edges only); the README known-limit line (from S6.2) now names the test. (case 009)

### Open questions (builder)

- **(a) A crate added under an unchanged workspace manifest gets `has_member` only on full or cached builds.** Recommendation: accept and document (S4-E1); do not special-case cargo. The probe shows the same miss for cc-kb, AutoLISP and upstream Python, so it is the general "unchanged file's edge to a new target" limit of incremental builds, and the next full or cached build repairs it. A cargo-only fix (members globs as a context field, edge emitted by the new crate) would give the edge a different owner than a full build does, so it would go stale when the workspace later excludes the crate. Revisit only if upstream solves the class.
- **(b) Toggling the fingerprint wipes the other AST namespace.** Recommendation: accept. It is upstream's own sweep (`graphify/cache.py:45-69`), it only costs one AST re-extraction (about 2 s for the 871-file claude-config Markdown corpus), and correctness is unaffected. Keeping several namespaces would need a wrapped or edited `_cleanup_stale_ast_entries` plus a bound on stale namespaces, which is more code than the problem is worth. The same thrash already happens, before S4, when two installs with different version strings (pipx release vs repo `.venv`) build the same repo. Add one README line under `GRAPHIFY_LANG_DISABLE`: toggling costs a full AST re-extract.

## S005 registry robustness

### Scope

- **Range**: `git diff rr-s4..rr-s5`, commits `ef2012a..a0b71b8` (12 commits) on `rr-s5`.
- **Spoke**: `docs/plans/05-S005-registry-robustness.md` (§3 result table and deviations); hub `docs/plans/05-review-remediation-cc-cr000-001.md` (owner decision D4); findings M1, E4, M5, M3, L6, L7, L8, L10 (closed as accepted), L13 (kept in fork, pinned) and N5 of `cc-CR000.001.md` (resolutions in `cc-CR000.002.md`).
- **Code**: fork-owned `graphify_lang/registry.py` (per-plugin load isolation, one entry-point group, `GRAPHIFY_LANG_PATH` loader, `load_errors`, `search_paths`, `augment_suffixes`, case-folded `[match] filenames`, `__wrapped__` on the augment wrapper), `graphify_lang/manifest.py` (`runtime` field), `graphify/lang_registry.py` (`watch_claims`, `check_languages`, fingerprint over path folders, no upper-case variants); upstream hook edits in `graphify/watch.py` (`_lang_claims` at the handler filter, `_batch_triggers_rebuild` and `_has_non_code`), `graphify/cli.py` (`lang list --check`, L8 logging), `graphify/detect.py`, `graphify/extract.py` (L8 logging); tests `tests/lang/test_s5_registry_robustness.py`, `tests/test_lang_registry.py` (728c6a3).
- **Verification**: read via `git show rr-s5:` / `git diff` only. Detached worktree of `rr-s5`, `PYTHONPATH` confirmed to import `graphify` and `graphify_lang` from the worktree, repo `.venv`, Python 3.12. Full suite: 6209 passed, 14 skipped. Each S5 test alone: 14 pass. Order probes: the `tests/lang` files, `tests/test_lang_*.py` and `tests/test_watch.py` in reverse order (421 passed), and `TestRegistryEnvironment` first, then S5, S4 and sniff tests (75 passed). No other test leaves a partial registry: every `_register_manifest` caller in `test_lang_sniff.py` runs under `clean_registry`, and `test_autolisp_plan02.py` resets on both sides. Probes (scratch folders, all on `rr-s5`):
  - **Path plugins**: two folders whose manifests both say `runtime = "plugin"`; a folder whose runtime is `wave` (stdlib, not yet imported) or `csv` (already imported); a runtime whose `extract` imports a sibling module lazily; `GRAPHIFY_LANG_PATH="."`; `GRAPHIFY_LANG_PATH="~nosuchuser_zz/plugins"`; a folder holding `pyproject.toml`.
  - **Fingerprint cost**: `import graphify.detect` with no path, a two-file folder, a folder with a symlinked `.venv`, and a folder with a 25 MB vendored package: 0.18, 0.18, 0.20 and 0.20 s (`rglob` does not follow the symlink).
  - **Watch claim**: `watch_claims` over the 565 `.md` files of the worktree; per claimed file, which part of the augment's output differs from the plain extractor; `_rebuild_code` on a 112 `.py` / 397 `.md` copy before and after one doc edit.
  - **L6**: every core lookup of a registry table lower-cases the path suffix first (`detect.classify_file`, `extract._get_extractor`, `cli` hook tails, `watch`); no case-sensitive `suffix in` lookup remains in `graphify/`.
  - **Upstream drift**: `upstream/v8` is 25 commits past the merge base; of the five hooked files only `graphify/extract.py` changed (one line, not near a hook).
- **Verdict**: M1 holds for errors inside a plugin, but not for a bad `GRAPHIFY_LANG_PATH` entry (S5-M1). E4, L6, L7, L8, L10, L13 and N5 are correct and pinned. M5 works as specified, but path plugins share Python's global module namespace, so two of them can silently swap extractors (S5-H1). M3 works; the `_has_non_code` change loses no upstream behaviour: `detect.classify_file` already returns CODE for a `[match]`-claimed `.yml` / `.xml` (S3), so `/graphify --update` never sent those files to the LLM, and a claimed file that writes no `needs_update` flag is consistent with it. The augment claim is broader than the spoke says (S5-M2). Good patterns: `_STATE` set before loading so a re-entrant plugin sees the partial state; `load_errors` as the one record behind both the warning and `--check`; `__wrapped__` instead of a second registry lookup; and a red-first strict xfail per finding again.

### Critical

None.

### High

- **S5-H1** `graphify_lang/registry.py:96-110` - Path plugins share `sys.modules`: two folders with the same `runtime` name get one extractor, silently.
  - **Problem**: `_path_manifest` puts the folder first on `sys.path` and calls `importlib.import_module(manifest.runtime)`. `import_module` returns any module already in `sys.modules` under that name without looking at `sys.path`, so the second folder's runtime is never imported. A runtime named like a module that is not yet imported (stdlib or installed) is imported from the folder and stays in `sys.modules` under the real name for the whole process.
  - **Failure scenario (measured)**: folders `a` (manifest `alpha`) and `b` (manifest `beta`), both `runtime = "plugin"`: `get_manifest('beta').extract(...)` returns `a`'s nodes (`from-a`), and `graphify lang list --check` prints `beta  ok` and exits 0. Runtime `wave` in folder `d`: after registry load, `import wave` anywhere in the process returns `d/wave.py` (no `wave.open`). Short generic names such as `plugin`, `extract` or `lang` are the likely ones for authors who copy a template. The fingerprint hashes both folders, so the cache namespace does not reveal the swap either.
  - **Fix**: after the import, require the module to come from the folder: `if not Path(module.__file__).resolve().is_relative_to(folder): raise ValueError(f"{manifest.runtime} resolves to {module.__file__}, not {folder}; give the runtime a unique top-level name")`. The error then reaches `load_errors` and `--check`. Also refuse a runtime whose top-level name is already in `sys.modules` from elsewhere before inserting the path, so the folder never shadows a real module. Document "unique top-level module name" in the README discovery bullet. Add a test with two folders sharing a runtime name (second one fails with that error, `--check` exits 1).
  - **Actioned**: `04990d7` test, `7ab39e7` fix — Path runtimes import as `graphify_lang_path._<sha256[:16] of folder>.<runtime>` (synthetic package per folder); `sys.path` untouched; nothing shadowed. (case 009)
  - **Owner decision** (S006 pass): a name clash stays a `--check` warning; private module names make it harmless. No change.

### Medium

- **S5-M1** `graphify_lang/registry.py:61-72`; `graphify/lang_registry.py:251-262` - A bad `GRAPHIFY_LANG_PATH` entry escapes the per-plugin isolation and disables plugins in the core tables, while `--check` reports all `ok`.
  - **Problem**: `Path(entry).expanduser().resolve()` and `importlib.metadata.entry_points(...)` run outside every `try`. `_STATE` is already set, so an exception leaves a partial state cached for the process (later folders never load) and propagates to the first caller. At import that caller is `_apply_registry` in `detect.py`, which logs "registry merge failed" and leaves `CODE_EXTENSIONS` without the plugin suffixes. `check_languages` only reads `load_errors`, which the exception never reaches.
  - **Failure scenario (measured)**: `GRAPHIFY_LANG_PATH="~nosuchuser_zz/plugins"` (`expanduser` raises `RuntimeError: Could not determine home directory`): `'.mki' in CODE_EXTENSIONS` is False (True without the variable), so every bmake file is left out of detection for the process, and `graphify lang list --check` prints nine `ok` rows and exits 0. The same happens for a corrupt distribution's metadata in `entry_points()`.
  - **Fix**: move the path handling into `_load_folder` under its `try` (`_failed(state, "plugin folder", entry, exc)`), and wrap the `entry_points()` call the same way (`_failed(state, "entry points", _GROUP, exc)`). Have `check_languages` also fail when `lang_registry._REGISTRY_AVAILABLE` is False after `apply_registry()`. Add the `~nosuchuser` entry to `test_m5_missing_dir_warns` and assert `.mki` stays in `CODE_EXTENSIONS`.
  - **Actioned**: `04990d7` test, `7ab39e7` fix — `expanduser`/`resolve` per entry and `entry_points()` inside a `try` (`load_errors` keys: the entry, `entry points`); `check_languages` calls `apply_registry()` and fails when `_REGISTRY_AVAILABLE` is False. (case 009)

- **S5-M2** `graphify/lang_registry.py:174-203`; `docs/plans/05-S005-registry-robustness.md:54` - The augment claim makes almost every linked `.md` code for `graphify watch`, not just cc-kb documents.
  - **Problem**: `watch_claims` counts a file when `extractor(path) != inner(path)`. The cc-kb augment adds the `cc_kb_refs` payload to any Markdown page with a relative link (the `code` and `up` lists), not only pages with a cc mention. The spoke deviation says "a plain `.md` still takes the doc path", and it calls the known limit "an edit that removes a doc's last cc mention". Upstream's `test_batch_modified_doc_only_does_not_rebuild` passes only because its fixture document has no links.
  - **Failure scenario (measured)**: 460 of the worktree's 565 `.md` files are claimed. Of these, 421 carry no cc mention at all (only `code` and `up` refs). So a doc-only edit in any repo with cross-linked docs now runs `_rebuild_code` as well as writing the `needs_update` flag: 3.6 s on a 112 `.py` / 397 `.md` copy, and the cost grows with the repo. The claim check itself is cheap (1.1 ms a file, 0.6 s for all 565). The real limit is "an edit that removes a page's last relative link of any kind", and the stale edges stay until the next rebuild.
  - **Fix**: the claim is right for correctness, because the cc-kb resolver turns `code` and `up` refs into edges, so keep the rule. Correct the spoke deviation and add one README line under discovery: "`graphify watch` rebuilds on an edit of any Markdown page with a relative link". State the real known limit in the `watch_claims` docstring. Add a case to `test_m3_watch_triggers_on_claimed_xml_yml_toml_md` with a plain linked non-cc page (claimed) and a page with no links (not claimed), so a narrowing or widening of the rule is deliberate. If the rebuild cost matters later, scope the augment's payload to the harness roots it already recognises.
  - **Actioned**: `04990d7` test, `29d91ea` engine, `63a8e2c` cc-kb — Narrowed, as the owner directed (the review proposed keeping the rule): `LanguageManifest.watch` predicate (path plugin: `WATCH`), `registry.augment_watch_claims` (no predicate: old rule; failing predicate: claims). (case 009)
  - **Owner follow-up**: `fc1a803` test, `4fd2a60` fix — every `docs/cc-*.md` is also claimed by name; re-measured 46 / 646 / 847 claimed (case 009 S006).

- **S5-M3** `graphify_lang/registry.py:69-71` - A relative `GRAPHIFY_LANG_PATH` entry runs code from the current directory (security hardening).
  - **Problem**: an entry resolves against the working directory, and `_path_manifest` imports the `runtime` module of every `*.toml` there. Every graphify process imports the registry, including the MCP servers and the git hooks (`graphify hook`), which run in whatever repository the user is in.
  - **Failure scenario (measured)**: `GRAPHIFY_LANG_PATH="."` with the working directory in folder `a` loads `a/plugin.py` (`search_paths() == [.../probe/a]`). A user who sets `.` or `plugins` in a shell profile then executes a cloned repository's `*.toml` runtime on the next `graphify` call or commit hook in that clone. This is like `.` in `PATH`.
  - **Fix**: after `expanduser()`, reject a non-absolute entry through `_failed(state, "plugin folder", entry, "must be an absolute path")`, and say so in the README discovery bullet. Add a test.
  - **Actioned**: `04990d7` test, `7ab39e7` fix — A non-absolute entry after `~` expansion is a load error "must be an absolute path". (case 009)

### Low

- **S5-L1** `graphify_lang/registry.py:104-108` - A path plugin that imports a sibling module lazily fails at extraction time.
  - **Problem**: the folder is on `sys.path` only while the runtime is imported. An `import helper` inside `extract()` runs later, when the folder is gone.
  - **Failure scenario (measured)**: `extract()` doing `import helper` (`helper.py` beside the runtime) raises `ModuleNotFoundError: No module named 'helper'` on every call. Upstream's `_safe_extract` then drops each file of that language with one warning. The load itself succeeds and `--check` says `ok`.
  - **Fix**: document "import the plugin's own modules at module top, or ship them as a package (`runtime = "mypkg.extract"`)" in the README discovery bullet. The test fixture already uses a package. Keeping the folder on `sys.path` would widen S5-H1, so don't.
  - **Actioned**: `04990d7` test, `7ab39e7` fix — Relative imports (`from . (case 009)

- **S5-L2** `graphify_lang/registry.py:88-91,141` - Duplicate language names are handled two ways.
  - **Problem**: a path manifest that repeats a registered name is a load error, but an entry point that repeats one overwrites the first in `_register_manifest` with no warning. The same folder listed twice in `GRAPHIFY_LANG_PATH` turns every manifest in it into an "already registered" error.
  - **Failure scenario**: a third-party distribution that ships a manifest named `autolisp` silently replaces the fork's AutoLISP plugin (its suffixes, resolver and `context_fields`), and `--check` shows one `autolisp ok` row.
  - **Fix**: move the duplicate check into `_register_manifest`, so both paths raise and `_failed` records it. De-duplicate the resolved folders before loading.
  - **Actioned**: `04990d7` test, `7ab39e7` fix — Discovery registers through `_register_new`: first name wins, second (entry point or path) is a load error; a repeated folder loads once. (case 009)

- **S5-L3** `graphify_lang/registry.py:86` - Every `*.toml` in a path folder is a manifest.
  - **Problem**: a folder that also holds a `pyproject.toml`, `ruff.toml` or `Cargo.toml`, for example a plugin checkout used in place, reports each one as a failed plugin.
  - **Failure scenario (measured)**: `pyproject.toml` in a path folder: warning "missing required field: language.name ...", and `graphify lang list --check` exits 1 with nothing wrong with the plugins.
  - **Fix**: skip a `*.toml` without a `[language]` table (debug log), or document "a `GRAPHIFY_LANG_PATH` folder holds only manifests" in the README bullet. The first is one `tomllib` check before `from_toml`.
  - **Actioned**: `04990d7` test, `7ab39e7` fix — A `*.toml` that parses without `[language]` is skipped (debug log); an unparsable one still reaches `from_toml` and is reported. (case 009)

### Nit

- **S5-N1** `graphify/cli.py:3879-3881`, `graphify/extract.py:6886,6924`, `graphify/detect.py:537` - The L8 `import logging` inside an `except` in a function makes `logging` a local name for the whole of `dispatch_command`, `_get_extractor` and `classify_file`. Upstream uses the same idiom (`extract.py:7964`), and nothing breaks today. But if upstream adds a module-level `import logging` and uses it earlier in one of these functions, the rebase gives an `UnboundLocalError` on that path only. Use `import logging as _lang_logging`, or one fork helper, in the seven copies.
  - **Actioned**: `04990d7` test, `748befd` fix — `import logging as _lang_logging` at all seven L8 hook handlers (cli 1, detect 2, extract 4). (case 009)
- **S5-N2** `tests/lang/test_s5_registry_robustness.py:242-257` - `test_m3_watch_handler_sees_claimed_xml` starts `watch()` in a daemon thread that never stops. Its observer keeps running for the rest of the session, and once the monkeypatch is undone an event under that `tmp_path` would run the real `_rebuild_code`. The 5 s deadline is also timing-based. Stop the loop from the test (patch `watch_mod.time.sleep` to raise `KeyboardInterrupt` once `calls` is non-empty, which runs `observer.stop()` in `watch`'s `finally`), then join the thread.
  - **Actioned**: `f4a4cc8` — `watch`'s `time` replaced by a clock whose loop sleep raises `KeyboardInterrupt` once the rebuild ran (10 s deadline), so `watch` stops its observer; the thread is joined and asserted dead. (case 009)
- **S5-N3** `graphify/watch.py:2406` - The handler calls `_lang_claims` (which can sniff the file) before upstream's cheaper dotfile and `graphify-out` filters, so `.xml` / `.toml` writes under `.git/` or dot-folders are opened on the observer thread. Moving the check below those filters would edit a second upstream line, so leave it unless profiling shows a cost. On rebase risk: the three watch hooks are inline edits of upstream expressions (`:2314`, `:2326`, `:2406`), each a one-token conflict if upstream touches them. Upstream has not touched them since the merge base (25 commits).
  - **Rejected** (no change): As the review advises: moving `_lang_claims` below the dotfile / `graphify-out` filters edits a second upstream line; no profile shows a cost. (case 009)

### Enhancements

- **S5-E1** `README.md` (discovery bullet), `graphify_lang/templates/` - Add a minimal path-plugin example (one manifest, one module with `extract` and optional `RESOLVER`) with the rules S5-H1, S5-M3, S5-L1 and S5-L3 imply: an absolute folder, a unique top-level module name, imports at module top, and only manifests in the folder. The fingerprint covers `.py` / `.toml` only, so data files a plugin reads (queries, JSON tables) do not move the cache namespace; say so, as for entry-point plugins. — Effort: LOW | Benefit: HIGH
  - **Actioned**: `61d8388` — `graphify_lang/templates/path-plugin/` (`example.toml`, `example_lang.py`), shipped as package data and loaded by `test_s5_e1_path_plugin_template_loads`; README rules for absolute entries, manifests only, private package, relative imports, first name wins, fingerprint `.py`/`.toml` only, watch predicate. (case 009)

## S006 tests, docs and pre-release

### Scope

- **Range**: `git range-diff 4c73561..rr-s5 4000de1..9351e4c` for the S6.0 rebase (old base `4c73561`, 0.9.67; new base `upstream/v8` `4000de1`, 0.9.68), then `git diff 9351e4c..5dad25c`, commits `5a53250..5dad25c` (6 commits) on `rr-s6`. S6.4 to S6.6 (release, rebuild, close-out) are deferred by the owner and not reviewed.
- **Spoke**: `docs/plans/05-S006-tests-docs-and-release.md` (§3 result table and deviations); hub `docs/plans/05-review-remediation-cc-cr000-001.md` (D2, D5); findings M11, M12, N1, N2, E3 of `cc-CR000.001.md`.
- **Code and docs**: `tests/lang/conftest.py`, `tests/lang/fixtures/corpus/` (synthetic ast-grep project, synthetic CRLF `ThisWorkbook.cls`), the five parametrized corpus tests (`test_astgrep.py`, `test_bmake.py`, `test_ecschema.py`, `test_vba.py`, `tests/test_lang_sniff.py`), `pyproject.toml` markers; `README.md`, `.claude/CLAUDE.md`, `docs/plans/` statuses; `docs/upstream/README.md` and `pr-01`..`pr-04`. The S6 commits touch no file under `graphify/` or `graphify_lang/`.
- **Verification**: read via `git show 5dad25c:` / `git diff` only. Detached worktree of `5dad25c`, `PYTHONPATH` confirmed to import `graphify` and `graphify_lang` from the worktree, repo `.venv`, Python 3.12.3. Full suite: 6238 passed, 14 skipped (matches `README.md:410`). `graphify lang list` rows match the README Status table; `--check` prints 9 `ok`, exit 0. Probes:
  - **Rebase**: `range-diff` shows 103 of 104 commits `=`; the one `!` (`7b6eaf3` -> `af152d9`) differs only in conflict context (upstream's Discord URL in deleted README lines; `0.9.67` -> `0.9.68` on the replaced version line of `pyproject.toml` and `uv.lock`). Tree check: for every file upstream changed between the bases, `diff(rr-s5, 9351e4c)` equals `diff(4c73561, 4000de1)` except `README.md`, `pyproject.toml`, `uv.lock` (fork-owned version and README); the only extra path is the learnings sidecar. No fork change was lost or altered. `docs/UPSTREAM-README.md` equals `4000de1:README.md`. No upstream test file and nothing under `graphify/extractors/` differs from `4000de1`.
  - **Upstream 0.9.68 against the fork hooks**: of the hooked files upstream changed only `extract.py` (one line: `resolution_context_nodes=` passed to `_augment_symbol_resolution_edges`) and `__main__.py` (`_reexec` for the hash-seed re-exec on Windows). The new `resolution.py` block indexes context nodes by `(path, label)` for JS/Python symbol facts; plugin context nodes (with the fork's extra `context_fields` and `_lang_source_file`) enter that index but no JS/Python fact names their paths, so no edge changes. `watch.py`, `cli.py`, `detect.py`, `cache.py` are unchanged upstream.
  - **M12 samples**: astgrep sample: 3 rules (2 tested, 1 untested), 2 `tested_by`, 1 util `references` edge. bmake fixture: 4 `%include` directives, 3 resolved, 1 unresolved, 3 `imports`. ecschema fixture: classes in 3 files plus the broken-XML file (0, parse warning). VBA sample: 1 class, 4 subs, 1 file node. Every assertion of the five tests is non-vacuous on its sample. The samples are synthetic (the VBA `VB_Base` GUID is Excel's public `ThisWorkbook` class id).
  - **PR drafts**: each `diff` block, extracted with the `docs/upstream/README.md` awk line, applies with `git apply --check` to a detached `4000de1` worktree; its test passes there with `PYTHONPATH` on that worktree (2 / 3 / 3 / 2 passed). Full upstream suite per draft not re-run.
  - **Version**: `graphify/cache.py:957` namespaces the AST cache as `v{_EXTRACTOR_VERSION}-s{schema}`, and `lang_registry` appends the plugin-set fingerprint, which hashes `graphify_lang` code but not core `graphify/` code. `packaging`: `0.9.67+lang.4 < 0.9.68` is True; `0.9.68+lang.4 > 0.9.68` is True.
- **Verdict**: the rebase is clean and complete. M12 is correct and the samples exercise the code. M11, N1 and N2 are correct against the code; every symbol the README cites exists at `5dad25c`, with the inaccuracies below. The four PR drafts are minimal, apply cleanly and have red/green tests; pr-01 leaves the AST-cache question open (S6-M2). Release version: **`0.9.68+lang.4`** (S6-M1). Good patterns: the rebase kept every conflict to fork-owned lines; each corpus test keeps its private case under one marker with a `corpus:` skip reason; each PR draft names how the fork would switch to it.

### Critical

None.

### High

None.

### Medium

- **S6-M1** `pyproject.toml:7`, `uv.lock:1099`; `docs/plans/05-review-remediation-cc-cr000-001.md:3,13,44,78`; `docs/plans/05-S006-tests-docs-and-release.md` §1 'Release', §2 S6.4 - The branch says `0.9.67+lang.3` on a 0.9.68 base, and the plan still releases `0.9.67+lang.4`.
  - **Problem**: PEP 440 orders a local version after its public version only: `0.9.67+lang.4` sorts before stock `0.9.68`. The README's own release rule (`README.md:524`) is `<upstream version>+lang.<n>`, and the rollback line installs `==<upstream version>`.
  - **Failure scenario**: with `0.9.67+lang.4` installed, `pipx upgrade graphifyy` (or `pip install -U graphifyy` in any venv) sees PyPI `0.9.68` as newer and silently replaces the fork with stock graphify, dropping all nine plugins; with `0.9.68+lang.4` it does not. `_check_skill_version` (`graphify/__main__.py:209-231`) compares `_version_tuple`: a skill stamped `0.9.68` by a stock install elsewhere gives `(0, 9, 68) > (0, 9, 67, 4)` and a permanent 'package is older, upgrade' warning. `graphify --version` would also misstate the core that runs. (The AST cache is safe either way: any version change moves the namespace.)
  - **Fix**: in S6.4 set `version = "0.9.68+lang.4"` in `pyproject.toml` and refresh `uv.lock` (`uv lock`, so CI's `--frozen` sync and the lock agree), tag `v0.9.68+lang.4`, and change the hub (lines 3, 13, 44, 78) and spoke (§1, S6.4 check `graphify --version`) to that version. Close the spoke's 'Version' deviation with this decision.
  - **Actioned**: `0c5c58f` — Hub and spoke say `0.9.68+lang.4` (owner-confirmed); spoke 'Version' deviation settled; S6.4 bumps `pyproject.toml` and runs `uv lock`. (case 009)

- **S6-M2** `docs/upstream/pr-01-language-plugin-entry-points.md` (Change, Diff, Fork side) - Plugin extractors bypass the AST cache's version namespace, so a plugin upgrade replays stale results.
  - **Problem**: upstream's AST cache is valid only for the extractor code that wrote it (`graphify/cache.py:23-27`: "namespaced by package version"). pr-01 lets code from other distributions produce cached extractions, but the namespace still carries only graphify's version. The fork hit exactly this (cc-CR000.001 M2, E1) and fixed it with the plugin-set fingerprint; the draft lists the fingerprint only as a later fork feature.
  - **Failure scenario**: a user upgrades a `graphify.languages` plugin (say an extractor fix) without changing graphify; `graphify update` serves every unchanged file of that language from the old cache, and the fix never shows until the cache is deleted. An upstream reviewer who knows `cache.py` will ask for this.
  - **Fix**: in `language_plugins.plugins()`, collect `(ep.dist.name, ep.dist.version)` for each loaded entry point and expose a short hash; have `cache.py` append it to the AST namespace when non-empty (`v{version}-s{schema}-p{hash}`), so no plugin means no change. Add a test: two dist-info versions of one plugin give two cache directories. If kept out of the PR, say so under 'Change' as a known limit.
  - **Actioned**: `961b970` — pr-01 adds `language_plugins.fingerprint()` (loaded plugin dist names + versions) and `cache_dir` appends `-p<hash>` (no plugin: unchanged); test: two plugin versions, two cache dirs. (case 009)

### Low

- **S6-L1** `docs/upstream/pr-01-language-plugin-entry-points.md` (Fork side) - "the fork would then register through this group and drop its own `detect.py` / `extract.py` blocks" overstates the seam.
  - **Problem**: `_DISPATCH.setdefault` never replaces a built-in, and the draft has no sniff, match or override. Of the fork's plugins only `.mnl`, `.dcl`, `.bas`, `.frm`, `.mki`, `.mke` could move; `.lsp` (AutoLISP `overrides`), `.cls` (sniff against Apex), `.xml` / `.yml` (`[match]` data suffixes) and the two augments could not, so the fork's blocks stay.
  - **Failure scenario**: an upstream reviewer or the owner reads the PR as removing the fork's core diff, and it would not remove the part that carries the fork's first target, `.lsp`.
  - **Fix**: say which plugins can use the seam as drafted, and add `overrides` (a plugin taking a built-in suffix) to the list of follow-up seams.
  - **Actioned**: `961b970` — Fork side names the plugins that can move (`.mnl`, `.dcl`, `.bas`, `.frm`, `.mki`, `.mke`) and those that cannot; `overrides`, sniff, `[match]`, augments listed as follow-up seams. (case 009)

- **S6-L2** `docs/upstream/pr-03-watch-code-path-claims.md` (Fork side; Diff, handler hunk) - The fork-side text repeats a claim S5-M2 measured false, and the draft calls every claim before the cheap path filters.
  - **Problem**: the draft says the cc-kb claim "counts a file only when the augment adds something, so a plain doc edit does not rebuild"; S5-M2 measured 460 of 565 `.md` files claimed, 421 of them with no cc mention. In the diff, `_claimed_as_code(path)` sits at the suffix filter, above the handler's `filter_parts` check for dot-folders and `graphify-out`.
  - **Failure scenario**: every write under `.git/` (object files have no suffix) runs every registered claim on the observer thread; a claim that sniffs opens the file. Unlike the fork's hook (S5-N3), the upstream PR is free to place the check.
  - **Fix**: correct the Fork side sentence once S5-M2 is settled. In the draft, move the claim test below the `filter_parts` guard (keep the suffix test where it is and add `or _claimed_as_code(path)` after the dot/`graphify-out` checks), and add a `.git/objects/xx` event to the handler test that must not call the claim.
  - **Actioned**: `6dc7ff6` — pr-03 claim runs after the ignore / dot / `graphify-out` filters; handler test adds a `.git/objects` write that must not reach the claim. (case 009)

- **S6-L3** `README.md:462-464`; `.claude/CLAUDE.md` ('Tracking upstream') - "The fork's `v8` is at the same commit as `upstream/v8`" is false after S6.0.
  - **Problem**: local `v8` and `origin/v8` are at `4c73561`, 25 commits behind `upstream/v8` `4000de1`. The instrument given, `git rev-list --count upstream/v8..v8` = 0, only checks one direction, so it passes.
  - **Failure scenario**: a branch cut "off `v8`" as rule 1 says starts on the old base, and CI's `v8` trigger tests the old upstream.
  - **Fix**: fast-forward (`git branch -f v8 upstream/v8`, push in S6.6 with the other refs), and make the instrument `git rev-list --left-right --count v8...upstream/v8` = `0	0`.
  - **Actioned**: `c0135a0` (+ ref push) — `v8` and `origin/v8` fast-forwarded to `4000de1`; README and `.claude/CLAUDE.md` give the two-way instrument and the fast-forward steps. (case 009)

- **S6-L4** `README.md:186-201` - The manifest table mixes dataclass attributes and TOML keys and is incomplete.
  - **Problem**: it lists `extract` as required `Callable` (the TOML key is the required `[extract] runtime`, `graphify_lang/manifest.py:225-227`), `grammar` / `extra` (TOML `[grammar] module` / `extra`), and `resolver` as `LanguageResolver` (TOML gives a string). It omits `schema`, `case_insensitive`, `builtins_file` / `builtins_prefixes`, which the shipped manifests use. It lists `fixture`, which no manifest sets (`manifest.py:248` `fixture=None`) and nothing reads.
  - **Failure scenario**: a `GRAPHIFY_LANG_PATH` author writes a manifest from this table, omits `[extract] runtime`, and gets "missing required field: extract.runtime" with no README line explaining it.
  - **Fix**: add a TOML key column (`[language] name`, `[extract] runtime`, ...), add the omitted keys, and drop the `fixture` row (N3-style: delete the dataclass field too if nothing reads it).
  - **Actioned**: `fc1a803` test, `5a8fecc` fix — README table keyed by TOML key, with `schema`, `case_insensitive`, `builtins_file` / `builtins_prefixes`, `[extract] runtime` required; `fixture` row and `LanguageManifest.fixture` removed. (case 009)

- **S6-L5** `README.md:118-121,130-132` - Design goals 1 and 4 still describe superseded behaviour in the present tense.
  - **Problem**: goal 1 names discovery "by being a module under a `graphify_lang/` namespace package"; line 244 says "There is no namespace-package scan". Goal 4 says "The registry starts empty; with no language package installed the fork behaves as upstream"; the wheel ships nine plugins, so only `GRAPHIFY_LANG_DISABLE=1` gives upstream behaviour.
  - **Failure scenario**: a reader takes goal 4 as the fork's default and expects stock output from a plain install.
  - **Fix**: mark the section as the original goals and point to 'Shared suffixes, data files and augments' for the settled answers, or edit goal 1 to the entry-point / `GRAPHIFY_LANG_PATH` form and goal 4 to "with discovery off (`GRAPHIFY_LANG_DISABLE=1`) the fork behaves as upstream".
  - **Actioned**: `c0135a0` — Goal 1: entry points or `GRAPHIFY_LANG_PATH`; goal 4: `GRAPHIFY_LANG_DISABLE=1` gives upstream behaviour. (case 009)

### Nit

- **S6-N1** `docs/upstream/pr-02-resolver-context-fields.md` ('Fork finding'), `docs/upstream/pr-03-watch-code-path-claims.md` ('Fork finding') - The cited fork commits `2adf7bc`, `cd55efb`, `32d4618`, `227c194` are pre-rebase hashes, reachable only from `rr-s4` / `rr-s5`, not from `rr-s6`. Cite the rebased `03dfe51`, `cc0e296`, `f8219a1`, `ae768d4`, or the symbols.
  - **Actioned**: `6dc7ff6`, `82bd683` — pr-02 cites `03dfe51`, `cc0e296`; pr-03 cites `f8219a1`, `ae768d4` (all on `rr-s6`/`rr-fix`). (case 009)
- **S6-N2** `tests/lang/fixtures/corpus/vba/ThisWorkbook.cls`; `tests/lang/test_vba.py` (`test_bim_chk_this_workbook` docstring) - The CRLF the docstring names is not pinned: there is no `.gitattributes` entry, and an LF copy of the sample gives the same result (measured: 1 class, 4 subs), so an `autocrlf=input` commit or a future `* text=auto` would lose it silently. Add `tests/lang/fixtures/corpus/vba/*.cls -text` and assert `b"\r\n" in path.read_bytes()` in the sample case.
  - **Actioned**: `3e02a91` — `tests/lang/fixtures/corpus/vba/.gitattributes` `*.cls -text` (fork-only file, upstream `.gitattributes` untouched); the sample case asserts CRLF. (case 009)
- **S6-N3** `README.md:503` - "what CI can run" names `-m "not corpus and not perf"`, but `.github/workflows/graphify-lang-ci.yml:33` runs `-m 'not perf'` (corpus cases run and skip). Align the workflow, or reword to "the same set CI passes".
  - **Actioned**: `c0135a0` — README runs CI's own `-m 'not perf'`. (case 009)
- **S6-N4** `tests/lang/conftest.py:16-17` - `corpus_ls` splits `git ls-files` output on whitespace, so a tracked name with a space becomes two bogus paths (`FileNotFoundError` in the read). Use `git ls-files -z` and `split("\0")`.
  - **Actioned**: `fc1a803` test, `88a1b43` fix — `corpus_ls` reads `git ls-files -z`. (case 009)

### Enhancements

- **S6-E1** `docs/plans/05-S006-tests-docs-and-release.md` (S6.0 row) - Record the tree-level rebase instrument next to the pytest check, so the next rebase repeats it: `git range-diff <old-base>..<old-tip> <new-base>..<new-tip>` (only conflict commits may show `!`), plus, for each file in `git diff --name-only <old-base> <new-base>`, the upstream delta equals `git diff <old-tip> <new-tip> -- <file>` except fork-owned files. It answers "was a fork change lost" in seconds. — Effort: TRIVIAL | Benefit: NEUTRAL
  - **Actioned**: `a737cdf` — S6.0 check column records the range-diff plus per-file upstream-delta instrument. (case 009)
