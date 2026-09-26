# Code review: graphify-lang fork layer

Open findings only. Fixed and closed findings move to `cc-CR000.002.md` (plan 05 stage 1 moved H4, E6, L1, L2, L4, N4, stage 2 moved M7, M8, M9, M10, N6, E9, stage 3 moved H2, M4, M6, L3, L5, L12, N3, E2, E7, E8, and stage 4 moved H1, H3, M2, L9, L11, E1, E5 on 2026-09-26).

| Severity | Count |
|:---------|------:|
| Critical | 0 |
| High | 0 |
| Medium | 5 |
| Low | 5 |
| Nit | 3 |
| **Defects total** | **13** |
| Enhancements | 2 |

- **Date**: 2026-09-26
- **Mode**: Diff (`git diff upstream/v8...autolisp`), branch `autolisp`, HEAD `013c902` (v0.9.67+lang.3)
- **Scope**: `graphify/lang_registry.py`; the registry-lookup blocks in `graphify/detect.py`, `extract.py`, `cli.py`; `graphify/resolver_registry.py`; `graphify_lang/**` (registry, manifest, rules engine, templates, plugins autolisp, vba, bmake, cargo, astgrep, ecschema, cc_kb); fork tests and fixtures; `pyproject.toml`; `.github/workflows/*`; fork docs. Upstream code only where the fork depends on it.
- **Focus**: Comprehensive
- **Verification**: `pytest tests/ -q` = 6141 passed, 14 skipped (86 s); fork tests alone 172 passed, 0 skipped on this host. Every High and most Medium findings were reproduced with a probe in the repo `.venv` (probe named in the finding). No source file was modified.
- **Repo rules respected in every fix**: no edit to existing extractors, `engine.py`, `resolution.py` or upstream tests; core tables change only through registry lookups. A fix that needs a core change is marked **upstream PR**.

## High

None open.

## Medium

### M1 One failing plugin disables every plugin

- **Where**: `graphify_lang/registry.py:112-118` (`result = result()` runs outside the `try` at `registry.py:71-75` and `89-93`); every shipped `_get_manifest` raises `ValueError` on a TOML error (for example `graphify_lang/bmake/__init__.py:19-21`).
- **Problem**: the exception propagates out of `_init_state`; `_apply_registry` (`graphify/lang_registry.py:47-49`) catches it and sets `_REGISTRY_AVAILABLE = False`, so all plugins vanish behind one warning. Manifests registered before the failure stay in `_STATE`, so later direct registry calls see a partial state.
- **Failure scenario (measured)**: an entry point whose manifest callable raises, loaded first: every `registered_names()` call raises `ValueError`; with the core wrapper, no plugin suffix is registered.
- **Fix**: move `result = result()` inside the per-entry-point `try` (log `failed to load entry point %s`), or wrap `_process_loader_result(ep.name, result)` in it. Add a test with one raising entry point next to a good one.

### M3 `graphify watch` ignores plugin-claimed data files

- **Where**: upstream `graphify/watch.py:282` (`_WATCHED_EXTENSIONS`), `watch.py:2306` (`_batch_triggers_rebuild` checks `_CODE_EXTENSIONS`); fork `graphify/lang_registry.py:41-43` adds `[match]` suffixes only to the hook list.
- **Problem**: `.xml` is in neither `CODE_EXTENSIONS` nor `DOC_EXTENSIONS`, so an ECSchema edit produces no watch event at all; `.yml` (ast-grep), `Cargo.toml` (cargo augment) and `.md` (cc-kb augment) edits are treated as doc changes and never trigger the AST rebuild. The git-hook path works (it uses `_HOOK_SOURCE_EXTS`), watch mode does not.
- **Fix**: **upstream PR** or a registry lookup in `_batch_triggers_rebuild` and the watch filter: treat a path as code when `lang_registry.claims_file(path)` or an augment claims it. Adding the suffixes to `CODE_EXTENSIONS` is not an option (it would classify every `.xml` as code).

### M5 `GRAPHIFY_LANG_PATH` is collected and never used; docs say tests rely on it

