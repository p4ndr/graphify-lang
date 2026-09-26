# Code review: graphify-lang fork layer

Open findings only. Fixed and closed findings move to `cc-CR000.002.md` (plan 05 stage 1 moved H4, E6, L1, L2, L4, N4, stage 2 moved M7, M8, M9, M10, N6, E9, stage 3 moved H2, M4, M6, L3, L5, L12, N3, E2, E7, E8, stage 4 moved H1, H3, M2, L9, L11, E1, E5, stage 5 moved M1, M3, M5, L6, L7, L8, L10, L13, N5, E4, and stage 6 moved M11, M12, N1, N2, E3 on 2026-09-26).

| Severity | Count |
|:---------|------:|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Nit | 0 |
| **Defects total** | **0** |
| Enhancements | 0 |

- **Date**: 2026-09-26
- **Mode**: Diff (`git diff upstream/v8...autolisp`), branch `autolisp`, HEAD `013c902` (v0.9.67+lang.3)
- **Scope**: `graphify/lang_registry.py`; the registry-lookup blocks in `graphify/detect.py`, `extract.py`, `cli.py`; `graphify/resolver_registry.py`; `graphify_lang/**` (registry, manifest, rules engine, templates, plugins autolisp, vba, bmake, cargo, astgrep, ecschema, cc_kb); fork tests and fixtures; `pyproject.toml`; `.github/workflows/*`; fork docs. Upstream code only where the fork depends on it.
- **Focus**: Comprehensive
- **Verification**: `pytest tests/ -q` = 6141 passed, 14 skipped (86 s); fork tests alone 172 passed, 0 skipped on this host. Every High and most Medium findings were reproduced with a probe in the repo `.venv` (probe named in the finding). No source file was modified.
- **Repo rules respected in every fix**: no edit to existing extractors, `engine.py`, `resolution.py` or upstream tests; core tables change only through registry lookups. A fix that needs a core change is marked **upstream PR**.

## High

None open.

## Medium

None open.

## Low

None open.

## Nit

None open.


## Architectural findings

- **Resolver id contract**: three of five resolvers learned to read ids back through the node index (bmake, ecschema, astgrep), two did not (H2). The contract belongs in one shared sink (E2), not in each plugin. — Impact: STRONG. Done in plan 05 S3 (`graphify_lang/_common.py`, cc-CR000.002 H2, E2).
- **Purity contract with the AST cache**: extractors and augments must be functions of the file bytes; everything that looks at other files belongs in the resolver (H3, M2). Write it into `README.md` 'Proposed architecture' as a plugin rule. — Impact: STRONG. Done in plan 05 S6.2: `README.md` 'Plugin contract' (`acdac5f` on `rr-s6`).
- **Upstream seams the fork depends on**: `_disambiguate_colliding_node_ids` ordering, `watch.py` context-node fields (H1), `_reconcile_markdown_links` pruning only `references` (cc-kb relies on `cites` surviving, `cc_kb/resolve.py:30-33`), dict identity between `per_file` and `all_nodes` (bmake/astgrep/cc-kb index reads), `_get_extractor` suffix fallback. Each is untested from the fork side; an upstream refactor breaks them silently. A parity test (E5) covers most. — Impact: AVERAGE. Listed in `README.md` 'Upstream seams the fork depends on' (plan 05 S6.2); the `watch.py` context-node, claimed-path and resolver case-fold seams have upstream PR drafts in `docs/upstream/` (S6.3).

## Enhancements

None open.


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
