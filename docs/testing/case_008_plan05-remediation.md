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

## 3. Stage 4: clean-build counts after H3 (cargo, cc-kb)

**Branch:** `rr-s4` (base `rr-s3` `b6426db`); H3 commit `22855e9`.
**Instrument:** as §2 (`git archive HEAD` copy, fresh `cache_root`, `extract()`
over the plugin's files), run on `b6426db` (before) and `22855e9` (after).
cargo: every `Cargo.toml` outside `target/`. cc-kb on claude-config: the `.md`
files, and a second run with `.md` plus every `CODE_EXTENSIONS` file (so code
paths have targets). Edges compared id-free as in §2.

| Corpus | Files | Nodes | Edges | `has_member` | Workspaces | `external_deps` names | `depends_on` |
|:--|--:|--:|--:|--:|--:|--:|--:|
| moxide | 17 | 17 | 80 | 16 | 1 | 45 | 64 |
| oa-graph | 6 | 6 | 35 | 5 | 1 | 23 | 30 |
| oag-dev | 6 | 6 | 35 | 5 | 1 | 23 | 30 |
| tmllm | 1 | 1 | 14 | 0 | 0 | 14 | 14 |

| claude-config | Files | Nodes | Edges | `hub_spoke` | `cc_ref` | `code_ref` | `cc_id` docs | Dangling cc ids |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| `.md` only | 871 | 40164 | 51198 | 235 | 8995 | 1141 | 632 | 235 |
| `.md` + code | 1391 | 49106 | 71125 | 235 | 8995 | 3182 | 632 | 235 |

Before and after are equal in every cell, and every id-free edge is kept. The
89 differing edge keys per claude-config run are upstream's dangling Markdown
`references` whose target id carries the random scan-copy path, the same 89 in
both runs. The has_member counts equal plan 04 case 007 (moxide 16, oa-graph 5,
oag-dev 5) and `cargo metadata` `workspace_members`.

New node fields (attributes only; ids and edges unchanged): `cargo_ws_deps` on
a cargo workspace node, `bmake_includes` on a bmake file node that includes
something, `cc_kb_links` on a Markdown page node that links to another `.md`
file. They are declared as `[resolve] context_fields`, so an incremental build
keeps them on the context nodes of unchanged files (H1). `cc_kb_links` is set
in any repo, not only inside a harness root (cc-CR000.003 S4-N1): 36
non-harness pages / 47 KB on BentleyTools, 296 nodes / 28 KB on
claude-config, 0.1-0.2 % of `graph.json`; it reaches JSON and GraphML exports.

## 4. Stage 4: incremental parity (E5, H1)

`tests/lang/test_s4_build_coherence.py::test_e5_incremental_parity`: per fixture
tree, a clean `_rebuild_code(root)`, then for each plugin file in turn an
incremental `_rebuild_code(root, changed_paths=[f])`; node ids and
`(source, target, relation)` edges between graphed nodes must equal the clean
build.
Since the review fix (cc-CR000.003 S4-L2) the test runs on both hooked paths
(`_rebuild_code` and `graphify extract --code-only`, the latter without cc-kb
because `--code-only` skips `.md`), appends a byte to each file, and compares
whole node and edge dicts (minus `_origin`, `community`, `weight`) with a clean
build of the edited tree: 0 differing files on every tree and path.

| Fixture | Plugin files | Differing files before (`a5961fe`) | After (`cd55efb`) |
|:--|--:|--:|--:|
| autolisp `plan02` | 4 | 1 | 0 |
| autolisp `src` | 3 | 1 | 0 |
| vba | 5 | 4 | 0 |
| bmake | 4 | 2 | 0 |
| cargo | 5 | 0 | 0 |
| astgrep | 11 | 5 | 0 |
| ecschema | 7 | 2 | 0 |
| cc-kb | 10 | 8 | 0 |

Two upstream behaviours are outside the test, with or without plugins
(measured with `GRAPHIFY_LANG_DISABLE=1`): the incremental merge drops an
unchanged file's dangling edges (cargo `depends_on` to external crates), and
re-extracting one of a same-stem pair (`src/foo.cpp`, `src/foo.h`) alone
un-salts its id. The test compares only edges between graphed nodes and
touches only plugin files.

## 5. Stage 6: release rebuild (S6.5)

**Date:** 2026-09-26
**Build:** `graphify 0.9.68+lang.4` (pipx venv, wheel of tag `v0.9.68+lang.4`,
commit `ddefbc7` on `rr-fix`).
**Procedure:** one repo at a time by a logging script that stops on the first
failure: `cp graphify-out/graph.json graphify-out/graph.pre-plan05.json`,
`rm -rf graphify-out/cache/ast` (semantic caches kept), `graphify update <path>`,
then a second `graphify update <path>` with no change. Counts by the plan 04
S16 stats script (plugin rows by source-file suffix; `xfile` = edges whose ends
are in two files). Every update exited 0 with no traceback; the only warnings
are upstream's (zero-node `.yml` files, missing `tree_sitter_sql`, C++ syntax
errors), as in plan 04 S16.

