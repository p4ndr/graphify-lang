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
- Fixed on `lang-cc-kb` (`271a06c`, `6503e04`): `.yml` and `.yaml` are in
  `hook_suffixes`, so editing a rule triggers the git hook rebuild. Any other
  `.yml` edit triggers it too (owner, 2026-09-25).

## ecschema (S12, T29.5)

**Date:** 2026-09-25
**Branch:** `lang-ecschema` (off `lang-astgrep` `f6b6cc9`); engine `a6bdbb9`, plugin `2d07933`, tests `2632d4f`
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; plugin `graphify_lang/ecschema`, suffix `.xml`, `[match]` `*.xml` + sniff on a root `<ECSchema`; stdlib expat)
**Corpus HEAD:** BentleyHelp `95b9a95`, bentley-pyplace `fa8100d`, claude-config `0ad8780`
**Instrument:** `classify_file(Path(...))` on each `git ls-files '*.xml' '*.xsd'` path of every git repo under `~/repos` plus `~/.claude`, with and without `GRAPHIFY_LANG_DISABLE=1`; `extract(files, cache_root=..., root=CORPUS)` on the claimed files.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6126 passed, 14 skipped.

### Engine change

7 of the BentleyHelp schemas are UTF-16 LE with a BOM. The sniff read their
NUL bytes as binary, so no plugin could claim them. `a6bdbb9` decodes a head
that starts with a UTF-16 BOM; a head with NULs and no BOM stays binary
(`tests/test_lang_sniff.py`).

### Classification (D3, D8)

| Scope | `.xml` | `.xsd` | upstream (None) | code (fork) | changed |
|:--|--:|--:|--:|--:|--:|
| BentleyHelp | 76 | 0 | 76 | 58 | 58 |
| bentley-pyplace | 22 | 0 | 22 | 1 | 1 |
| claude-config | 0 | 47 | 47 | 0 | 0 |
| every git repo under `~/repos` + `~/.claude` | 127 | 165 | 292 | 63 | 63 |

The 63 changed files are the 58 + 1 corpus schemas and 4 fixture schemas in
this repo. The other 64 `.xml` and all 165 `.xsd` (47 PSMaml in claude-config)
classify as upstream does. BentleyHelp has 57 `.xml` that parse with an
`ECSchema` root plus `IllFormedXml.01.00.ecschema.xml`, which is claimed by its
head and keeps a file node only. `MissingNodes.01.00.ecschema.xml` has no root
element and is not claimed.

### Corpus counts

Truth grep, per claimed file (UTF-16 files through `iconv -f UTF-16 -t UTF-8`):
`grep -oE '<([A-Za-z_][A-Za-z0-9_.-]*:)?(ECClass|ECEntityClass|ECStructClass|ECCustomAttributeClass|ECRelationshipClass)[[:space:]>/]' | wc -l`.
The plan's `grep -c` counts lines and does not match an `ec:` prefix, so it
gives 5109 on the raw BentleyHelp files and 5133 after the UTF-16 decode.

| Repo | Claimed | Class tags (grep) | Class nodes | Difference |
|:--|--:|--:|--:|:--|
| BentleyHelp | 58 | 5134 | 5130 | 4: `IllFormedXml` (2, does not parse), `Unit_Attributes` (1, inside a comment), `MissingClassName` (1, no `typeName`) |
| bentley-pyplace | 1 | 3 | 3 | 0 |

BentleyHelp nodes: 58 file, 57 schema, 5130 class (4382 entity, 510
relationship, 141 custom_attribute, 97 struct), 10007 property, 0 enumeration
(all corpus schemas are EC 2.0). Edges: 15194 `contains`, 6254 `inherits`,
457 `source_constraint`, 365 `target_constraint`, 177 `uses`, 42 `imports`;
all EXTRACTED. `tests/lang/test_ecschema.py::test_corpus_class_count` pins the
per-file class count against an ElementTree parse for both repos.

### Known limits

- EC 3.x, enumerations and navigation properties are covered by the fixture
  only; the corpus has no EC 3.x schema.
- The sniff reads 4096 bytes: a root after a longer comment block is not
  claimed. A file with a DOCTYPE is not claimed, and the extractor refuses one.
- Custom attribute instances, `KindOfQuantity`, `PropertyCategory` and units
  items give no nodes.
- Fixed on `lang-cc-kb` (`271a06c`, `6503e04`): `.xml` is in
  `hook_suffixes`, so editing a schema triggers the git hook rebuild. Any other
  `.xml` edit triggers it too (owner, 2026-09-25).

## cc-kb (S13-S14, T30)

**Branch:** `lang-cc-kb` (off `lang-ecschema` `3e9e9fe`). Engine `271a06c`
(`hook_suffixes` read), `635ea9c` (augment payload keys carried), `01c76a2`
(a failing augment keeps the base result), `81b7fcc` (augments per path from
`_get_extractor`); plugin `9b266d3`.

