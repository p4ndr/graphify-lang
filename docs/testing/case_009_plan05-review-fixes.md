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
| S1-M1 | actioned | `4bf2374` test, `79ca519` fix | One pass over indented keys per document; 20 000 utils 18.93 s -> under 2 s; llm-linter-tool 82 YAML files output identical. |
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
