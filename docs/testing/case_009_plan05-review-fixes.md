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

## S003

**Tests:** `.venv/bin/python -m pytest tests/ -q`: before 6263 passed, 14 skipped;
after 6275 passed, 14 skipped (12 new: `test_s3_shared_core.py` 8 incl. two
`schema` params, `test_rules.py` 4). Red-first as in S001; the S3-E1 unit
tests and the S3-N3 reader check are green guards. The fork's
`queries.py` "int argument support is deprecated" warning is gone (only
upstream `solidity.py:81` keeps it). `git diff upstream/v8...HEAD --
graphify/extractors/` empty; `tests/lang_baseline.txt` and
`tests/upstream_tables.json` unchanged.

**Corpus (S3-E2 script):** `.venv/bin/python tools/compare_corpus.py --before
9d8cda4 --after HEAD autolisp=~/repos/autolithp vba=~/repos/bim-chk`
(autolithp `d5a2074`, 254 files: 10691 nodes / 10691 ids / 25584 edges / 1
dangling; bim-chk `d7ba56f`, 33 files: 416 / 416 / 1114 / 0). Before = after,
node and id-free edge diffs 0 on both; the autolithp row matches case 008's
"after" row.

| Id | Status | Commit(s) | Note |
|:--|:--|:--|:--|
| S3-M1 | actioned | `80f5d33` test, `bf00dbd` fix | `resolve_ref_id` falls back to a pre-S3 ref's `source` id, else None; `refs_of` and the ecschema resolver drop a ref with none. The E1 plugin-set fingerprint already covers the reported scenario: every namespace is `v<version>-lang<fp>-s<schema>` (measured `v0.9.67+lang.3-langccd5d632ef30-s4`), which no pre-E1 build wrote, so a pre-S3 entry is never read. The `+lang.4` bump is left to the release, as instructed. |
| S3-L1 | actioned | `80f5d33` test, `ab276d1` fix | `rules.build(..., package=)`: a `post_file` hook may name `graphify_lang.*` or the caller's own package, nothing else. D1 kept: a manifest is data (a GRAPHIFY_LANG_PATH folder or a third-party package) and cannot name arbitrary modules; the caller of `build` is code that already runs and vouches only for its own package. Templates and the `rules.py` docstring say so. |
| S3-L2 | actioned | `80f5d33` test, `8c02786` fix | `rules.Out` keeps a recursive reference's self-loop (`Sink.edge(self_loop=True)`), as upstream's built-ins do; plugin sinks still drop `src == tgt`. `err.lsp` call count unchanged (29). |
| S3-L3 | rejected (moot) | — | `953efd6` (plan 05 S4.3, H3) deleted the `lru_cache` on `_is_root`: harness roots are derived from the graphed nodes inside each `resolve` call, and `graphify_lang/cc_kb/` holds no process cache. |
| S3-N1 | actioned | `80f5d33` test, `115e717` fix | `#` starts a builtins comment only before a space or the line end; `is_builtin('#&/')` True again. |
| S3-N2 | actioned | `80f5d33` test, `a716186` fix | `schema` must be the integer 1 or `"v1"` (`true`, `1.0` rejected); message says `must be 1 or "v1"`. |
| S3-N3 | actioned | `80f5d33` | `test_s3_n3_every_read_key_has_a_reader_in_code`: each `_READ` key's leaf must be a string literal in `graphify_lang`. `extract.runtime` is now read to import a GRAPHIFY_LANG_PATH plugin (`registry._path_manifest`, S5), so it is not validation-only. |
| S3-N4 | actioned | `80f5d33` test, `0aaf7f0` fix | `Out.ref` -> `name_ref`, `Out.result` -> `resolved`, `Out.node` takes `**attrs`; test pins no signature clash with `Sink`. |
| S3-N5 | rejected (done) | — | Both duplications were absorbed by earlier parts: S1-N2 `3782129` (`_common.line_index`, no module cache) and S2-N5 `333a33d`/`b12630a`/`76cbe8f` (one `tomllib` shim in `manifest.py`, re-exported as `tomllib`). |
| S3-E1 | actioned | `80f5d33` | `test_s3_e1_pick_by_prefix`, `test_s3_e1_sink_ref_unique_and_add_salting`, and the stale-cache regression `test_s3_m1_stale_cache_ref_degrades`. |
| S3-E2 | actioned | `32c510f` | `tools/compare_corpus.py --before <ref> [--after <ref>] PLUGIN=REPO ...`; exits 1 on any difference. |
| (S002 warning) | actioned | `80f5d33` test, `880c72c` fix | `queries.py` wraps an int grammar pointer (`tree_sitter_commonlisp` 0.4.1) in a `tree_sitter.Language` capsule. |
