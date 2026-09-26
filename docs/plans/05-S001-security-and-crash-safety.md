# Plan 05 S001: security and crash safety

Stage 1 of plan 05 (hub `05-review-remediation-cc-cr000-001.md`): no input file can hang a build, crash it, or make a whole file vanish from the graph.

- Status: ACTIVE
- Task: T32
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s1` from `autolisp`
- Findings: H4, E6, L1, L2, L4, N4

## 1. Design

| Finding | Fix |
|:--------|:----|
| H4, E6 | `graphify_lang/astgrep/extract.py` `_matches`: keep a `seen: set[int]` of `id(obj)` for dicts and lists, and return on a revisit. The work is then bounded by the number of distinct YAML nodes, and a self-referencing alias ends. Move the `_rule_doc` calls (`extract.py:205,251`) inside the per-document `try`, so a bad document keeps the file node, as the module docstring says. |
| L1 | `graphify_lang/autolisp/extract.py`: catch `RecursionError` from `_Walker.walk` in `extract_autolisp` and fall back to the regex path that `root.has_error` already uses (`extract.py:293-304`). No rewrite to an explicit stack: the fallback path exists and is tested. |
| L2 | `ecschema/extract.py:127-132` and `astgrep/extract.py:174-179`: replace the linear edge scan with an `_edge_keys` set, as `bmake/extract.py:119-125` does. Stage 3 moves all sinks into one shared sink, so this is a two-line change now and the shared sink keeps it. |
| L4 | `graphify_lang/manifest.py`: check that each TOML section is a `dict`, that `name` is a `str`, and lower-case `suffixes`, `augments`, `overrides` and `hook_suffixes`. A bad manifest returns a one-line error. It never raises. |
| N4 | `autolisp/extract.py:252,298,304,331` and `astgrep/extract.py:132`: compute line numbers with `bisect` over a list of newline offsets built once per file. |

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S1.1 | Tests first: `test_h4_alias_bomb_bounded` (the 377-byte, 6-level file from the review and a 9-level file; limit 1 s), `test_h4_self_alias_keeps_file_node`, `test_l1_deep_nesting_falls_back` (1200 nested lists), `test_l2_large_schema_linear` (20 000 properties; limit 2 s), `test_l4_bad_sections_never_raise` (`language = "x"`, non-string `name`, `.LSP` suffix). | All fail for the reason the review names. |
| S1.2 | H4 and E6 fix. | The H4 tests pass; the 27 llm-linter-tool rule counts in case_007 do not change. |
| S1.3 | L1, L2, N4 fixes. | Their tests pass; the AutoLISP corpus counts in case_004 and the ECSchema counts in case_007 do not change. |
| S1.4 | L4 fix (engine commit). | The L4 tests pass; all shipped manifests still load (`graphify lang list` shows 9 languages). |
| S1.5 | Stage close: full pytest, extractor-diff and baseline checks (hub §3); move H4, E6, L1, L2, L4, N4 to `cc-CR000.002.md`. | Hub §3 checks pass. |