### Step 0: hook set

`graphify.cli._HOOK_SOURCE_EXTS` was the code suffixes only; `hook_suffixes`
was parsed and never read. `get_registry_suffixes()` now returns the code
suffixes plus every manifest's `hook_suffixes`, and `detect` takes the code set
from `get_code_suffixes()`, so `CODE_EXTENSIONS` does not change. `cli.py` is
not edited. Measured after: `.yml .yaml .xml .mke .mki .bas .cls .frm` are in
the hook set; `.yml .yaml .xml` are not in `CODE_EXTENSIONS`
(`tests/lang/test_astgrep.py::test_hook_set_has_data_and_plugin_suffixes`).

### D10: docs that skip the AST pass

Read from the existing graphs (`graphify.build._is_ast_tier` on each node whose
`source_file` is `docs/cc-*.md`; the `watch.py` #1915 rule):

| Corpus | `cc-*.md` | Semantic-backed (skip AST) | In graph via AST | Not in graph |
|:--|--:|--:|--:|--:|
| `~/.claude` | 644 | 0 | 515 | 129 (`cc-AR*`, `.graphifyignore`) |
| claude-config | 633 | 0 | 633 | 0 |

0 of 1277: not material, so no hook in the #1915 path. The link reconciliation
(`watch._reconcile_markdown_links`) calls `extract_markdown` directly but only
to rebuild authored-link edges; it does not skip the AST pass. It does prune:
an AST `references` edge from a Markdown file with no authored link behind it
is dropped. Measured on the scratch copy of `~/.claude`: with the augment's
edges as `references`, the first `graphify update` kept all 2490 cross-doc and
code-path edges and the second one (one doc edited) kept 0. The augment
therefore uses the relation `cites`; with it, the second update keeps all of
them.

### What the augment adds

On the page node of `extract_markdown`: `cc_id`, `doc_class`, `group`,
`subgroup`, `is_hub`, and `spoke` (`S001`) for a spoke file. The resolver adds,
matching docs by file name in the same `docs/` folder:

- `contains` (context `hub_spoke`): `cc-XXGGG.000` to `cc-XXGGG.SSS`, and
  `cc-XXGGG.SSS` to its `-SNNN` spokes. Runs first, so it takes a pair before a
  mention does.
- `cites` (context `cc_ref`): a `cc-XXGGG.SSS[-SNNN]` mention anywhere in the
  text. A mention with no such doc goes to `dangling_cc_refs` on the page node.
- `cites` (context `code_ref`): a backticked path, optionally `:line`, outside
  a fence, that is a file under the repo root (the parent of `docs/`).
  `$CLAUDE_HOME/` and `~/.claude/` read as the repo root.

A pair that any edge already joins (a Markdown link) gets no second edge.

### Corpus counts

Scratch copies (the git-tracked files of each repo, `graphify update .`, AST
only, no LLM); `~/.claude/graphify-out` and claude-config were not touched.

| Corpus | Nodes | Edges base | Edges with augment | `hub_spoke` | `cc_ref` | `code_ref` | Docs with `cc_id` |
|:--|--:|--:|--:|--:|--:|--:|--:|
| `~/.claude` | 15972 | 19758 | 22538 | 241 | 1555 | 984 | 514 |
| claude-config | 47225 | - | 55169 | 235 | 1831 | 1065 | 632 |

The first build found an augment bug (an empty backtick span raised) that
made graphify skip 6 docs whole; `01c76a2` makes the wrapper keep the base
result when an augment raises.

### Checks (plan S13)

| Check | `~/.claude` | claude-config |
|:--|:--|:--|
| Each `cc-*` mention resolves or is dangling | 3286 mentions: 1663 by `cites`, 1189 by an existing edge, 434 dangling, 0 neither | 3941: 1949, 1777, 215, 0 |
| Dangling by class | AR 250 (ignored), SN 101, LR 35, IP 16, DB 10, RS 10, other 12 | SN 101, LR 35, AR 31, other 48 |
| Hub-to-spoke against the `cc-RF000.000` Quick Lookup | 417 expected pairs: 297 joined (241 `contains`, 56 Markdown link), 0 missing, 120 not graphed (AR); 0 `hub_spoke` edges outside the list | 408: 408 joined (235, 173), 0 missing; 6 `hub_spoke` edges for docs the index does not list |
| Base nodes the same with and without the augment | yes: 15972 nodes, identical after removing the added keys and `community` | - |
| Base edges kept | yes | - |
| `graphify lang list` | `cc-kb  +.md  -  match  cc-kb` | |
| Wheel | `graphify_lang/cc_kb/*` and the `cc-kb` entry point are in `graphifyy-0.9.67+lang.2-py3-none-any.whl` | |

### S14 value test (D6)

Five fixed questions, `graphify query "<q>" --graph <scratch>/graph.json`
(default 2000-token budget), on the `~/.claude` scratch copy. One build per
variant: `base` (every element off), `all`, and `all` minus one element
(`GRAPHIFY_CC_KB_OFF`). A cell is the position of the first node from the
relevant doc among the NODE lines, or `-` when none is in the output.

| Question | Relevant doc | base | all | no attrs | no cc_ref | no hub_spoke | no code_ref | all + D11 |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| Q1 where is db.ps1 write ownership documented | `cc-SY050.001` | - | 7 | 7 | 9 | 7 | - | 7 |
| Q2 which docs reference cc-SY050.000 | `cc-SY050.000` | 54 | 17 | 17 | 31 | 17 | 15 | 18 |
| Q2 docs citing `cc-SY050.000` in the output (of 40) | | 5 | 17 | 17 | 11 | 16 | 14 | 16 (+2 root, of 2) |
| Q3 what is the retrieval spec | `cc-SY060.000` | - | - | - | - | - | - | - |
| Q4 which hub lists the style guides | `cc-SG000.000` | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| Q5 what documents the graphify skip hook | `cc-SY010.007` | - | 8 | 8 | 12 | 8 | - | 9 |

No element pushes a relevant node out of the budget, so all four are kept.
`code_ref` gives the Q1 and Q5 hits; `cc_ref` moves Q1, Q2 and Q5 up;
`hub_spoke` adds one Q2 citer; the attributes do not change query output
(they are the `kb.db` join key). Every output is truncated at the budget
except Q3, whose start nodes are the `Retrieval` heading of `PROMPT-BASE.md`
and a graphify skill reference: `PROMPT-BASE.md` names `cc-SY060.000` but is
not a `docs/cc-*.md` file, so the augment does not read it.

### D11: root, agent and skill files (`9aa125f`)

The augment also reads the root `*.md`, `agents/**/*.md` and
`skills/**/*.md` files of a harness root, a folder whose `docs/` holds a
`cc-*.md` file. It adds `cc_ref` and `code_ref` edges from their page nodes;
attributes and `hub_spoke` stay on `docs/cc-*.md`. The `[match]` glob is
`*.md`, because a glob matches at any folder depth; the augment scopes each
file and returns nothing for any other `.md`. Same scratch copy and build as
above (`all + D11`):

| Check | Result |
|:--|:--|
| Edges | 22863 (`all` 22538): `cc_ref` 1776 (1555), `code_ref` 1088 (984), `hub_spoke` 241 (241) |
| New edges by source | agents 104 `cc_ref` + 26 `code_ref`, skills 101 + 76, root (`CLAUDE.md`, `CROSS-HOST.md`, `PROMPT-BASE.md`) 16 + 19; 72 files |
| `all` edges kept | 22521 of 22538; the other 17 pairs are joined by the reverse edge (an agent or skill file citing the doc that cites its path), one edge per pair |
| Base nodes, with and without | identical (15972) after removing the added keys and `community`; base edges kept (19758) |
| `cc_id` outside `docs/cc-*.md`; `hub_spoke` from a non-doc | 0; 0 |
| Second `graphify update`, `PROMPT-BASE.md` edited | edge counts unchanged |
| D10 for the new file set (`~/.claude/graphify-out`, read-only) | 131 files: 130 in the graph via AST, 0 semantic-backed, 1 not in the graph |
| Non-harness repos (git-tracked copy, all on against all off) | tmllm: 4601 nodes, 11609 edges, 0 extra edges. graphify-lang: 19214 nodes, 14 extra edges, all from its `.claude/docs/cc-*.md` (T30 scope) and the `tests/lang/fixtures/cc_kb` fixture tree. Base nodes identical in both |

Q3 is still not reached. `PROMPT-BASE.md` now cites `cc-SY060.000`, but the
edge is on its page node, and the query starts at the `Retrieval` heading:
`Retrieval` <- H1 <- `PROMPT-BASE.md` -> `cc-SY060.000.md` is 3 hops, and
the default traversal depth is 2. Q2 now shows the 2 root citers of
`cc-SY050.000` (`CLAUDE.md`, `PROMPT-BASE.md`) in the budget, which moves the
doc from 17 to 18 and one `docs/` citer out.

### Known limits

- Mention edges start at the page node, not at the heading whose section
  holds the mention (the Q3 miss: 3 hops from a heading start node).
- An incremental update resolves the changed docs against the whole graph,
  but a new hub gets its `contains` edges only when each spoke is next
  extracted (the edge is owned by the spoke's file).
- A path that exists but is not graphed (for example a file under
  `.graphifyignore`) adds nothing and is not listed.
