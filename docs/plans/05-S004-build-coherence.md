# Plan 05 S004: build coherence

Stage 4 of plan 05: an incremental build, a cached build and a clean build give the same graph.

- Status: ACTIVE
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
