# Plan 05 S003: shared plugin core

Stage 3 of plan 05: one shared module carries the id, sink and resolver contracts that the five plugins now copy, so H2 and M4 are fixed in one place.

- Status: ACTIVE
- Task: T34
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s3` from `rr-s2`
- Findings: E2, L5, H2, M4, M6, E7, L3, E8, N3, L12

## 1. Design

- **E2, L5: `graphify_lang/_common.py`.** It holds:
  - the lazy `_make_id` / `_file_stem` helpers;
  - one `Sink` class with an `_edge_keys` set (from S001 L2), nodes and edges;
  - index-based refs: each ref stores `node` (an index into the result's `nodes`), and `resolve_ref_id(res, ref)` reads the current id back (the bmake pattern, ltm learning 1477);
  - `pick_by_prefix` (the `_pick` + `shared` copies);
  - `load_manifest(pkg, toml, **fields)` (the 7 `_get_manifest` copies).

  autolisp, vba, bmake, ecschema, astgrep and cc_kb move to it. Each plugin keeps only its language logic.
- **H2.** Because of the shared refs, autolisp and vba resolve through the node index. `dialogs_of` is keyed by the current id. The wrong comment at `autolisp/resolve.py:79-80` is deleted.
- **M4.** The file-node id is `_make_id(str(path))`, with the suffix included, as the built-in extractors make it. Upstream's portable-id remap then applies. Symbol ids stay stem-based. `app.lsp`, `app.mnl` and `app.dcl` no longer collide at file level, and no absolute path gets into an id.
- **M6, E7 (hub D1).** The shared `Sink` and the builtins filter come from the rules engine (`rules.py`, `builtins.py`), so the engine has users. `rules.py` `post_file` accepts only a `graphify_lang.` module prefix and rejects any other import string with a manifest error. E7 is closed as "rejected per D-008". `test_rules.py` stays and gains a test for the rejected import.
- **L3, E8.** `cc_kb/resolve.py:80` uses the `node` dict it already has, not a linear search. `cc_kb/augment.py` `_is_root` gets `functools.lru_cache`. Stage 4 (H3) moves the `docs/` scan into the resolver, and the cache goes with it.
- **N3.** Unread manifest keys (`type`, `grammar.kind`, `language_fn`, `version`, `case_insensitive`, `builtins_file`, `builtins_prefixes`): `builtins_file` and `builtins_prefixes` are now READ by the shared builtins filter, which removes the copy in `autolisp/extract.py:31-32`. `case_insensitive` is read by the shared sink. The other keys are deleted from the shipped manifests and from the templates.
- **L12.** Correct the stale comments and docstrings at `astgrep/extract.py:18-20,32`, `manifest.py:86,219,223`, `autolisp/resolve.py:79` and `registry.py:1`. PyYAML is now a runtime dependency (`pyproject.toml:45`), so the flat YAML parser in `astgrep/extract.py:55-99` and the `_yaml is None` branches are deleted.

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S3.1 | Tests first: `test_h2_same_stem_lsp_mnl_dcl` (`x.lsp` + `x.mnl` + `x.dcl` with cross-file calls and a sidecar), `test_h2_vba_same_stem`, `test_m4_file_ids_portable` (build in two different tmp roots, compare ids), `test_m6_post_file_prefix_only`. | They fail for the reason the review names. |
| S3.2 | Add `_common.py` and move bmake to it first (it already has the index pattern). | bmake tests and the case_007 bmake counts do not change. |
| S3.3 | Move ecschema, astgrep, vba, autolisp and cc_kb, one commit each. | Each plugin's tests pass after its commit; its case_004 or case_007 counts do not change, except the file-node ids (M4). |
| S3.4 | H2 and M4 are complete when S3.3 is done. | The S3.1 tests pass. Write the old-to-new file id form in `docs/testing/case_008_plan05-remediation.md` (new file). |
| S3.5 | M6, N3, L3, E8, L12. | `graphify lang list` still shows 9 languages; no manifest key remains that nothing reads (a test loads every shipped manifest and checks each key against a list of the keys that are read). |
| S3.6 | Stage close (hub §3); move the findings to `cc-CR000.002.md`; record E7 as closed per D1. | Hub §3 checks pass. |
