# Code review: graphify-lang fork layer

| Severity | Count |
|:---------|------:|
| Critical | 0 |
| High | 4 |
| Medium | 12 |
| Low | 13 |
| Nit | 6 |
| **Defects total** | **35** |
| Enhancements | 9 |

- **Date**: 2026-09-26
- **Mode**: Diff (`git diff upstream/v8...autolisp`), branch `autolisp`, HEAD `013c902` (v0.9.67+lang.3)
- **Scope**: `graphify/lang_registry.py`; the registry-lookup blocks in `graphify/detect.py`, `extract.py`, `cli.py`; `graphify/resolver_registry.py`; `graphify_lang/**` (registry, manifest, rules engine, templates, plugins autolisp, vba, bmake, cargo, astgrep, ecschema, cc_kb); fork tests and fixtures; `pyproject.toml`; `.github/workflows/*`; fork docs. Upstream code only where the fork depends on it.
- **Focus**: Comprehensive
- **Verification**: `pytest tests/ -q` = 6141 passed, 14 skipped (86 s); fork tests alone 172 passed, 0 skipped on this host. Every High and most Medium findings were reproduced with a probe in the repo `.venv` (probe named in the finding). No source file was modified.
- **Repo rules respected in every fix**: no edit to existing extractors, `engine.py`, `resolution.py` or upstream tests; core tables change only through registry lookups. A fix that needs a core change is marked **upstream PR**.

## High

### H1 Incremental rebuild drops every cross-file plugin edge into unchanged files

- **Where**: all plugin resolvers index targets by `node_kind`: `graphify_lang/autolisp/resolve.py:26`, `graphify_lang/vba/resolve.py:59`, `graphify_lang/bmake/resolve.py:68`, `graphify_lang/astgrep/resolve.py:51-55`, `graphify_lang/cc_kb/resolve.py:60`. Upstream dependency: `graphify/watch.py:1723-1729` builds the resolution-context node for unchanged files from `id`, `label`, `source_file`, `file_type`, `type` plus a fixed marker list; `node_kind` (and `astgrep_scope`, `visibility`, `accessor`) is not forwarded.
- **Problem**: on an incremental rebuild (`_rebuild_code(changed_paths=...)`, used by the git post-commit hook, the Claude hook flow and `graphify watch`), the resolvers see unchanged files' nodes without `node_kind`, so no target in an unchanged file is found. The changed file's old edges were removed with its re-extraction, so the edges disappear.
- **Failure scenario (measured)**: corpus `src/app.lsp` `(defun c:go () (libfn))` + `src/lib.lsp` `(defun libfn ...)`. Full build: `src_app_c_go calls src_lib_libfn`. Edit `app.lsp` only, run `graphify.watch._rebuild_code(root, changed_paths=[app.lsp])`: the `calls` edge is gone. Same mechanism for VBA calls, bmake includes/macros, ast-grep util/test links, cc-kb `cites`, ECSchema cross-schema refs.
- **Fix**: **upstream PR** (generic, small): forward `node_kind` (or a plugin-declared marker list) in the `ctx_node` at `watch.py:1723`. Until then, a plugin-side mitigation: resolvers fall back to classifying context nodes without `node_kind` by id shape or by a marker upstream already forwards (for example the node `type` field, but check `_disambiguate_colliding_node_ids` exempts `type in ("module","namespace")`). Add a test that compares a full build with full-then-incremental for every plugin fixture (E5).

### H2 AutoLISP and VBA resolver refs carry extraction-time ids; same-stem files lose edges