- **Where**: `graphify_lang/registry.py:96-108` (paths go into `search_paths`, which nothing reads; when any entry point registered a manifest first, `_STATE` already exists and the list is discarded); `docs/55-SETTLED.md:125` ("Development and tests discover the plugin through `GRAPHIFY_LANG_PATH`"); `docs/35-DONE.md:289`; module docstring `registry.py:1` ("or namespace", not implemented). `_RegistryState.enabled` (`registry.py:30`) is also never read.
- **Failure scenario**: a user or test sets `GRAPHIFY_LANG_PATH` to a directory with a manifest; nothing is loaded and nothing is logged.
- **Fix**: delete `_PATH_VAR`, `search_paths` and `enabled` (YAGNI; entry points cover packaging and tests), and correct the two docs and the docstring. Implement path discovery only when a real out-of-tree plugin needs it.

### M11 README is stale in several load-bearing places

- **Where**: `README.md:460-463` ("## Status: No code yet"); `README.md:417-437` (says the pipx venv is `graphifyy 0.9.55` and "left alone", plans `~/.venvs/graphify-lang`, "`uv` is not installed") versus `README.md:439-458` (pipx runs the fork; release uses `uv build`) and `.claude/CLAUDE.md` (develop in repo `.venv`); `README.md:342-363` roadmap without per-phase status and citing `cli.py:881`; `README.md:367` "Planned directories are marked" (none are).
- **Problem**: the entry document contradicts itself; a reader following 'Development setup' installs into the wrong venv.
- **Fix**: replace 'Status' with the current state (released `0.9.67+lang.3`, 7 plugins, `graphify lang list`); rewrite 'Development setup' to the repo `.venv` + `uv sync`; mark roadmap phases done/open (phase 6 = T10, open).

### M12 Test suite misses the failure classes above

- **Where**: `tests/lang/*`, `tests/test_lang_*.py`.
- **Problem**: no test covers incremental rebuild (H1), same-stem collisions for autolisp/vba (H2), augment cache coherence (H3, M2), hostile YAML (H4), or a failing plugin (M1). Four corpus tests (`test_vba.py:166-169`, `test_bmake.py:157-160`, `test_ecschema.py:31,184-185`, `test_astgrep.py:26,139`, `test_lang_sniff.py:165-168`) depend on private repos under `~/repos` and always skip in CI, so CI exercises only the small fixtures. `test_rules.py` (259 lines) tests the dead engine (M6).
- **Fix**: add one fixture-based test per class above (each a few lines); keep corpus tests but mark them `@pytest.mark.corpus` so skips are explicit.

## Low

### L6 Upper-case suffix variants are redundant

- **Where**: `graphify/lang_registry.py:36-42,94`.
- **Problem**: upstream already lower-cases (`classify_file`, `extract.py:6891-6892` fallback, `resolver_registry.py:80`), so `.LSP` entries only add noise to the core tables; `extract.py:6754-6757` then finds no manifest for them anyway. The comment at `:36` says "casefolded" but the code adds `upper()`.
- **Fix**: drop the `upper()` variants and fix the comment.

### L7 Two entry-point groups and a dead Python 3.9 path

- **Where**: `graphify_lang/registry.py:55-94` scans `graphify_lang.plugins` and `graphify_lang_plugins` with duplicated loops; the `entry_points().get(...)` fallback (`:63-64,81-82`) and `import importlib_metadata` (`:58-59`) cannot run under `requires-python >= 3.10`.
- **Fix**: one group (`graphify_lang_plugins`, as `pyproject.toml:122` ships), one loop.

### L8 Core hook sites swallow errors silently

- **Where**: `graphify/detect.py:49-50,535-536`, `graphify/extract.py:6719-6720,6758-6759,6883-6884,6920-6921`, `graphify/cli.py:82-83` (`except Exception: pass`).
- **Problem**: a bug in `claims_file` or `augment_extractor` silently reverts files to stock behaviour on every call, with no trace.
- **Fix**: `except Exception as exc: logging.getLogger("graphify.lang_registry").debug(...)` (keeps the one-line upstream diff).

### L10 Router suffixes widen `collect_files`

- **Where**: `graphify/lang_registry.py:92-94` puts `.yml`, `.yaml`, `.xml` routers in `_DISPATCH`; upstream `collect_files` (`graphify/extract.py:8698,8729`) collects every `_DISPATCH` suffix.
- **Problem**: every YAML/XML file under a `python -m graphify.extract <dir>` scan is dispatched to a router that returns empty results: wasted reads.
- **Fix**: accept, or omit `[match]`-only suffixes from `dispatch_table` (they only reach extraction through `claims_file`, which gives CODE).

### L13 Upstream-file edit in `resolver_registry.py`

