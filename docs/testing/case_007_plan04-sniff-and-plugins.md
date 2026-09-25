# Case 007 — plan 04 sniff router and plugins, corpus counts

Plan: `docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md`.
One section per plugin; S14 (KB augment value test) adds its own section.

## vba (S8, T29.1)

**Date:** 2026-09-25
**Branch:** `lang-vba` at `6486c9b` (off `lang-rules` `91f26cd`)
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; plugin `graphify_lang/vba`, no grammar)
**Corpus HEADs:** BentleyTools `83c526f`, bentley-model-management `ddd0b65`, bim-chk `d7ba56f`
**Instrument:** per repo, `extract(files, cache_root=<fresh temp dir>, root=repo)` over `git ls-files`
entries ending `.bas` / `.cls` / `.frm` (`.frx` not extracted); truth = lines matching
`^\s*(public |private |friend )?(static )?(sub|function|property (get|let|set)) ` (case-insensitive),
summed over the same files, each decoded as Windows-1252.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6086 passed, 14 skipped.

### Start point (plan 04 §1)

| File | `extract_apex` nodes / edges | Fork (`sniff_router[.cls]` → `extract_vba`) nodes / edges |
|:--|--:|--:|
| bim-chk `src/document/ThisWorkbook.cls` | 1 / 0 | 8 / 8 (file, class, 6 procedures; 7 contains, 1 calls) |

### Procedure counts against grep

| Repo | Files .bas / .cls / .frm | .cls routed to vba | Sub + Function + Property nodes | grep truth | Difference |
|:--|:--:|--:|--:|--:|--:|
| BentleyTools | 121 / 5 / 13 | 5 / 5 | 1166 + 1006 + 64 = 2236 | 2236 | 0 |
| bentley-model-management | 42 / 7 / 8 | 7 / 7 | 474 + 447 + 74 = 995 | 995 | 0 |
| bim-chk | 11 / 18 / 4 | 18 / 18 | 201 + 135 + 11 = 347 | 347 | 0 |

Per-file comparison: no file differs. Two BentleyTools `.bas` files have no
`Attribute VB_Name` header (`build/remap-levels.bas`,
`src/modules/BtDumpModels/DumpModels.bas`); `.bas` is not sniffed, so both are
extracted (module label = file stem).

### Other nodes and edges

| Repo | module / class / form | declare / type / enum | contains | calls EXTRACTED / INFERRED | uses | implements |
|:--|:--:|:--:|--:|:--:|--:|--:|
| BentleyTools | 121 / 5 / 13 | 15 / 8 / 4 | 2402 | 7518 / 6 | 106 | 0 |
| bentley-model-management | 42 / 7 / 8 | 7 / 5 / 5 | 1069 | 2804 / 0 | 148 | 0 |
| bim-chk | 11 / 18 / 4 | 0 / 0 / 3 | 383 | 719 / 8 | 5 | 0 |

No corpus file uses `Implements`; the edge is pinned by `tests/lang/test_vba.py`.
INFERRED calls: several same-named public procedures, the one sharing the
longest directory prefix with the caller wins (the AutoLISP resolver rule).
A 24-edge hand check of cross-module calls (12 BentleyTools, 12 bim-chk,
random sample) found every target correct.

### Known limits

- A user procedure named like a VBA-library routine (`Reset` in
  bentley-model-management, a public `.bas` Sub) is not reached by an
  unqualified call from another module: the builtins filter drops the name
  before the resolver. `Module.Reset` still resolves.
- `obj.Method` resolves only when `obj` is declared `As <Class>` in the
  procedure, its parameters or the module; `Variant` / `Object` receivers and
  `With` blocks give no edge.
- The form → code-behind relation is the `contains` edge from the form node to
  its procedures: a `.frm` holds both the designer and the code, so there is no
  second node to link.

## bmake (S9, T29.2)

**Date:** 2026-09-25
**Branch:** `lang-bmake` at `6a67e36` (off `lang-vba` `241d085`)
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; plugin `graphify_lang/bmake`, no grammar)
**Corpus HEAD:** BentleyHelp `95b9a95` (68 files: 52 `.mki`, 16 `.mke`)
**Instrument:** `extract(files, cache_root=<fresh temp dir>, root=repo)` over `git ls-files`
entries ending `.mki` / `.mke` plus `*.cpp` / `*.h` / `*.c` / `*.r` / `*.py` (so dependency
targets have file nodes); per-directive refs from `extract_bmake(Path(...))`; truth =
`grep -c '%include'` summed over the same 68 files.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6096 passed, 14 skipped.

