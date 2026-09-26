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

**CI:** push run 36229683521 on `d9910c1` green (3.10 6270/19, 3.12 and 3.13
6269/20, security-scan success; 12 more passed than S002's run).

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

## S004

**Tests:** `.venv/bin/python -m pytest tests/ -q`: before 6275 passed, 14 skipped;
after 6288 passed, 14 skipped, 4 xfailed (13 new passing: E5 parity now 15
cases over two paths (+7), `test_s4_m1_*` 2, `test_s4_l1_*`, `test_s4_l3_*`,
`test_s4_l4_*`, `test_s3_x1_*`; the 4 xfails are the strict S4-E1 add-file
pin). Red-first as in S001; S4-L2 / S4-N2 are green guards (the stronger
assertions hold today, as the review measured). `git diff upstream/v8...HEAD --
graphify/extractors/` empty; `tests/lang_baseline.txt`,
`tests/upstream_tables.json` and `tests/test_watch.py` unchanged.

**Import time (S4-M1):** `python -X importtime -c "import graphify.detect"`,
cumulative, 5 runs: 173-185 ms before, 42-48 ms after (`GRAPHIFY_LANG_DISABLE=1`:
23-24 ms). Fresh interpreter (`timeit`, 10 runs, median): 193 ms -> 59 ms. The
namespace computation itself: 1.3 ms.

**Corpus (S3-X1):** `tools/compare_corpus.py --before 151ae36 --after 9541fcb
autolisp=~/repos/autolithp vba=~/repos/bim-chk` (autolithp `d5a2074`, bim-chk
`d7ba56f`): autolithp 254 files, nodes 10691 = 10691, edges 25584 -> 25621
(+37, none removed; all 37 are `calls` self-loops, counted on the after
graph); bim-chk 33 files, 416 nodes / 1114 edges, no difference.

| Id | Status | Commit(s) | Note |
|:--|:--|:--|:--|
| S4-M1 | actioned | `0975dff` test, `1990154` fix | Distributions from `ep.dist` (`registry.distributions()`), no `packages_distributions()`; a plugin package hashes its top-level package dir, a top-level module only its file; `lru_cache` kept. |
| S4-L1 | actioned | `0975dff` test, `1990154` fix | `_namespace_ast_cache` catches its own failure: `-langerr` namespace plus a warning. |
| S4-L2 | actioned | `0975dff` | Parametrized over `watch` and `cli` (`dispatch_command("extract")` in-process, `--code-only`; cc-kb watch only); a byte appended per file; whole node and edge dicts minus `_origin` / `community` / `weight` vs a clean build of the edited tree. |
| S4-L3 | actioned | `0975dff` test, `151ae36` fix | One `enrich_context(nodes, graph, identity)` call after each upstream loop (maps context nodes to persisted nodes by id); failure logged as a warning. Fork diff vs `upstream/v8`: `cli.py` 35 -> 26 lines, `watch.py` 26 -> 18. |
| S4-L4 | actioned | `bf76df9` test, `d21f7b2` fix, `f215fb0` docs | `graphify/lang_registry.py` hashed into the fingerprint; the other fork lines under `graphify/` still need a version change. Learning 1498 (global) supersedes 1490; spoke 05-S004 deviation added. `cc-LR000.002.md` (auto-exported) not hand-edited. |
| S4-L5 | actioned | `f215fb0` | `[resolve] context_fields` with the context-node contract in all three templates; README plugin contract extended (fields read on other files' nodes, edges, `enrich_context`). |
| S4-N1 | actioned | `f215fb0` | Spoke deviation and case 008 §3 say `cc_kb_links` is set in any repo, with the measured sizes. |
| S4-N2 | actioned | `0975dff` | `cargo_ws_deps` in the union test. |
| S4-N3 | actioned | `f215fb0` | Spoke deviation names the real test file. |
| S4-N4 | rejected | `0975dff` (red test), removed in `151ae36` | Every resolver filters by its own suffixes before reading a field, so the union is a read-only superset; scoping by claimed suffix drops fields for a plugin split across manifests (vba declares `visibility` / `accessor`, `vba-cls` owns `.cls`), and prefixing renames persisted fields. |
| S4-E1 | actioned | `0975dff`, `f215fb0` | Strict xfail `test_s4_e1_add_file_limit` over cargo `has_member`, cc-kb `cites`, AutoLISP `calls`, Python `calls` (each asserts that relation's edges only); the README known-limit line (from S6.2) now names the test. |
| Open q. (a) | accepted | — | Recorded as S4-E1; no cargo special case. |
| Open q. (b) | accepted | `f215fb0` | README line under `GRAPHIFY_LANG_DISABLE` (already there from S6.2) now lists the fingerprint inputs. |
| S3-X1 | actioned | `5eb3902` test, `9541fcb` fix | AutoLISP extractor and resolver, VBA extractor and resolver keep `calls` self-loops (other relations still drop them). VBA: a Sub has no result variable, so a bare `Walk` in `Sub Walk` is a call; in a Function / Property `Name(...)` is a call, `Name = x` the result. Learning 1499 (repo). |

## S005

**Tests:** `.venv/bin/python -m pytest tests/ -q`: before 6288 passed, 14
skipped, 4 xfailed; after 6302 passed, 14 skipped, 4 xfailed (+14 in
`tests/lang/test_s5_registry_robustness.py`: 12 red-first strict xfails,
`raises=` pinned, each removed by its fix commit, plus the green
`test_s5_m2_augment_watch_predicate` and the rewritten N2 test). `git diff
upstream/v8...HEAD -- graphify/extractors/` empty; `tests/lang_baseline.txt`,
`tests/upstream_tables.json` and `tests/test_watch.py` unchanged.

**Watch claim (S5-M2):** `graphify.lang_registry.watch_claims` over each set,
old rule ("the augment adds anything") -> new rule (`watch_cc_kb`): this repo's
tracked `.md` 349 -> 43 of 436; `~/.claude/docs/*.md` 648 -> 640 of 648;
`~/repos/claude-config` `**/*.md` (no `.git` / `graphify-out`) 861 -> 841 of
871. Claim check for 648 files: 3.1 s -> 0.6 s.

| Id | Status | Commit(s) | Note |
|:--|:--|:--|:--|
| S5-H1 | actioned | `04990d7` test, `7ab39e7` fix | Path runtimes import as `graphify_lang_path._<sha256[:16] of folder>.<runtime>` (synthetic package per folder); `sys.path` untouched; nothing shadowed. The review's fix (fail the second folder) was replaced by the owner's (namespace both): a shared top-level runtime name, or one an importable module has, loads and is a `--check` `warning:` row (exit status unchanged). |
| S5-M1 | actioned | `04990d7` test, `7ab39e7` fix | `expanduser`/`resolve` per entry and `entry_points()` inside a `try` (`load_errors` keys: the entry, `entry points`); `check_languages` calls `apply_registry()` and fails when `_REGISTRY_AVAILABLE` is False. `~nosuchuser_zz/plugins`: `.mki` stays in `CODE_EXTENSIONS`, `--check` exits 1. |
| S5-M2 | actioned | `04990d7` test, `29d91ea` engine, `63a8e2c` cc-kb | Narrowed, as the owner directed (the review proposed keeping the rule): `LanguageManifest.watch` predicate (path plugin: `WATCH`), `registry.augment_watch_claims` (no predicate: old rule; failing predicate: claims). cc-kb `watch_cc_kb`: a mention of another cc id, or a backticked path that is a file under the page's harness root. Spoke 05-S005 deviation and known limit corrected (a cc doc with no mention and a links-only page stay docs; removing the last mention/path leaves stale `cites` until the next rebuild). |
| S5-M3 | actioned | `04990d7` test, `7ab39e7` fix | A non-absolute entry after `~` expansion is a load error "must be an absolute path". |
| S5-L1 | actioned | `04990d7` test, `7ab39e7` fix | Relative imports (`from . import helper`) work at top level and lazily, via the H1 package; no global `sys.path` change. Absolute `import helper` stays unsupported by design (it would reopen H1); README says so. |
| S5-L2 | actioned | `04990d7` test, `7ab39e7` fix | Discovery registers through `_register_new`: first name wins, second (entry point or path) is a load error; a repeated folder loads once. `_register_manifest` itself still replaces (fork tests `test_lang_sniff.py` re-register on purpose). |
| S5-L3 | actioned | `04990d7` test, `7ab39e7` fix | A `*.toml` that parses without `[language]` is skipped (debug log); an unparsable one still reaches `from_toml` and is reported. |
| S5-N1 | actioned | `04990d7` test, `748befd` fix | `import logging as _lang_logging` at all seven L8 hook handlers (cli 1, detect 2, extract 4). |
| S5-N2 | actioned | `f4a4cc8` | `watch`'s `time` replaced by a clock whose loop sleep raises `KeyboardInterrupt` once the rebuild ran (10 s deadline), so `watch` stops its observer; the thread is joined and asserted dead. |
| S5-N3 | rejected (no change) | — | As the review advises: moving `_lang_claims` below the dotfile / `graphify-out` filters edits a second upstream line; no profile shows a cost. |
| S5-E1 | actioned | `61d8388` | `graphify_lang/templates/path-plugin/` (`example.toml`, `example_lang.py`), shipped as package data and loaded by `test_s5_e1_path_plugin_template_loads`; README rules for absolute entries, manifests only, private package, relative imports, first name wins, fingerprint `.py`/`.toml` only, watch predicate. |