| Repo | Before nodes / edges | After nodes / edges | 2nd update | Plugin rows after (nodes / edges / xfile) | New context fields after |
|:--|:--|:--|:--|:--|:--|
| bim-chk | 818 / 1598 | 818 / 1598 | same | vba 416 / 1114 / 319 | - |
| bentley-model-management | 1406 / 4282 | 1406 / 4286 | same | vba 1126 / 3961 / 1821 | - |
| BentleyTools | 36395 / 44499 | 36395 / 44521 | same | vba 2529 / 9954 / 4862; cites 452 | `cc_kb_links` 36 |
| BentleyHelp | 22230 / 36945 | 22231 / 36946 | same | bmake 729 / 2254 / 347; ecschema 15252 / 22457 / 1773 | `bmake_includes` 15 |
| bentley-pyplace | 3777 / 7475 | 3777 / 7475 | same | ecschema 7 / 8 / 0; cites 60 | `cc_kb_links` 1 |
| moxide | 6046 / 15075 | 6046 / 15075 | same | cargo 17 / 35 / 35; cites 29 | `cc_kb_links` 1, `cargo_ws_deps` 1 |
| oa-graph | 2434 / 3977 | 2434 / 3977 | same | cargo 6 / 12 / 12; cites 2 | `cc_kb_links` 4, `cargo_ws_deps` 1 |
| oag-dev | 2587 / 4096 | 2587 / 4096 | same | cargo 6 / 12 / 12 | `cc_kb_links` 3, `cargo_ws_deps` 1 |
| tmllm | 4623 / 11629 | 4623 / 11629 | same | cargo 1 / 0 / 0 | - |
| llm-linter-tool | 1662 / 2882 | 1662 / 2882 | same | astgrep 82 / 81 / 54; cites 16 | - |
| claude-config | 47568 / 64638 | 47568 / 64638 | same | cites 12104; cargo 4 / 6 / 6 | `cc_kb_links` 296, `cargo_ws_deps` 1 |
| `~/.claude` | 18260 / 33774 | 18326 / 33834 | same | cites 10594; cargo 4 / 6 / 6 | `cc_kb_links` 200, `cargo_ws_deps` 1 |

"Before" equals the plan 04 S16 "after" count in every repo except `~/.claude`
(its tree changed since). Differences, each traced by an id-level diff of
`graph.pre-plan05.json` against `graph.json`:

- **bentley-model-management +4, BentleyTools +22 edges:** VBA `calls`
  self-loops of recursive procedures (`Loader.ResolveDependencies`,
  `PathUtils.CollectFiles`, ...; 21 `.bas` + 1 `.frm`). S3-X1 (`9541fcb`)
  keeps a recursive call as a self-loop, as upstream's built-ins do. No edge
  lost.