### `%include` against grep

| Count | Value |
|:--|--:|
| `grep -c '%include'` (all lines) | 206 |
| lines where `%include` sits in a `#` comment | 7 |
| `%include` directives (`^\s*%include`) = extractor include refs | 199 |
| resolved to a file in the repo → `imports` edges | 135 directives → 113 edges |
| unresolved → kept on the file node as `unresolved_includes` | 64 |

135 + 64 = 199: every directive is an edge or an attribute entry. 135 directives
give 113 edges because a file that includes the same file in several `%if`
branches gets one edge. Of the 64 unresolved: 46 name a literal `.mki` that is
not in the repo (BentleyHelp holds a subset of the SDK `PublicSDK` folder:
`gccmdl.mki`, `llvmlink.mki`, `ApplyToolSet_VS2022.mki` ...), 18 are computed
from a macro defined in another file or the environment (`$(PolicyFile)` in
`ConfigurePolicy.mki`, `$(RedoCppMakefile)`, `$(COMPENVMKI_DIR)$(compenvMKI)`).
7 paths were expanded through a same-file macro; 1 of those resolved
(INFERRED). The 7 comment lines: `#%include common.mki`, `#  %include
%(BuildContext)ToolContextLink.mki`, and 5 prose comments ("the %includer",
"%included by").

### Nodes and edges

| file / macro / target nodes | contains | imports EXTRACTED / INFERRED | depends_on EXTRACTED / INFERRED | references EXTRACTED / INFERRED |
|:--:|--:|:--:|:--:|:--:|
| 68 / 1161 / 507 | 1668 | 112 / 1 | 334 / 3 | 2109 / 7 |

`depends_on`: 339 dependency tokens with a literal file name (338 `.cpp`, 1
`.c`) → 337 edges, all to `.cpp` files. `compenv.c` is not in the repo;
`valueformat.cpp` and `pydgnview.cpp` exist twice, 3 picks by longest shared
directory prefix (INFERRED), 1 tie dropped. `.r` resources are not graphed, so
a `.r` dependency gives no edge. No edge in the run dangles.

### Known limits

- A `%include` path that ends in a macro is expanded only through a definition
  in the same file above the directive; a macro set by the includer (the
  `PolicyFile` / `SolutionPolicyMki` pattern) stays unresolved.
- A macro use resolves to a definition in its own file, else to one on its
  include chain (files it includes, or that include it, transitively);
  siblings are out of scope. Several definitions: longest shared directory
  prefix, INFERRED; a tie is dropped. `%if` branches are not evaluated, so the
  first definition in a file is its node.
- `x.mki` and `x.mke` in one directory share a file stem
  (`build/PublicSDK/PreCompileHeader`). Upstream salts the two file ids apart
  (with the path) before the language resolvers run; the resolver reads each
  ref's source id back from the node, so the edges follow the salted ids.

## cargo (S10, T29.3)

**Date:** 2026-09-25
**Branch:** `lang-cargo` (off `lang-bmake` `483d6ae`); engine hook `d3d052d`, plugin `1e8244c`
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; augment `graphify_lang/cargo`, kind `augment` on `.toml`, `[match]` filename `Cargo.toml`)
**Corpus HEADs:** moxide `a234d74`, oa-graph `c36fa1c`, oag-dev `6aff8c3`, tmllm `1c950f3`, llm-linter-tool `4123a92`, comment-sidecar `dd93c0d`
**Instrument:** per repo, `_get_extractor(Path(...))(Path(...))` on each `Cargo.toml` outside `target/`, compared with `extract_package_manifest(Path(...))`; truth = `cargo metadata --no-deps --offline --format-version 1` `workspace_members` (cargo 1.97.1), run in the workspace root.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6102 passed, 14 skipped.

### Start point (D9)

`_get_extractor` sends `Cargo.toml` to `extract_package_manifest` by file name,
before `_DISPATCH`. Measured on the corpus before the augment:

| Manifest | Nodes | Edges |
|:--|:--|:--|
| virtual workspace root (`moxide/Cargo.toml`, `oa-graph/engine/Cargo.toml`) | 0 | 0 |
| member crate (`moxide/crates/mox_core/Cargo.toml`) | 1 (`pkg_mox_core`, `type=package`) | 16 `depends_on` to `pkg_<dep key>` (runtime deps only) |

A path or workspace dependency on a sibling crate already lands on that
crate's `pkg_` node (ids are keyed by name). External crates get an edge that
the build prunes, so they disappear. No workspace node, no member edges.

