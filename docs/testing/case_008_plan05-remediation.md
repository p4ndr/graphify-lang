# Case 008 — plan 05 remediation, file-node ids and corpus counts

Plan: `docs/plans/05-review-remediation-cc-cr000-001.md`, stage 3
(`05-S003-shared-plugin-core.md`, cc-CR000.001 H2, M4).

**Date:** 2026-09-26
**Branch:** `rr-s3` (base `rr-s2` `8e3354c`)
**Instrument:** per corpus, `extract(files, cache_root=<fresh temp dir>, root=repo)`
over a `git archive HEAD` copy of the repo, files = `git ls-files` entries with
the plugin's suffixes (autolisp: `.lsp .mnl .dcl .md`; vba: `.bas .cls .frm`;
bmake: `.mki .mke`; astgrep: `.yml .yaml`; ecschema: `.xml`; cc-kb: `.md`;
cargo: `.toml`). Before = the `8e3354c` tree on `PYTHONPATH`; after = `rr-s3`.
Edges are compared id-free, as `(source_file, label, node_kind)` triples.
**Corpus HEADs:** autolisp-pvcase `90bc5d3`, autolithp `d5a2074`, autolithp02
`76ebb5b`, autolithp-snap-rework `73eab4c`, BentleyTools `83c526f`,
bentley-model-management `ddd0b65`, bim-chk `d7ba56f`, BentleyHelp `95b9a95`,
llm-linter-tool `4123a92`, bentley-pyplace `fa8100d`, claude-config `0ad8780`,
moxide `a234d74`, tmllm `1c950f3`.

## 1. File-node id form (M4)

A plugin file node was `_make_id(_file_stem(path))`: the path without its
suffix, minted from the path the extractor saw (absolute under `extract()`).
It is now `_make_id(str(path))`, suffix included, as the built-in extractors
mint it (`graphify_lang._common.Sink`), so upstream's id remap turns it into
the canonical root-relative stem before `_disambiguate_colliding_node_ids`
runs. Symbol ids are unchanged (`<stem>_<name>`).

| Case | Old file id | New file id |
|:--|:--|:--|
| No same-stem file anywhere | `src_pvc_app_main` | `src_pvc_app_main` (unchanged) |
| Same-stem plugin files `d/x.lsp`, `d/x.mnl`, `d/x.dcl` | `d_x_lsp_<scan root>_d_x` | `d_x_lsp_d_x` |
| Same-stem `d/x.mki`, `d/x.mke` | `d_x_mki_<scan root>_d_x` | `d_x_mki_d_x` |
| Same-stem `d/x.bas`, `d/x.cls`, `d/x.frm` | `d_x_bas_<scan root>_d_x` | `d_x_bas_d_x` |
| Plugin file beside a same-stem built-in file (`d/x.xml` + `d/x.py`, `app/x.lsp` + `app/x.md`) | `d_x` for both: one merged node | `d_x_xml_d_x`, `d_x_py_d_x` |

`<scan root>` is the absolute checkout path made an id
(`tmp_claude_1000_home_p4ndr_..._autolithp`), so the old form differed per
machine and per checkout path. `tests/lang/test_s3_shared_core.py::test_m4_file_ids_portable`
builds each plugin's same-stem fixture under two roots and requires identical,
unique, root-free ids.

## 2. Corpus counts, before / after

Nodes are list entries / distinct ids.

| Plugin | Repo | Files | Before nodes / ids / edges | After nodes / ids / edges | Ids renamed | Dangling before / after |
|:--|:--|--:|:--|:--|--:|:--|
| autolisp | autolisp-pvcase | 87 | 2280 / 2280 / 7757 | 2280 / 2280 / 7757 | 0 | 1 / 1 |
| autolisp | autolithp | 254 | 10691 / 10630 / 25522 | 10691 / 10691 / 25584 | 64 | 1 / 1 |
| autolisp | autolithp02 | 227 | 8241 / 8181 / 18153 | 8241 / 8241 / 18214 | 63 | 1 / 1 |
| autolisp | autolithp-snap-rework | 240 | 8035 / 7974 / 17296 | 8035 / 8035 / 17358 | 64 | 1 / 1 |
| vba | BentleyTools | 139 | 2541 / 2541 / 9984 | 2541 / 2541 / 9984 | 0 | 0 / 0 |
| vba | bentley-model-management | 57 | 1126 / 1126 / 3964 | 1126 / 1126 / 3964 | 0 | 0 / 0 |
| vba | bim-chk | 33 | 416 / 416 / 1114 | 416 / 416 / 1114 | 0 | 0 / 0 |
| bmake | BentleyHelp | 68 | 1736 / 1736 / 3897 | 1736 / 1736 / 3897 | 2 | 0 / 0 |
| astgrep | llm-linter-tool | 82 | 109 / 109 / 108 | 109 / 109 / 108 | 0 | 0 / 0 |
| ecschema | BentleyHelp | 76 | 15252 / 15252 / 22489 | 15252 / 15252 / 22489 | 0 | 0 / 0 |
| ecschema | bentley-pyplace | 22 | 7 / 7 / 8 | 7 / 7 / 8 | 0 | 0 / 0 |
| ecschema | claude-config | 14 | 0 / 0 / 0 | 0 / 0 / 0 | 0 | 0 / 0 |
| cc-kb | claude-config | 871 | 40164 / 40164 / 51198 | 40164 / 40164 / 51198 | 0 | 120 / 120 |
| cargo | moxide | 20 | 17 / 17 / 80 | 17 / 17 / 80 | 0 | 45 / 45 |
| cargo | tmllm | 4 | 1 / 1 / 14 | 1 / 1 / 14 | 0 | 14 / 14 |

Every edge relation count is unchanged except `sidecar_doc`, and every id-free
edge is kept, with these causes:

- **autolithp, autolithp02, autolithp-snap-rework:** 62 / 61 / 62 `.lsp` files
  have a same-stem `.md` sidecar (`build/make-bundle.lsp` + `make-bundle.md`).
  The resolver skipped every one ("same stem: one node id"); now each gets its
  `sidecar_doc` edge: 1 → 63 / 62 / 63. In 61 / 60 / 61 of the pairs the `.lsp`
  file node and the `.md` page node had one id and graphed as one node (ids <
  nodes); they are two nodes now, and the `contains` edges the merged node
  showed "from the `.md` page" come from the `.lsp` file node (same count). The
  other pair, `src/ui/manager.lsp`, also has `manager.dcl`: its `.lsp` and
  `.dcl` ids were salted with the scan root and now are not.
- **BentleyHelp bmake:** `PrecompileHeader.mki` + `PrecompileHeader.mke` lose
  the scan root from their ids.
- The dangling edges are upstream's (Markdown `references` to out-of-corpus
  files, cc-kb and cargo `depends_on` / link targets), identical before and
  after. The fixture tests cover the H2 case the corpus lacks: same-stem
  `.lsp` / `.mnl` defuns calling another file (`test_h2_same_stem_lsp_mnl_dcl`)
  and same-stem `.bas` / `.cls` procedures (`test_h2_vba_same_stem`), which
  dangled before.
