# Case 009 — plan 05 review-fix pass

Review report: `.claude/docs/cc-CR000.003.md` (plan 05 spoke reviews). One H2
section per spoke; each lists every finding id with its status, for a later
part to copy into the report.

**Branch:** `rr-fix` (from `rr-s6` `5dad25c`, on `upstream/v8` 0.9.68)

## S001

**Tests:** `.venv/bin/python -m pytest tests/ -q`: baseline 6238 passed,
14 skipped; after 6252 passed, 14 skipped (14 new tests). Red-first: each fix
commit removes a strict `xfail(raises=...)` marker added by the test commit
before it. `git diff upstream/v8...HEAD -- graphify/extractors/` empty;
`tests/lang_baseline.txt` and `tests/upstream_tables.json` unchanged.

| Id | Status | Commit(s) | Note |
|:--|:--|:--|:--|
| S1-H1 | actioned | `548b209` test, `b282fce` fix | A non-scalar `id` skips the document; `testDir` kept only when `str`/`int`. |
| S1-M1 | actioned | `4bf2374` test, `79ca519` fix, `8065360` test (scaling ratio, not wall clock) | One pass over indented keys per document; 20 000 utils 18.93 s -> 0.94 s locally; llm-linter-tool 82 YAML files output identical. |
| S1-L1 | actioned | `59909c2` test, `b0b4af3` fix | `action_callees` returns no callees on `RecursionError`. |
| S1-L2 | actioned | `401de76` test, `3c4de2d` fix | `yaml.YAMLError` keeps "document skipped (YAML does not parse)"; any other exception is logged by type with "nodes added before it are kept". Partial nodes are kept, not rolled back. |
| S1-L3 | actioned | `6580837` | Docstring states the fallback loss; test pins `contains`-only edges and no refs. |
| S1-L4 | actioned | `bba2f84` test, `d5793c2` fix | `UnicodeDecodeError` and `RecursionError` give a one-line error. |
| S1-L5 | actioned | `4950b5c` test, `d6f0285` fix | `runtime` / `resolver` must be strings; `hook_suffixes` and `overrides` dot-checked. |
| S1-L6 | rejected | — | Already resolved by `87f78fa` (plan 05 S3.5): PyYAML is a runtime dependency and the module-level `skipif` was deleted. |
| S1-N1 | actioned | `0b8e5ba` (fixture), `0d1f41d` (`cc-CR000.002.md`) | The limit is raised by `_raise_recursion_limit()` when extraction runs, not on import. |
| S1-N2 | actioned | `3782129` | `_common.line_index(text)`, built per extraction and passed down; no module `lru_cache`. |
| S1-N3 | rejected | — | Process advice, no code change; followed in this pass (the S1-L1 and S1-L4 red tests pin the recursion limit in the red commit). |
| S1-N4 | actioned | `0b8e5ba` | `_timed` runs without `check=True` and fails with the child's stderr. |
| S1-E1 | actioned | `548b209` | Bombs at rule `id`, test `id` and `testConfigs[].testDir`; shared `matches:` credited once. |
| S1-E2 | actioned | `954a22b` test, `e5d5c99` fix | Documents over 1 000 000 characters skipped with a warning. |

## S002

**Tests:** `.venv/bin/python -m pytest tests/ -q`: before 6252 passed, 14 skipped;
after 6263 passed, 14 skipped (11 new: `tests/lang/test_ci_workflows.py` 10,
`test_s3_shared_core.py::test_s2_n5_one_tomllib_shim` 1). Red-first as in S001;
the E2 parse guard is green by design (a regression guard). `git diff
upstream/v8...HEAD -- graphify/extractors/` empty; `tests/lang_baseline.txt`
and `tests/upstream_tables.json` unchanged; `publish.yml` / `release-graph.yml`
keep only their one guard line against `upstream/v8`.

**CI:** push run 36228277830 on `cc729db` green (3.10 6258/19, 3.12 and 3.13
6257/20; security-scan gating steps pass: `pip-audit --skip-editable` "No known
vulnerabilities found", `bandit -r graphify_lang -ll` 0 issues). Dispatch run
36228295041 exercised the `wheel` job: built `graphifyy-0.9.67+lang.3`, installed
into a clean venv, `graphify lang list --check` 9 languages ok.

**Warnings (S001 saw 39 vs 19):** diffed the warning sets of `rr-s6` `5dad25c`
(`git archive` into a scratch dir, `PYTHONPATH` to it, imports confirmed to
resolve there) against HEAD, same `.venv`. No fork-caused new warning. HEAD
in the repo: 20 in 4 of 5 runs, 40 in 1. The extra ones in the 39/40 runs are
the nondeterministic `multiprocessing/popen_fork.py` "multi-threaded, use of
fork()" DeprecationWarning (upstream tests; the scratch baseline also hit it,
plus 11 git-dependent `test_skillgen` failures a non-git tree causes). 19 -> 20:
hypothesis' "Skipping collection of '.hypothesis'" UserWarning, from the local
untracked `.hypothesis/` dir and upstream's `norecursedirs`. Pre-existing and
fork-owned but not new: `graphify_lang/queries.py:96` "int argument support is
deprecated" (7 tests; a grammar binding returns an int; upstream
`solidity.py:81` has the same).

| Id | Status | Commit(s) | Note |
|:--|:--|:--|:--|
| S2-M1 | actioned | `89b12ff` test, `2352a06` lock, `3a8f0dc` fix, `cc729db` docs | `pip-audit --skip-editable`, gating, job syncs all extras. Lock bump cleared all 14 advisories: anyio 4.15.1, cryptography 50.0.1, pip 26.2.1, soupsieve 2.10 (typing-extensions 4.16.0 came with anyio); none left unbumped. Full locked set (`uv export --all-extras` + `pip-audit -r --no-deps`) clean. "security-scan success" corrected in `cc-CR000.002.md` M8 and spoke S2.5. |
| S2-M2 | actioned | `89b12ff` test, `644cc9c` fix | Gating `bandit -r graphify_lang -ll`; combined scan kept informational. |
| S2-L1 | actioned | `89b12ff` test, `50363e0` fix | `fail-fast: false`. |
| S2-N1 | actioned | `89b12ff` test, `50363e0` fix | Top-level `permissions: {contents: read}`. SHA pinning not done: the reviewer's own condition (no secrets, read token) still holds. |
| S2-N2 | actioned | `89b12ff` test, `50363e0` fix | `tags: ['v*\+lang.*']`. |
| S2-N3 | actioned | `39fce02` | Suggestion plan and Metrics show open findings only (all 0). |
| S2-N4 | actioned | `6614b24` | T17.4-T17.6 and Sources marked deleted in S2.3 (`1f8a2e4`). |
| S2-N5 | actioned | `333a33d` test, `b12630a` engine, `76cbe8f` cargo | One shim in `manifest.py`, bound as `tomllib`; kept there, not `_common.py`, because `_common` imports `manifest` (circular otherwise). |
| S2-E1 | actioned | `89b12ff` test, `3232862` fix | `wheel` job on tags (and `workflow_dispatch`): `uv build --wheel`, clean `uv venv`, `graphify lang list --check`. |
| S2-E2 | actioned | `89b12ff` | `test_s2_e2_every_workflow_parses` over all 4 workflows. |
