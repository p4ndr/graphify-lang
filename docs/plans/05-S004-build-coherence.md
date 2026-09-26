# Plan 05 S004: build coherence

Stage 4 of plan 05: an incremental build, a cached build and a clean build give the same graph.

- Status: DONE (2026-09-26, `rr-s4` `a5961fe`..HEAD)
- Task: T35
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s4` from `rr-s3`
- Findings: H1, E3, E5, H3, L9, L11, M2, E1

## 1. Design

- **E5: parity test first.** `tests/lang/test_parity.py`: for each plugin fixture tree, compare a clean `extract` + build with a clean build followed by `graphify.watch._rebuild_code(root, changed_paths=[one file])`. The node ids and the `(source, target, relation)` edge set must be equal. It fails today because of H1 (the review measured this).
- **H1, E3 (hub D2).** The context nodes that `graphify/watch.py:1723-1729` builds for unchanged files do not carry `node_kind` or the other plugin fields.
  - Fork fix: a try-wrapped registry lookup after the `ctx_node` dict is built copies the extra fields that the registry reports (`graphify.lang_registry.context_fields()`, the union of each manifest's new optional `[resolve] context_fields` list, default `["node_kind"]`).
  - Upstream PR draft, written in S006: forward a registrable field list from `watch.py`.
  - The upstream `graphify/extract.py` context path (if any) gets the same lookup; confirm by a read before editing.
- **H3, L9.** Augments become pure functions of the file bytes. The cargo augment emits its raw payload (member globs and `exclude` relative to the manifest folder, renamed and workspace dependencies by key) and does no filesystem reads. A new cargo resolver matches that payload against the graphed `pkg_*` nodes by their `source_file` folder. The cc-kb augment emits every path-like code span and every `cc-*` id. The cc-kb resolver resolves them against graphed file nodes and does the `docs/` root check (moved from `_is_root`). The resolver sees only graphed nodes, so nothing outside the scan root is read (L9).
- **L11.** `astgrep/resolve.py:80-83`: apply `posixpath.normpath` to both sides before `is_relative_to`.
- **M2, E1.** In `graphify/lang_registry.py` `_apply_registry`: compute a fingerprint of the active plugin set (the sorted manifest names, the plugin distribution version, and a hash of each plugin package's `.py` and `.toml` files). Append it to `graphify.cache._EXTRACTOR_VERSION` at run time, with no source edit to `cache.py`. `GRAPHIFY_LANG_DISABLE=1` therefore gets its own cache namespace, and a plugin code change clears only plugin-affected entries without a `+lang.N` bump. This supersedes the "bump +lang.N" workaround in ltm learning 1484; update that learning.

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S4.1 | E5 parity test, plus `test_h3_new_member_crate_appears`, `test_h3_new_code_ref_target_appears`, `test_l9_outer_workspace_ignored`, `test_l11_dotdot_ruledirs`, `test_m2_disable_toggle_uses_own_cache`. | The parity test fails on at least autolisp, vba and cc-kb (H1); the others fail for their reasons. |
| S4.2 | H1 fork hook (a core registry-lookup commit) and the `[resolve] context_fields` manifest key. | The parity test passes for every plugin. |
| S4.3 | H3 and L9: cargo resolver; cc-kb resolver takes the `docs/` root and code-path checks. | The H3 and L9 tests pass; the case_007 cargo counts (moxide 16, oa-graph 5, oag-dev 5) and the cc-kb counts do not change on a clean build. |
| S4.4 | L11. | Its test passes. |
| S4.5 | M2 and E1 fingerprint (engine commit). Update ltm learning 1484. | `test_m2_*` passes; two builds with the same plugin set share the cache (the second build is served from cache). |
| S4.6 | Stage close (hub §3); move the findings to `cc-CR000.002.md` (E3 stays open until its PR draft is written in S006). | Hub §3 checks pass. |

## 3. Result

| Step | Result | Commits |
|:-----|:-------|:--------|
| S4.1 | 13 red tests, strict xfail with `raises=AssertionError`: E5 parity on 7 of 8 fixture trees (cargo already equal), H3 x2 (no `pkg_b` member from a cached root manifest; no `cites` to a script added after its doc), L9 (outer workspace's renamed dep leaks in), L11 (no `loads` for `../shared/rules`), M2 (a disabled run poisons the enabled one), E1 (pre-stage-3 entries served; the resolver fails on `'node'`). | `a5961fe` |
| S4.2 | Engine: `[resolve] context_fields` manifest key (default `["node_kind"]`), `graphify.lang_registry.context_fields()`, try-wrapped lookups in `watch._rebuild_code` and the `graphify extract` incremental path (`cli.py`), which also add `_lang_source_file` (absolute path). Plugins declare their fields; resolvers compare paths through `_common.source_of`; bmake gets `bmake_includes`, cc-kb `cc_kb_links`. Parity: 0 differing files on all 8 trees (was 23 of 49 plugin files). | `2adf7bc`, `cd55efb` |
| S4.3 | cargo and cc-kb augments read only their own file; new cargo resolver; cc-kb resolver chooses the harness root among graphed docs. H3, L9 tests pass. Clean-build counts unchanged: has_member 16 / 5 / 5, external_deps 45 / 23 / 23; claude-config hub_spoke 235, cc_ref 8995, code_ref 3182, cc_id 632 (case 008 §3). | `22855e9` |
| S4.4 | L11 `os.path.normpath` on both sides; test passes. | `dc8a8ec` |
| S4.5 | `-lang<fingerprint>` appended to `graphify.cache._EXTRACTOR_VERSION` in `_apply_registry` (enabled `...-lang132611af4a75`, disabled `...-lang22ec7175d162` on this tree). M2, E1 tests pass; two builds with one plugin set share entries. ltm learning 1484 (and repo 1480) superseded by global learning 1490 (learnings have no update path). | `2e2cba1` |
| S4.6 | `pytest tests/ -q`: 6195 passed, 14 skipped (baseline 6178 / 14; +16 in `test_s4_build_coherence.py`, +1 cargo pipeline test). `git diff upstream/v8...HEAD -- graphify/extractors/` empty; `tests/lang_baseline.txt`, `tests/upstream_tables.json`, `tests/test_watch.py` unchanged. H1, H3, M2, L9, L11, E1, E5 moved to `cc-CR000.002.md`; E3 stays open (PR draft in S006). | this commit |

Deviations from §1:

- **H1 needs more than `node_kind`.** Context nodes carry the root-relative `source_file`, fresh nodes the absolute one, so the hook also adds `_lang_source_file`; and an unchanged file's refs and non-structural edges never reach the resolver, so bmake's include graph (`bmake_includes`) and cc-kb's link-joined pairs (`cc_kb_links`) are now node fields.
- **`cli.py` too.** The `graphify extract` incremental path builds context nodes the same way as `watch.py`; it gets the same lookup.
- **E5 scope.** The parity test touches only plugin files and compares edges between graphed nodes; the two upstream behaviours it excludes are in case 008 §4.
- **cc-kb payload on every `.md`.** A pure augment cannot know whether a file is in a harness root, so any `.md` with a mention or a path-like span carries a `cc_kb_refs` payload; the resolver drops files with no graphed root. Out-of-scope files keep base nodes and edges.
- **Known limit.** An incremental build re-resolves only the changed files' payloads: a crate added under an unchanged workspace manifest gets its `has_member` edge on the next full or cached build, not on the incremental one (the edge belongs to the root manifest).
- **Parity test file** (cc-CR000.003 S4-N3). §1 names `tests/lang/test_parity.py`; the test landed as `tests/lang/test_s4_build_coherence.py::test_e5_incremental_parity`.
- **`cc_kb_links` outside harness roots** (S4-N1). The field is set on every Markdown page that links to an existing `.md` file, in any repo (BentleyTools: 36 non-harness pages, 47 KB), and reaches JSON and GraphML exports. It is needed for pair suppression when such a page is a cite target; out-of-scope pages keep base nodes and edges plus this one attribute.
- **Fingerprint scope** (S4-L4, review-fix `d21f7b2`). The M2/E1 fingerprint covers plugin code and, since the review fix, `graphify/lang_registry.py`; "without a `+lang.N` bump" holds for those only. Other fork edits under `graphify/` still need a version change. Learning 1490 is superseded by 1498.