- **BentleyHelp +1 node, +1 edge:** M4. `PyGeomTest.mke` and `pygeomtest.cpp`
  (same folded stem) were one node; they are two now (`..._pygeomtest_mke_...`,
  `..._pygeomtest_cpp_...`). The 33 `contains` edges to the makefile's macros
  and targets now come from the `.mke` file node, so they are no longer
  cross-file (bmake xfile 379 -> 347); the `.cpp` node keeps its own
  `contains` and `imports`. One semantic node without `_origin` (id
  `mspython`) now carries `_origin: semantic`; its edges are unchanged. The
  `PrecompileHeader` pair renamed at `extract()` level in §2 shows no id
  change in the graph.
- **`~/.claude` +66 nodes, +60 edges:** Markdown headings and `contains` edges
  of files added or rewritten since plan 04 S16 (six `skills/synced/...` skill
  files, the regenerated `cc-LR000.001` sidecars). `cites` unchanged.
- **The new node fields** (`cc_kb_links`, `cargo_ws_deps`, `bmake_includes`,
  stage 4) appear in 8 graphs; attributes only.
- Plugin edge counts otherwise equal plan 04 S16 in every repo; semantic node
  counts are unchanged in every repo (BentleyHelp +1 is the `_origin` stamp
  above).

### Incremental check (E5 on real corpora)

Instrument: two `git archive HEAD` copies per repo; clean
`watch._rebuild_code` on copy A; append `\n` to the K plugin files with the
most cross-file edges in both copies; incremental
`_rebuild_code(A, changed_paths=<those files>)`; clean build of copy B; node
and edge dicts compared minus `_origin`, `community`, `weight`, edges between
graphed nodes (the `test_e5_incremental_parity` comparison).

| Corpus | Files changed | Clean before (n / e / plugin xfile) | Incremental | Clean of edited tree | Differences |
|:--|:--|:--|:--|:--|:--|
| bim-chk | 6 `.bas` | 818 / 1598 / 319 | 818 / 1598 / 319 | 818 / 1598 / 319 | none |
| BentleyHelp | 8 ecschema `.xml`, 1 `.mke` | 22505 / 37343 / 2172 | 22505 / 37342 / 2171 | 22505 / 37343 / 2172 | 1 bmake edge lost; 11 upstream Python edges retargeted |

- **bim-chk:** every cross-file VBA edge survives.
- **BentleyHelp, upstream:** 11 `imports_from` edges from unchanged `.py`
  test files point to an `ambiguous_python_import_<hash>` stub whose hash
  differs between the incremental and the clean build (22 node differences =
  the 11 + 11 stubs). No plugin file or plugin node is involved.
- **BentleyHelp, fork: H1 is not closed for duplicate basenames.** The
  incremental build drops `PyDgnPlatform.mke` target `$(o)valueformat$(oext)`
  `depends_on` `PyDgnPlatform/source/valueformat.cpp` (INFERRED). Cause:
  upstream relabels file nodes whose basename collides
  (`graphify.build._file_label_reassignments`, #2032), so the persisted label
  of both `valueformat.cpp` nodes is a path suffix (`PyDgnPlatform/source/valueformat.cpp`).
  In a clean build the resolver runs before the relabel and sees
  `valueformat.cpp`; in an incremental build the context nodes carry the
  persisted label, and `graphify_lang/bmake/resolve.py` indexes file nodes by
  `label == Path(source_file).name`, so neither candidate is indexed and the
  edge is dropped. `graphify_lang/cc_kb/resolve.py` has the same test.
  Minimal repros (installed `0.9.68+lang.4`): two `source/vf.cpp` files and one
  `.mke` depending on its own -> the edge is gone after
  `_rebuild_code(changed_paths=[A/A.mke])`; `skills/x/SKILL.md` and
  `skills/y/SKILL.md` with a `docs/cc-AA000.000.md` citing the first -> its
  `cites` edge is gone after the doc changes. Full `graphify update` (no
  `changed_paths`) is not affected, so the 12 graphs above are complete; the
  git-hook and `graphify watch` incremental paths drop such edges until the
  next full update. Proposed fix (not in `lang.4`): index file nodes with
  upstream's `graphify.build._is_file_node_label(label, source_file)`, and
  add a same-basename pair to the bmake and cc-kb E5 parity fixtures.

Rollback per repo: `cp graphify-out/graph.pre-plan05.json graphify-out/graph.json`.
