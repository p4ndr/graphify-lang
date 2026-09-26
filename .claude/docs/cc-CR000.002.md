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

## High

### H4 ast-grep YAML alias expansion: unbounded time and recursion on crafted input (security, DoS)

- **Where**: `graphify_lang/astgrep/extract.py:106-116` (`_matches` walks the `yaml.safe_load` tree), called outside the per-document `try` at `extract.py:205,251`.
- **Problem**: `safe_load` shares aliased subtrees, but `_matches` traverses every reference, so N levels of 10 aliases cost 10^N visits; a self-referencing alias (`rule: &a {any: [*a]}`) recurses until `RecursionError`. graphify is run on arbitrary third-party repos, and the file only needs to sit under `rules/`, `utils/` or `rule-tests/` with `id:` plus one body key to be claimed.
- **Failure scenario (measured)**: a 377-byte `rules/bomb.yml` with 6 alias levels takes 0.59 s; each extra level multiplies by 10 (9 levels, under 500 bytes, is about 10 minutes; 10 levels about 100 minutes), hanging `graphify update`. The recursive alias raises `RecursionError`; upstream then skips the whole file ("recursion limit exceeded"), losing even its file node.
- **Fix**: memoise by object identity in `_matches` (a `seen: set[int]` of `id(obj)` for dicts/lists; return on revisit). That bounds work to the number of distinct YAML nodes and ends the recursion. Also wrap `_rule_doc` in the per-document `try` so a malformed document keeps the file node, as the module docstring promises.
- **Resolution (2026-09-26, plan 05 S1.2)**: fixed in `f3357fb` (fix), tests `029c35e` + `f3357fb`. `_matches` keeps a `seen` set of `id()` for dicts and lists; the whole per-document body (new `_document`, `_rule_doc` included) runs inside the per-document `try`. Tests `tests/lang/test_s1_safety.py::test_h4_alias_bomb_bounded[6|9]`, `test_h4_self_alias_keeps_file_node`. Measured in a child process: 9 alias levels (406 bytes) > 30 s timeout before, 0.04 s after; 6 levels 0.32 s before, 0.04 s after (incl. lazy import). llm-linter-tool graph byte-identical.

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

## Enhancements

- **E6** Visited-set memoisation in `astgrep._matches` (the H4 fix). — Effort: TRIVIAL | Benefit: HIGH
- **Resolution (2026-09-26, plan 05 S1.2)**: done with H4 in `f3357fb`.