- **Where**: `graphify/resolver_registry.py:78-80`.
- **Problem**: case-folding changes activation for every upstream resolver (a `.PY` file now activates the Python resolver) and is a direct edit outside the registry-lookup rule; each upstream rebase can conflict. Tracked as T10.4 but not proposed.
- **Fix**: send it upstream as its own small PR (T10.4) and drop it from the fork once merged.

## Nit

- **N1** `.claude/CLAUDE.md` cites `_DISPATCH` at `graphify/extract.py:5630`; it is at `:6601`. Cite the symbol, not the line.
- **N2** `docs/plans/00-INDEX.md` and plan headers mark plans 01 and 02 ACTIVE; plan 02 shipped in lang.1 (plan 01 is open only for T10).
- **N5** `[match] filenames` compare case-sensitively (`registry.py:240`): `cargo.toml` on a case-insensitive filesystem is not claimed.

## Architectural findings

- **Resolver id contract**: three of five resolvers learned to read ids back through the node index (bmake, ecschema, astgrep), two did not (H2). The contract belongs in one shared sink (E2), not in each plugin. — Impact: STRONG. Done in plan 05 S3 (`graphify_lang/_common.py`, cc-CR000.002 H2, E2).
- **Purity contract with the AST cache**: extractors and augments must be functions of the file bytes; everything that looks at other files belongs in the resolver (H3, M2). Write it into `README.md` 'Proposed architecture' as a plugin rule. — Impact: STRONG
- **Upstream seams the fork depends on**: `_disambiguate_colliding_node_ids` ordering, `watch.py` context-node fields (H1), `_reconcile_markdown_links` pruning only `references` (cc-kb relies on `cites` surviving, `cc_kb/resolve.py:30-33`), dict identity between `per_file` and `all_nodes` (bmake/astgrep/cc-kb index reads), `_get_extractor` suffix fallback. Each is untested from the fork side; an upstream refactor breaks them silently. A parity test (E5) covers most. — Impact: AVERAGE

## Enhancements

- **E3** Upstream PR: forward `node_kind` (or a registrable marker list) in `watch.py` context nodes (fixes H1 at the root). — Effort: LOW | Benefit: HIGH. Fork side done in `2adf7bc` (plan 05 S4.2); open until the upstream PR draft is written in S006.
- **E4** `graphify lang list --check`: load every manifest, report load errors per plugin (complements M1). — Effort: LOW | Benefit: NEUTRAL

## Suggestion plan

1. H4 + E6 (memoised `_matches`, per-document `try`): trivial, security.
2. H2 (index-based refs in autolisp and vba) with M4 (suffix-qualified file ids) and a same-stem fixture test.
3. H1: open the upstream PR (E3); meanwhile add the parity test (E5) marked `xfail` so the gap is visible.
4. H3: move cargo member/workspace and cc-kb code-path resolution into the resolvers.
5. M1, M2 (E1), M3 (upstream PR or registry lookup in watch).
6. M7, M8 (E9), M9, M10: repository and CI hygiene in one commit.
7. M5, M6 (E7), L6, L7, L12: deletions.
8. M11 README and plan index (N1, N2).
9. Remaining Low and Nit items as touched.

## Metrics

| Category | High | Medium | Low | Total |
|:---------|:----:|:------:|:---:|:-----:|
| Errors | 3 | 4 | 5 | 12 |
| Warnings | 0 | 3 | 4 | 7 |
| Security | 1 | 0 | 0 | 1 |
| Performance | 0 | 0 | 2 | 2 |
| Style / docs / CI | 0 | 4 | 2 | 6 |
| Test quality | 0 | 1 | 0 | 1 |
| Nit | - | - | - | 6 |
| Enhancements | - | - | - | 9 |

Errors = H1-H3, M1-M4, L1, L4, L9, L10, L11. Security = H4. Warnings = M5, M6, M10, L5-L8. Style/docs/CI = M7, M8, M9, M11, L12, L13. Test quality = M12. Performance = L2, L3.

- **Files reviewed**: 27 fork source files (`graphify/lang_registry.py`, 4 core hook blocks, 22 `graphify_lang` modules and manifests), 11 fork test modules, 3 workflows, `pyproject.toml`, 12 fork docs.
- **Files with issues**: 24.
- **Most affected**: `graphify_lang/registry.py`, `graphify_lang/autolisp/{extract,resolve}.py`, `graphify_lang/astgrep/extract.py`.
- **Skipped**: none.
