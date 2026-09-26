# Code review: graphify-lang fork layer, resolved findings

Findings moved out of `cc-CR000.001.md` once fixed or closed. Each entry keeps the original text and adds the resolution.

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

## High

### H4 ast-grep YAML alias expansion: unbounded time and recursion on crafted input (security, DoS)

- **Where**: `graphify_lang/astgrep/extract.py:106-116` (`_matches` walks the `yaml.safe_load` tree), called outside the per-document `try` at `extract.py:205,251`.
- **Problem**: `safe_load` shares aliased subtrees, but `_matches` traverses every reference, so N levels of 10 aliases cost 10^N visits; a self-referencing alias (`rule: &a {any: [*a]}`) recurses until `RecursionError`. graphify is run on arbitrary third-party repos, and the file only needs to sit under `rules/`, `utils/` or `rule-tests/` with `id:` plus one body key to be claimed.
- **Failure scenario (measured)**: a 377-byte `rules/bomb.yml` with 6 alias levels takes 0.59 s; each extra level multiplies by 10 (9 levels, under 500 bytes, is about 10 minutes; 10 levels about 100 minutes), hanging `graphify update`. The recursive alias raises `RecursionError`; upstream then skips the whole file ("recursion limit exceeded"), losing even its file node.
- **Fix**: memoise by object identity in `_matches` (a `seen: set[int]` of `id(obj)` for dicts/lists; return on revisit). That bounds work to the number of distinct YAML nodes and ends the recursion. Also wrap `_rule_doc` in the per-document `try` so a malformed document keeps the file node, as the module docstring promises.
- **Resolution (2026-09-26, plan 05 S1.2)**: fixed in `f3357fb` (fix), tests `029c35e` + `f3357fb`. `_matches` keeps a `seen` set of `id()` for dicts and lists; the whole per-document body (new `_document`, `_rule_doc` included) runs inside the per-document `try`. Tests `tests/lang/test_s1_safety.py::test_h4_alias_bomb_bounded[6|9]`, `test_h4_self_alias_keeps_file_node`. Measured in a child process: 9 alias levels (406 bytes) > 30 s timeout before, 0.04 s after; 6 levels 0.32 s before, 0.04 s after (incl. lazy import). llm-linter-tool graph byte-identical.

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
- **Resolution (2026-09-26, plan 05 S2.2)**: fixed in `23735ce`, CI 3.10 fix `3d3b99f`. `graphify-lang-ci.yml` triggers on push/PR to `autolisp`, `lang-*`, `rr-*`, `v8` and on `v*` tags; the security job runs `bandit -r graphify graphify_lang -ll`. Local bandit over `graphify_lang`: 0 issues at any severity. First fork CI run on `rr-s2` (36219014956) failed on 3.10: `tests/lang/test_rules.py` imported `tomllib` bare; fixed with the tomli fallback. Run 36219115105 green: 3.10 6149 passed/19 skipped, 3.12 and 3.13 6148/20, security-scan success (its 4 High are upstream B324 in `graphify/_minhash.py`, `extract.py:391`, `extractors/engine.py`, `extractors/resolution.py`).

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

## Low

### L1 AutoLISP walker recursion overflows on deep nesting

- **Where**: `graphify_lang/autolisp/extract.py:150-234` (`_Walker.walk` / `walk_list` recurse per list level), called outside the `try` at `extract.py:275-277`.
- **Failure scenario (measured)**: a defun with 1200 nested `(list ...)` raises `RecursionError`; upstream skips the whole file. Rare in hand-written code, possible in generated LISP.
- **Fix**: an explicit stack, or catch `RecursionError` in `extract_autolisp` and fall back to the regex path already used for `root.has_error` (`extract.py:293-304`).
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b` (fix), test `029c35e`. `extract_autolisp` catches `RecursionError` from the walk and uses the regex fallback (`fallback = root.has_error` or the overflow). Test `test_l1_deep_nesting_falls_back` (1200 levels at recursion limit 1000; `graphify.extract` raises the limit to 10 000 on import, so the pipeline overflows only near 5000 levels).

### L2 Quadratic edge de-duplication in two sinks

- **Where**: `graphify_lang/ecschema/extract.py:127-132` and `graphify_lang/astgrep/extract.py:174-179` scan `self.edges` linearly per edge.
- **Problem**: O(E²) per file; a large ECSchema (tens of thousands of properties) costs minutes. The other sinks use an `_edge_keys` set.
- **Fix**: use the `_edge_keys` set as `bmake/extract.py:119-125` does.
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b` (fix), test `029c35e`. Both sinks use an `_edge_keys` set. Test `test_l2_large_schema_linear`: 20 000 properties 25.1 s before, 0.18 s after. BentleyHelp graph byte-identical.

### L4 Manifest validation can still raise and does not normalise suffixes

- **Where**: `graphify_lang/manifest.py:131-133,135-206` (`data.get("language", {})` then `.get` on it: a TOML `language = "x"` raises `AttributeError`, contradicting "never an exception" at `:116`); `:164` accepts a non-string `name` (later `re.sub` in `registry.py:392` fails); `:245-247` checks the leading dot but not case, so `.LSP` in a manifest never matches (`registry.py:381,422` lower-case the path suffix).
- **Fix**: check each section `isinstance(..., dict)`; require `isinstance(name, str)`; lower-case `suffixes`, `augments`, `overrides`, `hook_suffixes`.
- **Resolution (2026-09-26, plan 05 S1.4)**: fixed in `d498a6f` (fix, engine), test `1e678c5`. A non-table `[language]`, `[grammar]`, `[extract]` or `[match]` and a non-string `name` are one-line errors; `suffixes`, `hook_suffixes`, `augments`, `overrides` are lower-cased (order kept, duplicates dropped). Tests `tests/test_lang_manifest_safety.py`. All 9 shipped languages load.

## Nit

- **N4** `text.count("\n", 0, m.start())` per match is quadratic (`autolisp/extract.py:252,298,304,331`, `astgrep/extract.py:132`); use a `bisect` over newline offsets if a large file shows up.
- **Resolution (2026-09-26, plan 05 S1.3)**: fixed in `10f235b`. `_line_of(text, pos)` bisects a cached tuple of newline offsets (autolisp headers, regex fallback, DCL dialogs; astgrep `_key_line`). Corpus graphs byte-identical.
- **N6** `docs/30-TODO.md:46` and `docs/35-DONE.md:270` mark T9.5 done with "(TODO: run manually)" inside it; resolve with M10.
- **Resolution (2026-09-26, plan 05 S2.4)**: fixed in `1e2e430`. T9.5 in `docs/30-TODO.md` and `docs/35-DONE.md` no longer carries "(TODO: run manually)" and cites M10.

## Enhancements

- **E6** Visited-set memoisation in `astgrep._matches` (the H4 fix). — Effort: TRIVIAL | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S1.2)**: done with H4 in `f3357fb`.
- **E9** CI on `autolisp`, `lang-*`, `v*` tags with `bandit` over `graphify_lang` (M8). — Effort: TRIVIAL | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S2.2)**: done with M8 in `23735ce` (CI fix `3d3b99f`).