- **Where**: `graphify_lang/autolisp/extract.py:104-106` (`ref` stores `source` id), consumed at `graphify_lang/autolisp/resolve.py:54-60,74-89`; `graphify_lang/vba/extract.py:156-159`, `graphify_lang/vba/resolve.py:89-94`. Upstream dependency: `_disambiguate_colliding_node_ids` (`graphify/extractors/resolution.py:929`) renames colliding node dicts in place at `graphify/extract.py:7944`, before `run_language_resolvers` (`extract.py:8480-8484`).
- **Problem**: when two files share a stem (the normal AutoCAD layout `foo.lsp` + `foo.mnl` + `foo.dcl`, or a same-named defun in `foo.lsp` and `foo.mnl`), their ids are salted apart before the resolver runs, but the ref still names the old id. The edge is emitted with a dangling source and later pruned, silently. bmake, ecschema and astgrep already avoid this by storing the node index (`bmake/extract.py:132-135`, ltm learning 1477); autolisp and vba do not. The comment at `autolisp/resolve.py:79-80` ("graphify already gives both files one node id") is wrong for the same reason.
- **Failure scenario (measured)**: `app.lsp` with `(defun helper () (libfn))`, `app.mnl` with its own `helper`, `sub/lib.lsp` with `libfn`: `extract()` emits `app_helper calls sub_lib_libfn` where `app_helper` no longer exists (nodes are `app_lsp_app_helper`, `app_mnl_app_helper`). Sidecar refs from a colliding file node dangle the same way.
- **Fix**: adopt the bmake pattern in both plugins: store `node` (index into the result's `nodes`) in each ref and read `res["nodes"][ref["node"]]["id"]` in the resolver; keep `dialogs_of` keyed by the current id. Add a same-stem fixture test (`x.lsp` + `x.mnl` + `x.dcl` with cross-file calls and a sidecar).

### H3 Augment output depends on other files but is cached by this file's content hash

- **Where**: `graphify_lang/cargo/augment.py:46-68` (`_members` globs member dirs and reads their `Cargo.toml`; `_workspace_deps` reads parent manifests); `graphify_lang/cc_kb/augment.py:64-82,85-102` (`_is_root` scans `docs/`, `_code_ref` calls `is_file()` on the referenced path). Upstream dependency: `graphify/cache.py:965` keys AST entries by file content + package version only.
- **Problem**: the extractor contract behind the AST cache is "output is a function of the file's bytes". These augments break it, so a cached result survives changes elsewhere.
- **Failure scenario (measured)**: workspace `members = ["crates/*"]` with crate `a`: `has_member -> pkg_a`. Add `crates/b/Cargo.toml` (root manifest unchanged) and rebuild with the same cache: still only `pkg_a`; a fresh cache gives `pkg_a, pkg_b`. For cc-kb: a doc that mentions `` `scripts/new.ps1` `` before the script exists never gains its `cites` edge until the cache is cleared.
- **Fix**: keep augments pure. Emit the raw payload (member globs and `exclude` relative to the manifest dir; renamed/workspace deps by key; every path-like code span) and let the resolver, which runs every build over the whole corpus, match against graphed nodes (`pkg_*` nodes by their `source_file` dir; file nodes by normalised path). This also removes the filesystem reads from extraction.

### H4 ast-grep YAML alias expansion: unbounded time and recursion on crafted input (security, DoS)

- **Where**: `graphify_lang/astgrep/extract.py:106-116` (`_matches` walks the `yaml.safe_load` tree), called outside the per-document `try` at `extract.py:205,251`.
- **Problem**: `safe_load` shares aliased subtrees, but `_matches` traverses every reference, so N levels of 10 aliases cost 10^N visits; a self-referencing alias (`rule: &a {any: [*a]}`) recurses until `RecursionError`. graphify is run on arbitrary third-party repos, and the file only needs to sit under `rules/`, `utils/` or `rule-tests/` with `id:` plus one body key to be claimed.
- **Failure scenario (measured)**: a 377-byte `rules/bomb.yml` with 6 alias levels takes 0.59 s; each extra level multiplies by 10 (9 levels, under 500 bytes, is about 10 minutes; 10 levels about 100 minutes), hanging `graphify update`. The recursive alias raises `RecursionError`; upstream then skips the whole file ("recursion limit exceeded"), losing even its file node.
- **Fix**: memoise by object identity in `_matches` (a `seen: set[int]` of `id(obj)` for dicts/lists; return on revisit). That bounds work to the number of distinct YAML nodes and ends the recursion. Also wrap `_rule_doc` in the per-document `try` so a malformed document keeps the file node, as the module docstring promises.

## Medium

### M1 One failing plugin disables every plugin

- **Where**: `graphify_lang/registry.py:112-118` (`result = result()` runs outside the `try` at `registry.py:71-75` and `89-93`); every shipped `_get_manifest` raises `ValueError` on a TOML error (for example `graphify_lang/bmake/__init__.py:19-21`).
- **Problem**: the exception propagates out of `_init_state`; `_apply_registry` (`graphify/lang_registry.py:47-49`) catches it and sets `_REGISTRY_AVAILABLE = False`, so all plugins vanish behind one warning. Manifests registered before the failure stay in `_STATE`, so later direct registry calls see a partial state.
- **Failure scenario (measured)**: an entry point whose manifest callable raises, loaded first: every `registered_names()` call raises `ValueError`; with the core wrapper, no plugin suffix is registered.
- **Fix**: move `result = result()` inside the per-entry-point `try` (log `failed to load entry point %s`), or wrap `_process_loader_result(ep.name, result)` in it. Add a test with one raising entry point next to a good one.

### M2 AST cache is shared across different plugin sets

- **Where**: `graphify/cache.py:957` (`v{_EXTRACTOR_VERSION}-s{schema}` namespace); registry state in `graphify_lang/registry.py:49-50`.
- **Problem**: the extractor chosen for a file depends on the active plugin set (`GRAPHIFY_LANG_DISABLE`, a third-party plugin installed or removed), but the cache key does not. Known (ltm learning 1480) but unmitigated.
- **Failure scenario (measured)**: run `extract()` on `app.lsp` with `GRAPHIFY_LANG_DISABLE=1`, then without it, same cache dir: the second run returns the stock Common Lisp result (2 nodes, no `node_kind`); a fresh cache gives the AutoLISP result (file, command, function, module). Same for `.cls` (Apex vs VBA) and `.md` (cc-kb augment).
- **Fix**: E1: in `_apply_registry`, append a fingerprint of the registered manifests (names, plugin distribution versions, maybe a hash of plugin module files) to `graphify.cache._EXTRACTOR_VERSION` (a runtime attribute set, no source edit), so each plugin set gets its own namespace.

### M3 `graphify watch` ignores plugin-claimed data files

- **Where**: upstream `graphify/watch.py:282` (`_WATCHED_EXTENSIONS`), `watch.py:2306` (`_batch_triggers_rebuild` checks `_CODE_EXTENSIONS`); fork `graphify/lang_registry.py:41-43` adds `[match]` suffixes only to the hook list.
- **Problem**: `.xml` is in neither `CODE_EXTENSIONS` nor `DOC_EXTENSIONS`, so an ECSchema edit produces no watch event at all; `.yml` (ast-grep), `Cargo.toml` (cargo augment) and `.md` (cc-kb augment) edits are treated as doc changes and never trigger the AST rebuild. The git-hook path works (it uses `_HOOK_SOURCE_EXTS`), watch mode does not.
- **Fix**: **upstream PR** or a registry lookup in `_batch_triggers_rebuild` and the watch filter: treat a path as code when `lang_registry.claims_file(path)` or an augment claims it. Adding the suffixes to `CODE_EXTENSIONS` is not an option (it would classify every `.xml` as code).

### M4 Plugin file-node ids diverge from upstream and become non-portable on collision

- **Where**: every plugin sink uses `self.stem = _make_id(_file_stem(path))` as the file-node id: `autolisp/extract.py:72,78`, `vba/extract.py:132,138`, `bmake/extract.py:97,108`, `ecschema/extract.py:110,116`, `astgrep/extract.py:157,163`, `rules.py:40,48`.
- **Problem**: upstream file nodes use the full path including the suffix (`extract_python` gives `..._app_py`), so `app.py` and `app.js` never collide. The plugin ids drop the suffix, so `app.lsp`/`app.mnl`/`app.dcl` collide; the salted replacement is built from the old id, which already contains the absolute scan-root path, and the later portable-id remap does not undo it.
- **Failure scenario (measured)**: file nodes come out as `app_lsp_tmp_claude_1000_home_p4ndr_..._c1_app`: the absolute checkout path is baked into graph ids, so the same repo graphs differently on another machine or path (breaks graph diffs and `graphify global` merges).
- **Fix**: mint the file-node id the way the built-ins do (`_make_id(str(path))`, suffix included, so upstream's portable remap applies) and keep symbol ids stem-based; re-run the case 004/007 corpus counts. This also removes most of the collisions behind H2.

### M5 `GRAPHIFY_LANG_PATH` is collected and never used; docs say tests rely on it

- **Where**: `graphify_lang/registry.py:96-108` (paths go into `search_paths`, which nothing reads; when any entry point registered a manifest first, `_STATE` already exists and the list is discarded); `docs/55-SETTLED.md:125` ("Development and tests discover the plugin through `GRAPHIFY_LANG_PATH`"); `docs/35-DONE.md:289`; module docstring `registry.py:1` ("or namespace", not implemented). `_RegistryState.enabled` (`registry.py:30`) is also never read.
- **Failure scenario**: a user or test sets `GRAPHIFY_LANG_PATH` to a directory with a manifest; nothing is loaded and nothing is logged.
- **Fix**: delete `_PATH_VAR`, `search_paths` and `enabled` (YAGNI; entry points cover packaging and tests), and correct the two docs and the docstring. Implement path discovery only when a real out-of-tree plugin needs it.

### M6 Declarative rules engine is dead weight (ponytail)

- **Where**: `graphify_lang/rules.py` (132 lines), `queries.py` (133), `regex_rules.py` (101), `builtins.py` (45), `templates/*.toml` (179), `tests/lang/test_rules.py` (259), fixtures `tests/lang/rules_dcl.toml`, plus shipped package data.
- **Problem**: no plugin calls `rules.build()`; its own docstring says "none depends on it". It also carries an import-by-string hook (`rules.py:86-95`, `post_file = "module:fn"` from TOML). Every shipped plugin duplicates what it would provide (builtins lists, sinks).
- **Fix**: delete the engine, its tests and the templates (git keeps them), or move them to the `lang-rules` branch until a plugin needs them.

### M7 `publish.yml` and `release-graph.yml` are corrupted YAML

- **Where**: `.github/workflows/publish.yml:20,33,36,39,50,53` and `release-graph.yml:17,25,34,39,42,52,58` (a trailing `:` was appended to lines, for example `contents: read:`, `uses: actions/checkout@v4:`).
- **Problem (measured)**: `yaml.safe_load` fails on both files ("mapping values are not allowed here"). The `if: github.repository == 'Graphify-Labs/graphify'` guard never gets evaluated because the file does not parse; a release event on the fork shows an invalid-workflow failure, and the corruption would break publishing if the diff ever went upstream. It also adds rebase conflicts in upstream-owned files.
- **Fix**: `git checkout upstream/v8 -- .github/workflows/publish.yml .github/workflows/release-graph.yml`, then re-add only the one-line `if:` guards (or disable the workflows in the fork's repo settings instead of editing them).

### M8 Fork CI does not run on the release branch

- **Where**: `.github/workflows/graphify-lang-ci.yml:4-7` (branches `lang-registry`, `v8`); upstream `ci.yml:5-7` (v1-v8, main). Releases are cut from `autolisp` (README 'Installing the fork').
- **Problem**: no workflow runs on a push to `autolisp` or on the `v*+lang.*` tags, so a released wheel is never CI-tested. The security job's `bandit -r graphify` (`:56`) skips `graphify_lang`.
- **Fix**: trigger on `autolisp` and `lang-*` branches and on `v*` tags; run `bandit -r graphify graphify_lang`.

### M9 Committed junk and scratch files

- **Where**: `git-sp.ps1` (765 lines, an unrelated sparse-checkout TUI); `.sidecar-cache/restore-8135b1ee46771d6c.json` (362 KB copy of `extract.py`) and `.sidecar-cache/T6-Resume-20260923.md`; repo-root `src_core_test.lsp`, `test_dcl.toml`, `test_pattern.toml` (unused: `tests/lang/test_autolisp_nodes.py:314` writes its own copy to `tmp_path`); `docs/testing/archive/` (32 near-duplicate `T14-*` reports); `.claude/docs/cc-T10-COMPLETE.md` (off-schema name).
- **Problem**: noise in every diff against upstream, in the repo's own graph (the root `.lsp` becomes a graph node), and in reviews; the JSON bloats clones.
- **Fix**: `git rm` them; add `.sidecar-cache/` to `.gitignore`; keep one summary of T14 if any of it is still referenced.

### M10 `scripts/install-mcp.sh` writes a config key nothing reads

- **Where**: `scripts/install-mcp.sh:1-10,64+` writes `.watch._HOOK_SOURCE_EXTS` into `~/.claude/mcp.json`.
- **Problem**: no component reads that key; hook suffixes come from the registry (`graphify/cli.py:76-83`). The script mutates a shared user config file for no effect, and `docs/30-TODO.md:46` still lists a manual run as pending.
- **Fix**: delete the script and the TODO line.

### M11 README is stale in several load-bearing places

- **Where**: `README.md:460-463` ("## Status: No code yet"); `README.md:417-437` (says the pipx venv is `graphifyy 0.9.55` and "left alone", plans `~/.venvs/graphify-lang`, "`uv` is not installed") versus `README.md:439-458` (pipx runs the fork; release uses `uv build`) and `.claude/CLAUDE.md` (develop in repo `.venv`); `README.md:342-363` roadmap without per-phase status and citing `cli.py:881`; `README.md:367` "Planned directories are marked" (none are).
- **Problem**: the entry document contradicts itself; a reader following 'Development setup' installs into the wrong venv.
- **Fix**: replace 'Status' with the current state (released `0.9.67+lang.3`, 7 plugins, `graphify lang list`); rewrite 'Development setup' to the repo `.venv` + `uv sync`; mark roadmap phases done/open (phase 6 = T10, open).

### M12 Test suite misses the failure classes above

- **Where**: `tests/lang/*`, `tests/test_lang_*.py`.
- **Problem**: no test covers incremental rebuild (H1), same-stem collisions for autolisp/vba (H2), augment cache coherence (H3, M2), hostile YAML (H4), or a failing plugin (M1). Four corpus tests (`test_vba.py:166-169`, `test_bmake.py:157-160`, `test_ecschema.py:31,184-185`, `test_astgrep.py:26,139`, `test_lang_sniff.py:165-168`) depend on private repos under `~/repos` and always skip in CI, so CI exercises only the small fixtures. `test_rules.py` (259 lines) tests the dead engine (M6).
- **Fix**: add one fixture-based test per class above (each a few lines); keep corpus tests but mark them `@pytest.mark.corpus` so skips are explicit.

## Low

### L1 AutoLISP walker recursion overflows on deep nesting

- **Where**: `graphify_lang/autolisp/extract.py:150-234` (`_Walker.walk` / `walk_list` recurse per list level), called outside the `try` at `extract.py:275-277`.
- **Failure scenario (measured)**: a defun with 1200 nested `(list ...)` raises `RecursionError`; upstream skips the whole file. Rare in hand-written code, possible in generated LISP.
- **Fix**: an explicit stack, or catch `RecursionError` in `extract_autolisp` and fall back to the regex path already used for `root.has_error` (`extract.py:293-304`).

### L2 Quadratic edge de-duplication in two sinks

- **Where**: `graphify_lang/ecschema/extract.py:127-132` and `graphify_lang/astgrep/extract.py:174-179` scan `self.edges` linearly per edge.
- **Problem**: O(E²) per file; a large ECSchema (tens of thousands of properties) costs minutes. The other sinks use an `_edge_keys` set.
- **Fix**: use the `_edge_keys` set as `bmake/extract.py:119-125` does.

### L3 cc-kb resolver and augment do avoidable linear work

- **Where**: `graphify_lang/cc_kb/resolve.py:80` (`next(n for n in all_nodes if n["id"] == node["id"])` per payload: O(files x nodes); `node` is already the live dict); `graphify_lang/cc_kb/augment.py:64-69` (`_is_root` re-scans `docs/` for every `.md`).
- **Fix**: use `node` directly (or one `by_id` dict); `functools.lru_cache` on `_is_root`.

### L4 Manifest validation can still raise and does not normalise suffixes

- **Where**: `graphify_lang/manifest.py:131-133,135-206` (`data.get("language", {})` then `.get` on it: a TOML `language = "x"` raises `AttributeError`, contradicting "never an exception" at `:116`); `:164` accepts a non-string `name` (later `re.sub` in `registry.py:392` fails); `:245-247` checks the leading dot but not case, so `.LSP` in a manifest never matches (`registry.py:381,422` lower-case the path suffix).
- **Fix**: check each section `isinstance(..., dict)`; require `isinstance(name, str)`; lower-case `suffixes`, `augments`, `overrides`, `hook_suffixes`.

### L5 Copy-paste across plugins

- **Where**: `_pick` + `shared` in `autolisp/resolve.py:30-50`, `vba/resolve.py:29-44`, `bmake/resolve.py:32-47`, `astgrep/resolve.py:26-41`; lazy `_file_stem`/`_make_id` shims in 5 extractors; `_Out` sinks in 5 extractors; 7 near-identical `_get_manifest` loaders.
- **Fix**: E2 (one `graphify_lang/_common.py`). Fixing H2/M4 in one place instead of five is the practical reason.

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

### L9 Cargo augment reads outside the scan root

- **Where**: `graphify_lang/cargo/augment.py:62-68` (walks every parent directory up to `/`), `:51-55` (`root.glob(pattern)` accepts `../` patterns).
- **Problem**: a repo graphed inside another Cargo workspace inherits that outer workspace's dependency table; member globs can reach outside the repo.
- **Fix**: stop at the scan root (or move to the resolver per H3, where only graphed nodes are visible).

### L10 Router suffixes widen `collect_files`

- **Where**: `graphify/lang_registry.py:92-94` puts `.yml`, `.yaml`, `.xml` routers in `_DISPATCH`; upstream `collect_files` (`graphify/extract.py:8698,8729`) collects every `_DISPATCH` suffix.
- **Problem**: every YAML/XML file under a `python -m graphify.extract <dir>` scan is dispatched to a router that returns empty results: wasted reads.
- **Fix**: accept, or omit `[match]`-only suffixes from `dispatch_table` (they only reach extraction through `claims_file`, which gives CODE).

### L11 ast-grep `ruleDirs` with `..` never match

- **Where**: `graphify_lang/astgrep/resolve.py:80-83`.
- **Problem**: `Path.is_relative_to` is lexical; `ruleDirs: ["../shared/rules"]` yields no `loads` edges.
- **Fix**: `posixpath.normpath` both sides first.

### L12 Stale comments and docstrings (SG000.005 rule 9)

- **Where**: `graphify_lang/astgrep/extract.py:18-20,32` (PyYAML "not a graphify dependency": it is one since lang.3, `pyproject.toml:45`; the flat parser `:55-99` and the `_yaml is None` branches are now dead); `graphify_lang/manifest.py:86` (path is `.claude/docs/cc-IP000.001.md`), `:219,223` ("the registry will call runtime.build": it never does); `graphify_lang/autolisp/resolve.py:79` (see H2); `graphify_lang/registry.py:1` ("or namespace").
- **Fix**: correct or delete; delete the flat YAML parser.

### L13 Upstream-file edit in `resolver_registry.py`

- **Where**: `graphify/resolver_registry.py:78-80`.
- **Problem**: case-folding changes activation for every upstream resolver (a `.PY` file now activates the Python resolver) and is a direct edit outside the registry-lookup rule; each upstream rebase can conflict. Tracked as T10.4 but not proposed.
- **Fix**: send it upstream as its own small PR (T10.4) and drop it from the fork once merged.

## Nit

- **N1** `.claude/CLAUDE.md` cites `_DISPATCH` at `graphify/extract.py:5630`; it is at `:6601`. Cite the symbol, not the line.
- **N2** `docs/plans/00-INDEX.md` and plan headers mark plans 01 and 02 ACTIVE; plan 02 shipped in lang.1 (plan 01 is open only for T10).
- **N3** Manifest keys that nothing reads: `type`, `grammar.kind`, `language_fn`, `version`, `case_insensitive`, `builtins_file`, `builtins_prefixes` (for example `autolisp/graphify-lang.toml:5,13-17,23-24`); the builtins lists are hard-coded again in `autolisp/extract.py:31-32`. Delete the unread keys or read them.
- **N4** `text.count("\n", 0, m.start())` per match is quadratic (`autolisp/extract.py:252,298,304,331`, `astgrep/extract.py:132`); use a `bisect` over newline offsets if a large file shows up.
- **N5** `[match] filenames` compare case-sensitively (`registry.py:240`): `cargo.toml` on a case-insensitive filesystem is not claimed.
- **N6** `docs/30-TODO.md:46` and `docs/35-DONE.md:270` mark T9.5 done with "(TODO: run manually)" inside it; resolve with M10.

## Architectural findings

- **Resolver id contract**: three of five resolvers learned to read ids back through the node index (bmake, ecschema, astgrep), two did not (H2). The contract belongs in one shared sink (E2), not in each plugin. — Impact: STRONG
- **Purity contract with the AST cache**: extractors and augments must be functions of the file bytes; everything that looks at other files belongs in the resolver (H3, M2). Write it into `README.md` 'Proposed architecture' as a plugin rule. — Impact: STRONG
- **Upstream seams the fork depends on**: `_disambiguate_colliding_node_ids` ordering, `watch.py` context-node fields (H1), `_reconcile_markdown_links` pruning only `references` (cc-kb relies on `cites` surviving, `cc_kb/resolve.py:30-33`), dict identity between `per_file` and `all_nodes` (bmake/astgrep/cc-kb index reads), `_get_extractor` suffix fallback. Each is untested from the fork side; an upstream refactor breaks them silently. A parity test (E5) covers most. — Impact: AVERAGE

## Enhancements

- **E1** Plugin-set fingerprint in the AST cache namespace (fixes M2), set from `_apply_registry`. — Effort: LOW | Benefit: HIGH
- **E2** `graphify_lang/_common.py`: lazy id helpers, one `_Out` sink with index-based refs and suffix-qualified file ids, `pick_by_prefix`, `load_manifest(pkg, toml, **fields)`. — Effort: MODERATE | Benefit: HIGH
- **E3** Upstream PR: forward `node_kind` (or a registrable marker list) in `watch.py` context nodes (fixes H1 at the root). — Effort: LOW | Benefit: HIGH
- **E4** `graphify lang list --check`: load every manifest, report load errors per plugin (complements M1). — Effort: LOW | Benefit: NEUTRAL
- **E5** One parity test: for each plugin fixture, full build == full build then touch-one-file incremental build (edges and ids). — Effort: LOW | Benefit: HIGH
- **E6** Visited-set memoisation in `astgrep._matches` (the H4 fix). — Effort: TRIVIAL | Benefit: HIGH
- **E7** Remove the rules engine and templates (M6). — Effort: TRIVIAL | Benefit: NEUTRAL
- **E8** `lru_cache` on `cc_kb.augment._is_root` and one `by_id` map in the cc-kb resolver (L3). — Effort: TRIVIAL | Benefit: MINOR
- **E9** CI on `autolisp`, `lang-*`, `v*` tags with `bandit` over `graphify_lang` (M8). — Effort: TRIVIAL | Benefit: HIGH

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