### Workspace members against cargo

| Repo | Cargo.toml files | `has_member` edges | cargo `workspace_members` | Equal |
|:--|--:|--:|--:|:--|
| moxide | 17 | 16 | 16 | yes |
| oa-graph (`engine/`) | 6 | 5 | 5 | yes |
| oag-dev (`engine/`) | 6 | 5 | 5 | yes |
| tmllm | 1 | 0 | 1 | no workspace: see below |
| llm-linter-tool | 1 | 0 | 1 | no workspace: see below |
| comment-sidecar | 0 | - | - | no `Cargo.toml` (Python repo) |

tmllm and llm-linter-tool have no `[workspace]` table; cargo reports the root
package as the one member of an implicit workspace. The augment adds a
workspace node only for a `[workspace]` table, so these two get none.

### Other additions

| Addition | Count |
|:--|--:|
| workspace nodes (`cargo_workspace_<dir>`) | 3 |
| crate nodes with `external_deps` / names listed: moxide | 45 names |
| oa-graph / oag-dev | 23 / 23 names |
| tmllm / llm-linter-tool | 14 / 17 names |
| `depends_on` edges for a path dep renamed with `package =` | 0 (none in the corpus; fixture pinned) |

On every corpus `Cargo.toml` the base nodes (minus the new `external_deps`
key) and base edges are unchanged. `pyproject.toml`: 3 files under `~/repos`,
`_get_extractor` returns `extract_package_manifest` itself and the JSON is
byte-identical. In a full `extract()` over moxide's 17 manifests, all 16
`has_member` targets are nodes.

### Known limits

- The workspace node id is `cargo_workspace_<dir name>`: two workspaces with
  the same directory name in one graph share a node.
- Dev- and build-dependencies stay out, as in core (runtime scope).

## astgrep (S11, T29.4)

**Date:** 2026-09-25
**Branch:** `lang-astgrep` (off `lang-cargo` `70bcfae`); plugin `680ce58`, tests `9c6be53`
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; plugin `graphify_lang/astgrep`, suffixes `.yml` `.yaml`, `[match]` + sniff; PyYAML 6.0.3 in `.venv`)
**Corpus HEAD:** llm-linter-tool `4123a92`
**Instrument:** `classify_file(Path(...))` on each `git ls-files '*.yml' '*.yaml'` path; `extract(files, cache_root=..., root=CORPUS)` on the 82 corpus files; the same classification with `GRAPHIFY_LANG_DISABLE=1` as the upstream reference.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6113 passed, 14 skipped.

### Classification (D3)

| Scope | `.yml`/`.yaml` files | document (upstream) | code (fork) | document (fork) |
|:--|--:|--:|--:|--:|
| llm-linter-tool | 82 | 82 | 82 | 0 |
| every git repo under `~/repos` | 100 | 100 | 82 | 18 |
| `.github/workflows/*.yml` under `~/repos` | 7 | 7 | 0 | 7 |

The only files whose class changed are the 82 in llm-linter-tool
(`sgconfig.yml`, 27 rules, 27 tests, 27 snapshots). `utils/` is empty there.

### Corpus counts

| Check | Measured | Truth | Equal |
|:--|--:|--:|:--|
| rule nodes | 27 | `rules/**/*.yml` files with `^id:`: 27 | yes |
| `tested_by` edges per rule with a test | 1 (all 27) | 27 test files, one per rule id | yes |
| `has_snapshot` edges | 27 | 27 snapshot files | yes |
| `loads` edges (sgconfig -> rule files) | 27 | 27 files under `ruleDirs: [rules]` | yes |
| `references` edges (`matches:`) | 0 | `matches:` in corpus: 0 | yes |

All resolver edges are EXTRACTED (one candidate per id). Local and global
util references, multi-document files and malformed YAML are covered by the
fixture only (`tests/lang/test_astgrep.py`).

### Known limits

- The globs use ast-grep's default directory names (`rules`, `rule-tests`,
  `utils`). A project that names other `ruleDirs` / `testDir` / `utilDirs`
  in `sgconfig.yml` is not claimed there.
- PyYAML is not a graphify dependency and is absent from the pipx runtime.
  There the flat fallback parses top-level keys only and finds `matches:` by
  a line regex, so a local util's references are credited to its rule.
- A file whose YAML does not parse keeps its file node with no
  `astgrep_role`, so it gets no `loads` edge.
- `.yml` is not in `hook_suffixes`: editing a rule does not trigger the git
  hook rebuild.
