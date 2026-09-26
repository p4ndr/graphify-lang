# Code review: graphify-lang fork layer, resolved findings

Findings moved out of `cc-CR000.001.md` once fixed or closed. Each entry keeps the original text and adds the resolution. Hashes up to stage 5 are on the `rr-s1`..`rr-s5` refs; `rr-s6` was rebased onto `upstream/v8` `4000de1` (plan 05 S6.0), so the same commits have new hashes there.

| Finding | Severity | Status | Commit | Stage |
|:--|:--|:--|:--|:--|
| H4 | High | Fixed | `f3357fb` | plan 05 S1 (`rr-s1`) |
| E6 | Enhancement | Fixed (with H4) | `f3357fb` | plan 05 S1 |
| L1 | Low | Fixed | `10f235b` | plan 05 S1 |
| L2 | Low | Fixed | `10f235b` | plan 05 S1 |
| N4 | Nit | Fixed | `10f235b` | plan 05 S1 |
| L4 | Low | Fixed | `d498a6f` | plan 05 S1 (engine commit) |
| M7 | Medium | Fixed | `711dfc6` | plan 05 S2 (`rr-s2`) |
| M8 | Medium | Fixed | `23735ce`, `3d3b99f` | plan 05 S2 |
| E9 | Enhancement | Fixed (with M8) | `23735ce` | plan 05 S2 |
| M9 | Medium | Fixed | `1f8a2e4` | plan 05 S2 |
| M10 | Medium | Fixed | `1e2e430` | plan 05 S2 |
| N6 | Nit | Fixed | `1e2e430` | plan 05 S2 |
| H2 | High | Fixed | `bbf0a1f`, `67a582c` | plan 05 S3 (`rr-s3`) |
| M4 | Medium | Fixed | `2c3e6e9`..`67a582c` | plan 05 S3 |
| M6 | Medium | Closed per D1 (engine kept; hook fixed) | `3fa02c2` | plan 05 S3 |
| L3 | Low | Fixed | `a5a899c` | plan 05 S3 |
| L5 | Low | Fixed (by E2) | `2c3e6e9`..`b244901` | plan 05 S3 |
| L12 | Low | Fixed | `4618429`, `e837ed2` | plan 05 S3 |
| N3 | Nit | Fixed | `7711700`, `0db2814` | plan 05 S3 |
| E2 | Enhancement | Done | `2c3e6e9` | plan 05 S3 |
| E7 | Enhancement | Closed: rejected per D-008 | - | plan 05 S3 |
| E8 | Enhancement | Done (with L3) | `a5a899c` | plan 05 S3 |
| H1 | High | Fixed | `2adf7bc`, `cd55efb` | plan 05 S4 (`rr-s4`) |
| H3 | High | Fixed | `22855e9` | plan 05 S4 |
| M2 | Medium | Fixed | `2e2cba1` | plan 05 S4 (engine commit) |
| L9 | Low | Fixed (with H3) | `22855e9` | plan 05 S4 |
| L11 | Low | Fixed | `dc8a8ec` | plan 05 S4 |
| E1 | Enhancement | Done (with M2) | `2e2cba1` | plan 05 S4 |
| E5 | Enhancement | Done | `a5961fe`, `cd55efb` | plan 05 S4 |
| M1 | Medium | Fixed | `4071b40` | plan 05 S5 (`rr-s5`, engine commit) |
| L7 | Low | Fixed (with M1) | `4071b40` | plan 05 S5 |
| M5 | Medium | Fixed (implemented, D4) | `4071b40` | plan 05 S5 |
| E4 | Enhancement | Done | `a05bc8b`, `cb21e7e` | plan 05 S5 |
| M3 | Medium | Fixed in fork (D2) | `32d4618`, `227c194` | plan 05 S5 |
| L6 | Low | Fixed | `7d9fbf8` | plan 05 S5 |
| L8 | Low | Fixed | `34510f8` | plan 05 S5 |
| N5 | Nit | Fixed | `b80a115` | plan 05 S5 |
| L10 | Low | Closed: accepted (measured) | - | plan 05 S5 |
| L13 | Low | Closed: kept per D2, pinned | `ef2012a` (test) | plan 05 S5 |
| M12 | Medium | Fixed | `842a67d` (and the per-stage tests) | plan 05 S6 (`rr-s6`) |
| M11 | Medium | Fixed | `acdac5f` | plan 05 S6 |
| N1 | Nit | Fixed | `acdac5f` | plan 05 S6 |
| N2 | Nit | Fixed | `acdac5f` | plan 05 S6 |
| E3 | Enhancement | Done (PR draft, not opened) | `31db078` | plan 05 S6 |

## High

### H4 ast-grep YAML alias expansion: unbounded time and recursion on crafted input (security, DoS)

- **Where**: `graphify_lang/astgrep/extract.py:106-116` (`_matches` walks the `yaml.safe_load` tree), called outside the per-document `try` at `extract.py:205,251`.
- **Problem**: `safe_load` shares aliased subtrees, but `_matches` traverses every reference, so N levels of 10 aliases cost 10^N visits; a self-referencing alias (`rule: &a {any: [*a]}`) recurses until `RecursionError`. graphify is run on arbitrary third-party repos, and the file only needs to sit under `rules/`, `utils/` or `rule-tests/` with `id:` plus one body key to be claimed.
- **Failure scenario (measured)**: a 377-byte `rules/bomb.yml` with 6 alias levels takes 0.59 s; each extra level multiplies by 10 (9 levels, under 500 bytes, is about 10 minutes; 10 levels about 100 minutes), hanging `graphify update`. The recursive alias raises `RecursionError`; upstream then skips the whole file ("recursion limit exceeded"), losing even its file node.
- **Fix**: memoise by object identity in `_matches` (a `seen: set[int]` of `id(obj)` for dicts/lists; return on revisit). That bounds work to the number of distinct YAML nodes and ends the recursion. Also wrap `_rule_doc` in the per-document `try` so a malformed document keeps the file node, as the module docstring promises.
- **Resolution (2026-09-26, plan 05 S1.2)**: fixed in `f3357fb` (fix), tests `029c35e` + `f3357fb`. `_matches` keeps a `seen` set of `id()` for dicts and lists; the whole per-document body (new `_document`, `_rule_doc` included) runs inside the per-document `try`. Tests `tests/lang/test_s1_safety.py::test_h4_alias_bomb_bounded[6|9]`, `test_h4_self_alias_keeps_file_node`. Measured in a child process: 9 alias levels (406 bytes) > 30 s timeout before, 0.04 s after; 6 levels 0.32 s before, 0.04 s after (incl. lazy import). llm-linter-tool graph byte-identical.

### H2 AutoLISP and VBA resolver refs carry extraction-time ids; same-stem files lose edges

- **Where**: `graphify_lang/autolisp/extract.py:104-106` (`ref` stores `source` id), consumed at `graphify_lang/autolisp/resolve.py:54-60,74-89`; `graphify_lang/vba/extract.py:156-159`, `graphify_lang/vba/resolve.py:89-94`. Upstream dependency: `_disambiguate_colliding_node_ids` (`graphify/extractors/resolution.py:929`) renames colliding node dicts in place at `graphify/extract.py:7944`, before `run_language_resolvers` (`extract.py:8480-8484`).
- **Problem**: when two files share a stem (the normal AutoCAD layout `foo.lsp` + `foo.mnl` + `foo.dcl`, or a same-named defun in `foo.lsp` and `foo.mnl`), their ids are salted apart before the resolver runs, but the ref still names the old id. The edge is emitted with a dangling source and later pruned, silently. bmake, ecschema and astgrep already avoid this by storing the node index (`bmake/extract.py:132-135`, ltm learning 1477); autolisp and vba do not. The comment at `autolisp/resolve.py:79-80` ("graphify already gives both files one node id") is wrong for the same reason.
- **Failure scenario (measured)**: `app.lsp` with `(defun helper () (libfn))`, `app.mnl` with its own `helper`, `sub/lib.lsp` with `libfn`: `extract()` emits `app_helper calls sub_lib_libfn` where `app_helper` no longer exists (nodes are `app_lsp_app_helper`, `app_mnl_app_helper`). Sidecar refs from a colliding file node dangle the same way.
- **Fix**: adopt the bmake pattern in both plugins: store `node` (index into the result's `nodes`) in each ref and read `res["nodes"][ref["node"]]["id"]` in the resolver; keep `dialogs_of` keyed by the current id. Add a same-stem fixture test (`x.lsp` + `x.mnl` + `x.dcl` with cross-file calls and a sidecar).
- **Resolution (2026-09-26, plan 05 S3)**: fixed in `bbf0a1f` (vba) and `67a582c` (autolisp) on the shared core of `2c3e6e9`; tests `542f417`. Every plugin ref stores `node`, the index of its source node in the result, and the resolver reads the current (salted) id back through `graphify_lang._common.refs_of` / `resolve_ref_id`; `dialogs_of` is keyed by that id. The wrong comment at `autolisp/resolve.py:79-80` is deleted with its `continue`, so a `.lsp` and its same-stem `.md` sidecar get their `sidecar_doc` edge. Tests `tests/lang/test_s3_shared_core.py::test_h2_same_stem_lsp_mnl_dcl` (x.lsp + x.mnl + x.dcl + x.md, cross-file calls, dialog, action, sidecar) and `test_h2_vba_same_stem`: dangling `calls` edges before, none after. Corpus: `docs/testing/case_008_plan05-remediation.md`.

### H1 Incremental rebuild drops every cross-file plugin edge into unchanged files

- **Where**: all plugin resolvers index targets by `node_kind`: `graphify_lang/autolisp/resolve.py:26`, `graphify_lang/vba/resolve.py:59`, `graphify_lang/bmake/resolve.py:68`, `graphify_lang/astgrep/resolve.py:51-55`, `graphify_lang/cc_kb/resolve.py:60`. Upstream dependency: `graphify/watch.py:1723-1729` builds the resolution-context node for unchanged files from `id`, `label`, `source_file`, `file_type`, `type` plus a fixed marker list; `node_kind` (and `astgrep_scope`, `visibility`, `accessor`) is not forwarded.
- **Problem**: on an incremental rebuild (`_rebuild_code(changed_paths=...)`, used by the git post-commit hook, the Claude hook flow and `graphify watch`), the resolvers see unchanged files' nodes without `node_kind`, so no target in an unchanged file is found. The changed file's old edges were removed with its re-extraction, so the edges disappear.
- **Failure scenario (measured)**: corpus `src/app.lsp` `(defun c:go () (libfn))` + `src/lib.lsp` `(defun libfn ...)`. Full build: `src_app_c_go calls src_lib_libfn`. Edit `app.lsp` only, run `graphify.watch._rebuild_code(root, changed_paths=[app.lsp])`: the `calls` edge is gone. Same mechanism for VBA calls, bmake includes/macros, ast-grep util/test links, cc-kb `cites`, ECSchema cross-schema refs.
- **Fix**: **upstream PR** (generic, small): forward `node_kind` (or a plugin-declared marker list) in the `ctx_node` at `watch.py:1723`. Until then, a plugin-side mitigation: resolvers fall back to classifying context nodes without `node_kind` by id shape or by a marker upstream already forwards (for example the node `type` field, but check `_disambiguate_colliding_node_ids` exempts `type in ("module","namespace")`). Add a test that compares a full build with full-then-incremental for every plugin fixture (E5).
- **Resolution (2026-09-26, plan 05 S4.2)**: fixed in `2adf7bc` (engine: `watch._rebuild_code` and the `graphify extract` incremental path copy each manifest's new `[resolve] context_fields` (default `["node_kind"]`) and `_lang_source_file`, the absolute source path, onto the context nodes through a try-wrapped `graphify.lang_registry.context_fields()` lookup) and `cd55efb` (plugins: astgrep, vba, ecschema, bmake (`bmake_includes`), cc-kb (`cc_kb_links`) declare their fields; resolvers compare paths through `_common.source_of`). Red test `a5961fe`. `tests/lang/test_s4_build_coherence.py::test_e5_incremental_parity` passes on all 8 fixture trees (7 of 8 failed before). The upstream PR draft is E3 (S006).

### H3 Augment output depends on other files but is cached by this file's content hash

- **Where**: `graphify_lang/cargo/augment.py:46-68` (`_members` globs member dirs and reads their `Cargo.toml`; `_workspace_deps` reads parent manifests); `graphify_lang/cc_kb/augment.py:64-82,85-102` (`_is_root` scans `docs/`, `_code_ref` calls `is_file()` on the referenced path). Upstream dependency: `graphify/cache.py:965` keys AST entries by file content + package version only.
- **Problem**: the extractor contract behind the AST cache is "output is a function of the file's bytes". These augments break it, so a cached result survives changes elsewhere.
- **Failure scenario (measured)**: workspace `members = ["crates/*"]` with crate `a`: `has_member -> pkg_a`. Add `crates/b/Cargo.toml` (root manifest unchanged) and rebuild with the same cache: still only `pkg_a`; a fresh cache gives `pkg_a, pkg_b`. For cc-kb: a doc that mentions `` `scripts/new.ps1` `` before the script exists never gains its `cites` edge until the cache is cleared.
- **Fix**: keep augments pure. Emit the raw payload (member globs and `exclude` relative to the manifest dir; renamed/workspace deps by key; every path-like code span) and let the resolver, which runs every build over the whole corpus, match against graphed nodes (`pkg_*` nodes by their `source_file` dir; file nodes by normalised path). This also removes the filesystem reads from extraction.
- **Resolution (2026-09-26, plan 05 S4.3)**: fixed in `22855e9`. The cargo augment emits the workspace node (with `cargo_ws_deps`) and a `cargo_refs` payload; a new cargo resolver matches member globs, `exclude` and workspace deps against graphed `pkg_*` nodes. The cc-kb augment emits every path-like span and the candidate roots; the resolver takes the first root whose `docs/` holds a graphed `cc-*.md` and drops ungraphed paths (`_is_root` deleted). Tests `test_h3_new_member_crate_appears`, `test_h3_new_code_ref_target_appears`. Clean-build counts unchanged (case 008 §3): has_member moxide 16, oa-graph 5, oag-dev 5; claude-config hub_spoke 235, cc_ref 8995, code_ref 3182, cc_id 632.

## Medium

### M7 `publish.yml` and `release-graph.yml` are corrupted YAML

- **Where**: `.github/workflows/publish.yml:20,33,36,39,50,53` and `release-graph.yml:17,25,34,39,42,52,58` (a trailing `:` was appended to lines, for example `contents: read:`, `uses: actions/checkout@v4:`).
- **Problem (measured)**: `yaml.safe_load` fails on both files ("mapping values are not allowed here"). The `if: github.repository == 'Graphify-Labs/graphify'` guard never gets evaluated because the file does not parse; a release event on the fork shows an invalid-workflow failure, and the corruption would break publishing if the diff ever went upstream. It also adds rebase conflicts in upstream-owned files.
- **Fix**: `git checkout upstream/v8 -- .github/workflows/publish.yml .github/workflows/release-graph.yml`, then re-add only the one-line `if:` guards (or disable the workflows in the fork's repo settings instead of editing them).
- **Resolution (2026-09-26, plan 05 S2.1)**: fixed in `711dfc6`. Both files restored from `upstream/v8`; the only fork delta is the one-line `if: github.repository == 'Graphify-Labs/graphify'` job guard. All four workflows pass `yaml.safe_load` (two failed before). `actionlint` is not installed on this host.

### M8 Fork CI does not run on the release branch

- **Where**: `.github/workflows/graphify-lang-ci.yml:4-7` (branches `lang-registry`, `v8`); upstream `ci.yml:5-7` (v1-v8, main). Releases are cut from `autolisp` (README 'Installing the fork').
- **Problem**: no workflow runs on a push to `autolisp` or on the `v*+lang.*` tags, so a released wheel is never CI-tested. The security job's `bandit -r graphify` (`:56`) skips `graphify_lang`.
- **Fix**: trigger on `autolisp` and `lang-*` branches and on `v*` tags; run `bandit -r graphify graphify_lang`.
- **Resolution (2026-09-26, plan 05 S2.2)**: fixed in `23735ce`, CI 3.10 fix `3d3b99f`. `graphify-lang-ci.yml` triggers on push/PR to `autolisp`, `lang-*`, `rr-*`, `v8` and on `v*` tags; the security job runs `bandit -r graphify graphify_lang -ll`. Local bandit over `graphify_lang`: 0 issues at any severity. First fork CI run on `rr-s2` (36219014956) failed on 3.10: `tests/lang/test_rules.py` imported `tomllib` bare; fixed with the tomli fallback. Run 36219115105 green: 3.10 6149 passed/19 skipped, 3.12 and 3.13 6148/20. Correction (plan 05 review-fix S2-M1/S2-M2): the security-scan job was green only through `continue-on-error`; in that run both steps exited 1. bandit exited 1 on the 4 upstream High B324 (`graphify/_minhash.py`, `extract.py:391`, `extractors/engine.py`, `extractors/resolution.py`), and `pip-audit --strict` exited 1 on the editable project before auditing anything. Both are now gating (`pip-audit --skip-editable`; `bandit -r graphify_lang -ll`), and the lock bump cleared the 14 advisories the audit then reported.

### M9 Committed junk and scratch files

- **Where**: `git-sp.ps1` (765 lines, an unrelated sparse-checkout TUI); `.sidecar-cache/restore-8135b1ee46771d6c.json` (362 KB copy of `extract.py`) and `.sidecar-cache/T6-Resume-20260923.md`; repo-root `src_core_test.lsp`, `test_dcl.toml`, `test_pattern.toml` (unused: `tests/lang/test_autolisp_nodes.py:314` writes its own copy to `tmp_path`); `docs/testing/archive/` (32 near-duplicate `T14-*` reports); `.claude/docs/cc-T10-COMPLETE.md` (off-schema name).
- **Problem**: noise in every diff against upstream, in the repo's own graph (the root `.lsp` becomes a graph node), and in reviews; the JSON bloats clones.
- **Fix**: `git rm` them; add `.sidecar-cache/` to `.gitignore`; keep one summary of T14 if any of it is still referenced.
- **Resolution (2026-09-26, plan 05 S2.3)**: fixed in `1f8a2e4`. Removed `.sidecar-cache/`, root `src_core_test.lsp`, `test_dcl.toml`, `test_pattern.toml`, `docs/testing/archive/` (the `docs/testing/case_*` summaries stay) and `.claude/docs/cc-T10-COMPLETE.md`; `.sidecar-cache/` added to `.gitignore`. `git-sp.ps1` stays (hub D3). Remaining mentions are history notes in `docs/25-HISTORY.md`.

### M10 `scripts/install-mcp.sh` writes a config key nothing reads

- **Where**: `scripts/install-mcp.sh:1-10,64+` writes `.watch._HOOK_SOURCE_EXTS` into `~/.claude/mcp.json`.
- **Problem**: no component reads that key; hook suffixes come from the registry (`graphify/cli.py:76-83`). The script mutates a shared user config file for no effect, and `docs/30-TODO.md:46` still lists a manual run as pending.
- **Fix**: delete the script and the TODO line.
- **Resolution (2026-09-26, plan 05 S2.4)**: fixed in `1e2e430`. `scripts/install-mcp.sh` deleted, and `docs/16-MCP-SETUP.md`, which only documented it; `docs/55-SETTLED.md` P1 gains a note. The T9.5 text is N6.

### M4 Plugin file-node ids diverge from upstream and become non-portable on collision

- **Where**: every plugin sink uses `self.stem = _make_id(_file_stem(path))` as the file-node id: `autolisp/extract.py:72,78`, `vba/extract.py:132,138`, `bmake/extract.py:97,108`, `ecschema/extract.py:110,116`, `astgrep/extract.py:157,163`, `rules.py:40,48`.
- **Problem**: upstream file nodes use the full path including the suffix (`extract_python` gives `..._app_py`), so `app.py` and `app.js` never collide. The plugin ids drop the suffix, so `app.lsp`/`app.mnl`/`app.dcl` collide; the salted replacement is built from the old id, which already contains the absolute scan-root path, and the later portable-id remap does not undo it.
- **Failure scenario (measured)**: file nodes come out as `app_lsp_tmp_claude_1000_home_p4ndr_..._c1_app`: the absolute checkout path is baked into graph ids, so the same repo graphs differently on another machine or path (breaks graph diffs and `graphify global` merges).
- **Fix**: mint the file-node id the way the built-ins do (`_make_id(str(path))`, suffix included, so upstream's portable remap applies) and keep symbol ids stem-based; re-run the case 004/007 corpus counts. This also removes most of the collisions behind H2.
- **Resolution (2026-09-26, plan 05 S3)**: fixed in `2c3e6e9` (`Sink`, bmake), `05ddbef` (ecschema), `569ef3e` (astgrep), `bbf0a1f` (vba), `67a582c` (autolisp, and `rules.Out` on the same `Sink`); tests `542f417`. The file-node id is `_make_id(str(path))`, suffix included, so upstream's remap makes it root-relative before disambiguation; symbol ids are unchanged. Test `test_m4_file_ids_portable[autolisp|vba|bmake|ecschema|astgrep]` (two scan roots, same-stem plugin files beside a same-stem `.py`: identical, unique, root-free ids). Old-to-new id form and corpus counts in `docs/testing/case_008_plan05-remediation.md`: counts unchanged except autolithp / autolithp02 / snap-rework, where 61 / 60 / 61 `.lsp` file nodes no longer merge with their same-stem `.md` page and `sidecar_doc` goes 1 -> 63 / 62 / 63; 2 bmake and 2 autolisp ids lose the scan root.

### M6 Declarative rules engine is dead weight (ponytail)

- **Where**: `graphify_lang/rules.py` (132 lines), `queries.py` (133), `regex_rules.py` (101), `builtins.py` (45), `templates/*.toml` (179), `tests/lang/test_rules.py` (259), fixtures `tests/lang/rules_dcl.toml`, plus shipped package data.
- **Problem**: no plugin calls `rules.build()`; its own docstring says "none depends on it". It also carries an import-by-string hook (`rules.py:86-95`, `post_file = "module:fn"` from TOML). Every shipped plugin duplicates what it would provide (builtins lists, sinks).
- **Fix**: delete the engine, its tests and the templates (git keeps them), or move them to the `lang-rules` branch until a plugin needs them.
- **Resolution (2026-09-26, plan 05 S3)**: closed per hub D1 (D-008 wins): the engine stays and has users. The plugins use its builtins filter (`builtins.py`, `;` comments `1d2eb29`; autolisp and vba read `builtins_file` / `builtins_prefixes` / `case_insensitive` through `load_builtins`, `bbf0a1f`, `67a582c`) and `rules.Out` is built on the shared `Sink` (`67a582c`). The import-by-string hook is fixed in `3fa02c2`: `post_file` accepts only `graphify_lang.*` modules; any other string is a manifest error (`failed to load`) and is never imported. Test `tests/lang/test_rules.py::test_m6_post_file_prefix_only` (red in `542f417`).

### M2 AST cache is shared across different plugin sets

- **Where**: `graphify/cache.py:957` (`v{_EXTRACTOR_VERSION}-s{schema}` namespace); registry state in `graphify_lang/registry.py:49-50`.
- **Problem**: the extractor chosen for a file depends on the active plugin set (`GRAPHIFY_LANG_DISABLE`, a third-party plugin installed or removed), but the cache key does not. Known (ltm learning 1480) but unmitigated.
- **Failure scenario (measured)**: run `extract()` on `app.lsp` with `GRAPHIFY_LANG_DISABLE=1`, then without it, same cache dir: the second run returns the stock Common Lisp result (2 nodes, no `node_kind`); a fresh cache gives the AutoLISP result (file, command, function, module). Same for `.cls` (Apex vs VBA) and `.md` (cc-kb augment).
- **Fix**: E1: in `_apply_registry`, append a fingerprint of the registered manifests (names, plugin distribution versions, maybe a hash of plugin module files) to `graphify.cache._EXTRACTOR_VERSION` (a runtime attribute set, no source edit), so each plugin set gets its own namespace.
- **Resolution (2026-09-26, plan 05 S4.5)**: fixed in `2e2cba1` with E1. Test `test_m2_disable_toggle_uses_own_cache` (the disabled run no longer poisons the enabled one) and `test_m2_same_plugin_set_shares_cache`. ltm learnings 1480 / 1484 superseded by 1490.

### M1 One failing plugin disables every plugin

- **Where**: `graphify_lang/registry.py:112-118` (`result = result()` runs outside the `try` at `registry.py:71-75` and `89-93`); every shipped `_get_manifest` raises `ValueError` on a TOML error (for example `graphify_lang/bmake/__init__.py:19-21`).
- **Problem**: the exception propagates out of `_init_state`; `_apply_registry` (`graphify/lang_registry.py:47-49`) catches it and sets `_REGISTRY_AVAILABLE = False`, so all plugins vanish behind one warning. Manifests registered before the failure stay in `_STATE`, so later direct registry calls see a partial state.
- **Failure scenario (measured)**: an entry point whose manifest callable raises, loaded first: every `registered_names()` call raises `ValueError`; with the core wrapper, no plugin suffix is registered.
- **Fix**: move `result = result()` inside the per-entry-point `try` (log `failed to load entry point %s`), or wrap `_process_loader_result(ep.name, result)` in it. Add a test with one raising entry point next to a good one.
- **Resolution (2026-09-26, plan 05 S5.2)**: fixed in `4071b40`. Each entry point loads inside its own `try` (the manifest callable included); a failure logs `failed to load entry point <name>: <error>`, is recorded in `load_errors()`, and the other plugins register. Test `test_m1_bad_entry_point_isolated`.

### M3 `graphify watch` ignores plugin-claimed data files

- **Where**: upstream `graphify/watch.py:282` (`_WATCHED_EXTENSIONS`), `watch.py:2306` (`_batch_triggers_rebuild` checks `_CODE_EXTENSIONS`); fork `graphify/lang_registry.py:41-43` adds `[match]` suffixes only to the hook list.
- **Problem**: `.xml` is in neither `CODE_EXTENSIONS` nor `DOC_EXTENSIONS`, so an ECSchema edit produces no watch event at all; `.yml` (ast-grep), `Cargo.toml` (cargo augment) and `.md` (cc-kb augment) edits are treated as doc changes and never trigger the AST rebuild. The git-hook path works (it uses `_HOOK_SOURCE_EXTS`), watch mode does not.
- **Fix**: **upstream PR** or a registry lookup in `_batch_triggers_rebuild` and the watch filter: treat a path as code when `lang_registry.claims_file(path)` or an augment claims it. Adding the suffixes to `CODE_EXTENSIONS` is not an option (it would classify every `.xml` as code).
- **Resolution (2026-09-26, plan 05 S5.3)**: fixed in the fork per hub D2: `32d4618` (engine: `lang_registry.watch_claims`, a `[match]` claim, or an augment that adds to the built-in's result; a deleted path counts by suffix) and `227c194` (one try-wrapped lookup, `_lang_claims`, at the watch filter, `_batch_triggers_rebuild` and `_has_non_code`). Tests `test_m3_watch_triggers_on_claimed_xml_yml_toml_md`, `test_m3_watch_handler_sees_claimed_xml`; upstream `tests/test_watch.py` unchanged and passing. Upstream PR draft in S006.

### M5 `GRAPHIFY_LANG_PATH` is collected and never used; docs say tests rely on it

- **Where**: `graphify_lang/registry.py:96-108` (paths go into `search_paths`, which nothing reads; when any entry point registered a manifest first, `_STATE` already exists and the list is discarded); `docs/55-SETTLED.md:125` ("Development and tests discover the plugin through `GRAPHIFY_LANG_PATH`"); `docs/35-DONE.md:289`; module docstring `registry.py:1` ("or namespace", not implemented). `_RegistryState.enabled` (`registry.py:30`) is also never read.
- **Failure scenario**: a user or test sets `GRAPHIFY_LANG_PATH` to a directory with a manifest; nothing is loaded and nothing is logged.
- **Fix**: delete `_PATH_VAR`, `search_paths` and `enabled` (YAGNI; entry points cover packaging and tests), and correct the two docs and the docstring. Implement path discovery only when a real out-of-tree plugin needs it.
- **Resolution (2026-09-26, plan 05 S5.2)**: implemented per hub D4 (not deleted) in `4071b40`: each `GRAPHIFY_LANG_PATH` folder's `*.toml` manifests load after the entry points; `[extract] runtime` is imported with the folder first on `sys.path` for that import only and must expose `extract` (or `augment`) and may expose `RESOLVER`; a missing folder, a bad manifest or a taken name logs one warning and is skipped. Loaded folders join the E1 fingerprint. `_RegistryState.enabled` (and the unread `warned_builtins`) deleted; module docstring fixed. Tests `test_m5_lang_path_loads_plugin`, `test_m5_missing_dir_warns`, `test_m5_bad_path_manifest_isolated`, `test_m5_path_plugin_in_cache_fingerprint`.

### M11 README is stale in several load-bearing places

- **Where**: `README.md:460-463` ("## Status: No code yet"); `README.md:417-437` (says the pipx venv is `graphifyy 0.9.55` and "left alone", plans `~/.venvs/graphify-lang`, "`uv` is not installed") versus `README.md:439-458` (pipx runs the fork; release uses `uv build`) and `.claude/CLAUDE.md` (develop in repo `.venv`); `README.md:342-363` roadmap without per-phase status and citing `cli.py:881`; `README.md:367` "Planned directories are marked" (none are).
- **Problem**: the entry document contradicts itself; a reader following 'Development setup' installs into the wrong venv.
- **Fix**: replace 'Status' with the current state (released `0.9.67+lang.3`, 7 plugins, `graphify lang list`); rewrite 'Development setup' to the repo `.venv` + `uv sync`; mark roadmap phases done/open (phase 6 = T10, open).
- **Resolution (2026-09-26, plan 05 S6.2)**: fixed in `acdac5f`. 'Status' gives the released `v0.9.67+lang.3`, the 9 plugins and `graphify lang list`; 'Development setup' is the repo `.venv` + `uv sync` (the pipx `0.9.55` / `~/.venvs/graphify-lang` / "uv is not installed" text is gone); roadmap phases 1-5 marked done, phase 6 open (T10); core-table line citations replaced by symbol names (the dated 'The problem' section keeps its `c9f9901` line numbers, labelled as such); "Planned directories are marked" deleted; new 'Plugin contract' (pure extractors and augments, index refs, `[resolve] context_fields`, `source_of`, `GRAPHIFY_LANG_PATH`, `lang list --check`), known limits (incremental builds miss edges into newly added files; toggling `GRAPHIFY_LANG_DISABLE` re-extracts once) and 'Upstream seams the fork depends on'. Check: `git grep -n "No code yet\|0.9.55\|~/.venvs/graphify-lang\|extract.py:5630" -- README.md .claude/CLAUDE.md` finds nothing.

### M12 Test suite misses the failure classes above

- **Where**: `tests/lang/*`, `tests/test_lang_*.py`.
- **Problem**: no test covers incremental rebuild (H1), same-stem collisions for autolisp/vba (H2), augment cache coherence (H3, M2), hostile YAML (H4), or a failing plugin (M1). Four corpus tests (`test_vba.py:166-169`, `test_bmake.py:157-160`, `test_ecschema.py:31,184-185`, `test_astgrep.py:26,139`, `test_lang_sniff.py:165-168`) depend on private repos under `~/repos` and always skip in CI, so CI exercises only the small fixtures. `test_rules.py` (259 lines) tests the dead engine (M6).
- **Fix**: add one fixture-based test per class above (each a few lines); keep corpus tests but mark them `@pytest.mark.corpus` so skips are explicit.
- **Resolution (2026-09-26, plan 05 S6.1)**: fixed. The per-class tests landed in stages 1-5 (H1/E5 `test_s4_build_coherence.py`, H2 `test_s3_shared_core.py`, H3/M2 `test_s4_build_coherence.py`, H4 `test_s1_safety.py`, M1 `test_s5_registry_robustness.py`); `test_rules.py` tests an engine with users (M6 closed per D1). `842a67d`: a `corpus` marker in `pyproject.toml`; the five corpus tests are parametrized, the private-repo cases marked `corpus` and skipping with a `corpus:` reason, and each has a checked-in sample case that always runs (bmake and ecschema reuse their fixture trees; a synthetic CRLF `ThisWorkbook.cls` and a synthetic ast-grep project under `tests/lang/fixtures/corpus/`). `pytest -m "not corpus and not perf" tests/ -q`: 6232 passed, 14 skipped, 6 deselected.

## Low

### L1 AutoLISP walker recursion overflows on deep nesting

- **Where**: `graphify_lang/autolisp/extract.py:150-234` (`_Walker.walk` / `walk_list` recurse per list level), called outside the `try` at `extract.py:275-277`.
- **Failure scenario (measured)**: a defun with 1200 nested `(list ...)` raises `RecursionError`; upstream skips the whole file. Rare in hand-written code, possible in generated LISP.
- **Fix**: an explicit stack, or catch `RecursionError` in `extract_autolisp` and fall back to the regex path already used for `root.has_error` (`extract.py:293-304`).
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b` (fix), test `029c35e`. `extract_autolisp` catches `RecursionError` from the walk and uses the regex fallback (`fallback = root.has_error` or the overflow). Test `test_l1_deep_nesting_falls_back` (1200 levels at recursion limit 1000; `_raise_recursion_limit()` in `graphify.extract` raises the limit to 10 000 when an extraction runs, not on import, so the pipeline overflows only near 5000 levels).

### L2 Quadratic edge de-duplication in two sinks

- **Where**: `graphify_lang/ecschema/extract.py:127-132` and `graphify_lang/astgrep/extract.py:174-179` scan `self.edges` linearly per edge.
- **Problem**: O(E²) per file; a large ECSchema (tens of thousands of properties) costs minutes. The other sinks use an `_edge_keys` set.
- **Fix**: use the `_edge_keys` set as `bmake/extract.py:119-125` does.
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b` (fix), test `029c35e`. Both sinks use an `_edge_keys` set. Test `test_l2_large_schema_linear`: 20 000 properties 25.1 s before, 0.18 s after. BentleyHelp graph byte-identical.

### L4 Manifest validation can still raise and does not normalise suffixes

- **Where**: `graphify_lang/manifest.py:131-133,135-206` (`data.get("language", {})` then `.get` on it: a TOML `language = "x"` raises `AttributeError`, contradicting "never an exception" at `:116`); `:164` accepts a non-string `name` (later `re.sub` in `registry.py:392` fails); `:245-247` checks the leading dot but not case, so `.LSP` in a manifest never matches (`registry.py:381,422` lower-case the path suffix).
- **Fix**: check each section `isinstance(..., dict)`; require `isinstance(name, str)`; lower-case `suffixes`, `augments`, `overrides`, `hook_suffixes`.
- **Resolution (2026-09-26, plan 05 S1.4)**: fixed in `d498a6f` (fix, engine), test `1e678c5`. A non-table `[language]`, `[grammar]`, `[extract]` or `[match]` and a non-string `name` are one-line errors; `suffixes`, `hook_suffixes`, `augments`, `overrides` are lower-cased (order kept, duplicates dropped). Tests `tests/test_lang_manifest_safety.py`. All 9 shipped languages load.

### L3 cc-kb resolver and augment do avoidable linear work

- **Where**: `graphify_lang/cc_kb/resolve.py:80` (`next(n for n in all_nodes if n["id"] == node["id"])` per payload: O(files x nodes); `node` is already the live dict); `graphify_lang/cc_kb/augment.py:64-69` (`_is_root` re-scans `docs/` for every `.md`).
- **Fix**: use `node` directly (or one `by_id` dict); `functools.lru_cache` on `_is_root`.
- **Resolution (2026-09-26, plan 05 S3)**: fixed in `a5a899c`, test `0dea8c6`. The resolver finds a payload's live page node through one `by_id` map built in its single `all_nodes` pass. Test `test_l3_cc_kb_resolver_scans_nodes_once`: 7 scans for 6 docs before, 1 after. `_is_root` is E8.

### L5 Copy-paste across plugins

- **Where**: `_pick` + `shared` in `autolisp/resolve.py:30-50`, `vba/resolve.py:29-44`, `bmake/resolve.py:32-47`, `astgrep/resolve.py:26-41`; lazy `_file_stem`/`_make_id` shims in 5 extractors; `_Out` sinks in 5 extractors; 7 near-identical `_get_manifest` loaders.
- **Fix**: E2 (one `graphify_lang/_common.py`). Fixing H2/M4 in one place instead of five is the practical reason.
- **Resolution (2026-09-26, plan 05 S3)**: fixed by E2: `graphify_lang/_common.py` (`2c3e6e9`) holds the lazy id helpers, `Sink`, `refs_of` / `resolve_ref_id`, `pick_by_prefix`, `load_manifest`, `load_builtins`; bmake, ecschema, astgrep, vba, autolisp, cc-kb and cargo moved one commit each (`2c3e6e9`, `05ddbef`, `569ef3e`, `bbf0a1f`, `67a582c`, `71ab8e8`, `b244901`). Each plugin keeps only its language logic (`graphify_lang/` +270 / -603 lines over the stage).

### L12 Stale comments and docstrings (SG000.005 rule 9)

- **Where**: `graphify_lang/astgrep/extract.py:18-20,32` (PyYAML "not a graphify dependency": it is one since lang.3, `pyproject.toml:45`; the flat parser `:55-99` and the `_yaml is None` branches are now dead); `graphify_lang/manifest.py:86` (path is `.claude/docs/cc-IP000.001.md`), `:219,223` ("the registry will call runtime.build": it never does); `graphify_lang/autolisp/resolve.py:79` (see H2); `graphify_lang/registry.py:1` ("or namespace").
- **Fix**: correct or delete; delete the flat YAML parser.
- **Resolution (2026-09-26, plan 05 S3)**: fixed in `4618429` (`manifest.py` schema path and the `runtime.build` comments, `registry.py:1`), `e837ed2` (`astgrep/extract.py` docstring; the flat YAML parser, the regex `matches` scan and every `_yaml is None` branch deleted with their test) and `67a582c` (`autolisp/resolve.py:79`).

### L9 Cargo augment reads outside the scan root

- **Where**: `graphify_lang/cargo/augment.py:62-68` (walks every parent directory up to `/`), `:51-55` (`root.glob(pattern)` accepts `../` patterns).
- **Problem**: a repo graphed inside another Cargo workspace inherits that outer workspace's dependency table; member globs can reach outside the repo.
- **Fix**: stop at the scan root (or move to the resolver per H3, where only graphed nodes are visible).
- **Resolution (2026-09-26, plan 05 S4.3)**: fixed in `22855e9` with H3: the cargo resolver sees only graphed nodes, so an outer workspace outside the scan root is never read. Test `test_l9_outer_workspace_ignored`.

### L11 ast-grep `ruleDirs` with `..` never match

- **Where**: `graphify_lang/astgrep/resolve.py:80-83`.
- **Problem**: `Path.is_relative_to` is lexical; `ruleDirs: ["../shared/rules"]` yields no `loads` edges.
- **Fix**: `posixpath.normpath` both sides first.
- **Resolution (2026-09-26, plan 05 S4.4)**: fixed in `dc8a8ec` (`os.path.normpath` on both sides). Test `test_l11_dotdot_ruledirs`.

### L6 Upper-case suffix variants are redundant

- **Where**: `graphify/lang_registry.py:36-42,94`.
- **Problem**: upstream already lower-cases (`classify_file`, `extract.py:6891-6892` fallback, `resolver_registry.py:80`), so `.LSP` entries only add noise to the core tables; `extract.py:6754-6757` then finds no manifest for them anyway. The comment at `:36` says "casefolded" but the code adds `upper()`.
- **Fix**: drop the `upper()` variants and fix the comment.
- **Resolution (2026-09-26, plan 05 S5.4)**: fixed in `7d9fbf8`; comment fixed. `tests/upstream_tables.json` unchanged (it is the plugins-disabled snapshot). Test `test_l6_no_upper_variants` (an `ERR.LSP` file still extracts).

### L7 Two entry-point groups and a dead Python 3.9 path

- **Where**: `graphify_lang/registry.py:55-94` scans `graphify_lang.plugins` and `graphify_lang_plugins` with duplicated loops; the `entry_points().get(...)` fallback (`:63-64,81-82`) and `import importlib_metadata` (`:58-59`) cannot run under `requires-python >= 3.10`.
- **Fix**: one group (`graphify_lang_plugins`, as `pyproject.toml:122` ships), one loop.
- **Resolution (2026-09-26, plan 05 S5.2)**: fixed in `4071b40`: one group, `graphify_lang_plugins`, one loop, no `importlib_metadata` fallback. Test `test_l7_single_group`.

### L8 Core hook sites swallow errors silently

- **Where**: `graphify/detect.py:49-50,535-536`, `graphify/extract.py:6719-6720,6758-6759,6883-6884,6920-6921`, `graphify/cli.py:82-83` (`except Exception: pass`).
- **Problem**: a bug in `claims_file` or `augment_extractor` silently reverts files to stock behaviour on every call, with no trace.
- **Fix**: `except Exception as exc: logging.getLogger("graphify.lang_registry").debug(...)` (keeps the one-line upstream diff).
- **Resolution (2026-09-26, plan 05 S5.4)**: fixed in `34510f8`: the seven sites plus the two S4 `context_fields` fallbacks log at debug level to `graphify.lang_registry`. Test `test_l8_hook_error_logged`.

### L10 Router suffixes widen `collect_files`

- **Where**: `graphify/lang_registry.py:92-94` puts `.yml`, `.yaml`, `.xml` routers in `_DISPATCH`; upstream `collect_files` (`graphify/extract.py:8698,8729`) collects every `_DISPATCH` suffix.
- **Problem**: every YAML/XML file under a `python -m graphify.extract <dir>` scan is dispatched to a router that returns empty results: wasted reads.
- **Fix**: accept, or omit `[match]`-only suffixes from `dispatch_table` (they only reach extraction through `claims_file`, which gives CODE).
- **Resolution (2026-09-26, plan 05 S5.4)**: closed as accepted. `_get_extractor` finds extractors only in `_DISPATCH` (no built-in claims `.yml`, `.yaml`, `.xml`), so dropping the routers would stop claimed files being extracted. Measured cost on this repo: `collect_files` returns 27 `.yml`/`.xml` files, 16 unclaimed, 0.1 ms of router time in total (the glob fails before any read). Test `test_l10_claimed_yml_still_extracted` pins the router.

### L13 Upstream-file edit in `resolver_registry.py`

- **Where**: `graphify/resolver_registry.py:78-80`.
- **Problem**: case-folding changes activation for every upstream resolver (a `.PY` file now activates the Python resolver) and is a direct edit outside the registry-lookup rule; each upstream rebase can conflict. Tracked as T10.4 but not proposed.
- **Fix**: send it upstream as its own small PR (T10.4) and drop it from the fork once merged.
- **Resolution (2026-09-26, plan 05 S5.4)**: closed: kept in the fork per hub D2 and pinned by `test_l13_upper_suffix_activates_resolver` (a `.LSP` file activates the AutoLISP resolver). The upstream PR draft (T10.4) is written in S006; the fork edit goes when upstream merges it.

## Nit

- **N4** `text.count("\n", 0, m.start())` per match is quadratic (`autolisp/extract.py:252,298,304,331`, `astgrep/extract.py:132`); use a `bisect` over newline offsets if a large file shows up.
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b`. `_line_of(text, pos)` bisects a cached tuple of newline offsets (autolisp headers, regex fallback, DCL dialogs; astgrep `_key_line`). Corpus graphs byte-identical.
- **N6** `docs/30-TODO.md:46` and `docs/35-DONE.md:270` mark T9.5 done with "(TODO: run manually)" inside it; resolve with M10.
- **Resolution (2026-09-26, plan 05 S2.4)**: fixed in `1e2e430`. T9.5 in `docs/30-TODO.md` and `docs/35-DONE.md` no longer carries "(TODO: run manually)" and cites M10.

- **N3** Manifest keys that nothing reads: `type`, `grammar.kind`, `language_fn`, `version`, `case_insensitive`, `builtins_file`, `builtins_prefixes` (for example `autolisp/graphify-lang.toml:5,13-17,23-24`); the builtins lists are hard-coded again in `autolisp/extract.py:31-32`. Delete the unread keys or read them.
- **Resolution (2026-09-26, plan 05 S3)**: fixed in `7711700` (engine: the top-level `schema` key is read, only 1 / `"v1"`), `0db2814` (`type`, `grammar.kind`, `grammar.language_fn`, `grammar.version` deleted from the shipped manifests; the templates keep only keys the rules engine reads), `bbf0a1f` and `67a582c` (`builtins_file`, `builtins_prefixes`, `case_insensitive` read by `load_builtins` and the `Sink`; the copy in `autolisp/extract.py:31-32` is gone). Tests `test_n3_every_manifest_key_is_read[12 manifests]` (red `5287844`) and `test_n3_schema_is_read`. `graphify lang list` shows 9 languages.

- **N5** `[match] filenames` compare case-sensitively (`registry.py:240`): `cargo.toml` on a case-insensitive filesystem is not claimed.
- **Resolution (2026-09-26, plan 05 S5.4)**: fixed in `b80a115` (`casefold()` on both sides). Test `test_n5_cargo_toml_casefold`.

- **N1** `.claude/CLAUDE.md` cites `_DISPATCH` at `graphify/extract.py:5630`; it is at `:6601`. Cite the symbol, not the line.
- **Resolution (2026-09-26, plan 05 S6.2)**: fixed in `acdac5f`: `.claude/CLAUDE.md` names `_DISPATCH`, `CODE_EXTENSIONS` and `_HOOK_SOURCE_EXTS` with their files, no line numbers.
- **N2** `docs/plans/00-INDEX.md` and plan headers mark plans 01 and 02 ACTIVE; plan 02 shipped in lang.1 (plan 01 is open only for T10).
- **Resolution (2026-09-26, plan 05 S6.2)**: fixed in `acdac5f`: plan 02 DONE; plan 01 `ACTIVE (open only for T10, the upstream PRs; drafts in docs/upstream/)`; `docs/plans/00-INDEX.md` regenerated with the `manifest` verb.

## Enhancements

- **E6** Visited-set memoisation in `astgrep._matches` (the H4 fix). — Effort: TRIVIAL | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S1.2)**: done with H4 in `f3357fb`.
- **E9** CI on `autolisp`, `lang-*`, `v*` tags with `bandit` over `graphify_lang` (M8). — Effort: TRIVIAL | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S2.2)**: done with M8 in `23735ce` (CI fix `3d3b99f`).
- **E2** `graphify_lang/_common.py`: lazy id helpers, one `_Out` sink with index-based refs and suffix-qualified file ids, `pick_by_prefix`, `load_manifest(pkg, toml, **fields)`. — Effort: MODERATE | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S3)**: done in `2c3e6e9` and the plugin moves listed under L5.
- **E7** Remove the rules engine and templates (M6). — Effort: TRIVIAL | Benefit: NEUTRAL
- **Resolution (2026-09-26, plan 05 S3)**: closed: rejected per D-008 (plan 05 hub D1); the engine stays and gained users (M6).
- **E8** `lru_cache` on `cc_kb.augment._is_root` and one `by_id` map in the cc-kb resolver (L3). — Effort: TRIVIAL | Benefit: MINOR
- **Resolution (2026-09-26, plan 05 S3)**: done in `a5a899c` (`functools.lru_cache` on `cc_kb.augment._is_root`; test `test_e8_cc_kb_is_root_cached`, 6 augment scans for 6 docs before, 1 after). Stage 4 (H3) moves the scan into the resolver.
- **E1** Plugin-set fingerprint in the AST cache namespace (fixes M2), set from `_apply_registry`. — Effort: LOW | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S4.5)**: done in `2e2cba1`: `-lang<fingerprint>` (manifest names, plugin distribution versions, a hash of every `graphify_lang` and plugin package `.py` / `.toml`) is appended to `graphify.cache._EXTRACTOR_VERSION` from `_apply_registry`. Pre-stage-3 entries (refs without `node`) sit in the plain namespace and are never read (`test_e1_pre_stage3_entries_unreachable`).
- **E5** One parity test: for each plugin fixture, full build == full build then touch-one-file incremental build (edges and ids). — Effort: LOW | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S4.1-S4.2)**: done: `test_e5_incremental_parity` over autolisp (2 trees), vba, bmake, cargo, astgrep, ecschema, cc-kb, every plugin file touched in turn; red `a5961fe`, green `cd55efb`.
- **E4** `graphify lang list --check`: load every manifest, report load errors per plugin (complements M1). — Effort: LOW | Benefit: NEUTRAL
- **Resolution (2026-09-26, plan 05 S5.2)**: done in `a05bc8b` (engine `check_languages`) and `cb21e7e` (`cli.py` `lang` branch): one row per plugin, `ok` or `error: <reason>`, exit 1 when any plugin failed; 9 `ok` rows on this tree. Test `test_e4_lang_list_check`.
- **E3** Upstream PR: forward `node_kind` (or a registrable marker list) in `watch.py` context nodes (fixes H1 at the root). — Effort: LOW | Benefit: HIGH. Fork side done in `2adf7bc` (plan 05 S4.2); open until the upstream PR draft is written in S006.
- **Resolution (2026-09-26, plan 05 S6.3)**: done in `31db078`: `docs/upstream/pr-02-resolver-context-fields.md` (a `context_fields` field on `LanguageResolver`, forwarded with `_abs_source_file` by both context-node builders), plus drafts for the entry-point registry lookups, watch code-path claims (M3) and the resolver suffix case-fold (L13). Each diff applies to `upstream/v8` `4000de1` and its test passes there (2 / 3 / 3 / 2 passed; full upstream suite green with each). Not opened on GitHub.
