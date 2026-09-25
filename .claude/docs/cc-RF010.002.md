# Upstream state relevant to a graphify plugin/registry layer

> **Repo**: `Graphify-Labs/graphify` (upstream), default branch `v8`
> **Fork**: `/home/p4ndr/repos/graphify-lang`, branch `v8` = `a5dcc70` (fork init on top of `c9f9901` = tag `v0.9.55`)
> **Upstream head at time of research**: `67f99bd` "release: 0.9.56", 2026-09-07
> **Fork position**: `git rev-list --count v8..upstream/v8` = **16**; `upstream/v8..v8` = **1** (the fork-init commit)
> **Date of research**: 2026-09-08
> **Method**: `gh` CLI (issues/PRs/search API), local clone (`git log/diff/show/grep` against `upstream/v8`)

---

## 1. The upstream plugin / registry discussion

### 1.1 Issue #3180 — Pluggable extractor packaging (entry-point discovery)

- URL: https://github.com/Graphify-Labs/graphify/issues/3180
- **State: OPEN. Author: `Ashfaqbs`. Created 2026-08-29T02:47:54Z, updated same timestamp. 0 comments, 0 labels, no milestone, no assignee, no linked PR.**
- No maintainer (`safishamsi`) response of any kind.
- Proposal verbatim shape: a `graphify.extractors` entry-point group discovered at startup by `importlib.metadata.entry_points`, *alongside* (not replacing) the built-in `_DISPATCH`; each third-party package owns its grammar dependency, its `extract_<lang>(path) -> dict`, and its suffix registration.
- Cites the long tail of unclaimed language requests as motivation: GDScript (#2152), Haxe (#1424), MATLAB (#2935), 1C/BSL (#2127).
- Explicit open question left to the maintainer: whether built-ins migrate to the same mechanism or the entry-point path serves new third-party additions only.
- Closes with "This is a proposal, not a commitment to implement."

**Read**: this is the closest issue to the fork's design, it is 10 days old, and it has drawn zero engagement. There is no maintainer direction to follow and no reservation of the work by anyone.

### 1.2 Issue #1070 — [1.0.0 RFC] Extractor plugin API + CLI command group consolidation

- URL: https://github.com/Graphify-Labs/graphify/issues/1070
- **State: OPEN. Author: `ryanhaarmann`. Created 2026-05-28, last updated 2026-05-30. 3 comments.**
- Proposes exactly the setuptools entry-point group `graphify.extractors`, with a `load_plugin_extractors()` in `graphify/extract.py` and a `Extractor` Protocol of `can_extract(path) -> bool` / `extract(path) -> ExtractionResult`. Cites `pytest11`, `flake8.extension`, `mkdocs.plugins` as precedent.
- **The only maintainer statement anywhere in this thread group**, `safishamsi` @ 2026-05-30T08:24:03Z, verbatim:
  > "Hey, thanks for this!!
  > Feel free to send a pr if possible"
- Nothing since. No design constraints stated, no protocol shape chosen, no rejection.
- Note the proposed protocol (`can_extract` + a class) is **different in shape** from what the code actually wants today (a bare `Callable[[Path], dict]`, which is what `LANGUAGE_EXTRACTORS` already holds). The fork's manifest design is closer to the code than #1070's Protocol is.

### 1.3 Issue #1212 — Split extract.py into per-language modules

- URL: https://github.com/Graphify-Labs/graphify/issues/1212
- **State: OPEN. Author: `nucleusjay`. Created 2026-06-09. 0 comments** (no maintainer reply), despite the work having been largely done.
- Proposed exactly the shape that now exists: `graphify/extractors/__init__.py` holding `LANGUAGE_EXTRACTORS`, `base.py`, per-language modules, `extract.py` as a thin orchestrator.
- Its "Risk" paragraph asks for language-by-language delivery, which is what `graphify/extractors/MIGRATION.md` codifies.

### 1.4 PR #2857 — complete extractor migration to extractors/ package

- URL: https://github.com/Graphify-Labs/graphify/pull/2857
- **State: OPEN, NOT merged, NOT closed. Author `thebigshed`, head `extractor-migration`, base `v8`. Created 2026-08-18T18:40:28Z, last updated 2026-08-18T19:07:09Z (19 minutes later — the automated review). Zero human comments. Zero maintainer response in 3 weeks.**
- Size: 25 files, `graphify/extract.py` **+25 / −2522**; adds `js.py` (+521), `xaml.py` (+636), `python.py` (+234), `csproj.py`, `groovy.py`, etc.; `tests/test_extractors_registry.py` +175.
- Claim in the body: "`extract.py` is now a pure facade of re-exports and extraction orchestration (`extract()`, `collect_files()`, `_get_extractor()`). Every entry in MIGRATION.md is marked `yes`."
- The only review is from the `graphify-labs` bot ("Graphify reviewed this change" — 5 advisory findings, one formal-verification behaviour change in `_hyperedge_script`).
- **Confirmed not landed**: `git show upstream/v8:graphify/extractors/MIGRATION.md` still marks the config-driven batch (`python, js, java, c, cpp, csharp, kotlin, scala, php, lua, swift, groovy, vue, svelte, astro, xaml`) and the bespoke set (`julia, verilog, markdown, objc, csproj, slnx, lazarus_package, pascal`) as `no`, and `graphify/extractors/` at `upstream/v8` contains no `python.py`, `js.py` or `xaml.py`.

### 1.5 PR #2951 — optional bounded LSP semantic providers

- URL: https://github.com/Graphify-Labs/graphify/pull/2951 (implements issue #2948, also OPEN)
- **State: OPEN, NOT merged. Author `kerberosmansour`, head `feat/bounded-lsp-providers`, base `v8`. Created 2026-08-22T12:04:56Z, last updated 2026-08-22T12:13:43Z (9 minutes later — the bot review). Zero human comments, zero maintainer response.**
- **The extension seam it proposes is a wholly separate top-level package, `graphify_semantic_providers/`, not a hook inside `graphify/`.** Files: `contracts.py` (+76), `registry.py` (+214), `lsp.py` (+745), `merge.py` (+118), `cli.py` (+182), plus `docs/SEMANTIC-PROVIDERS.md` and 4 test files. `pyproject.toml` +3/−2 adds an optional extra and a `graphify-semantic` console entry point.
- Its registry is **manifest-driven**: a provider manifest declares languages/commands and "custom provider manifests extend language coverage without adding language-specific runner code". Providers are discovered from manifests, run as bounded `shell=False` subprocesses, and merged **additively into a separate graph output** — the native tree-sitter path is untouched.
- Explicit non-goals stated by the author: does not wire providers into `graphify extract`, does not download servers, does not run by default.
- Bot review raised 5 advisories, incl. `cli.py:79` calling `registry.for_workspace` where the registry defines `for_path`.

**Relevance to the fork**: #2951 is the closest existing precedent for "a new capability arrives as a sibling top-level package with its own manifest registry, plus a minimal `pyproject.toml` touch". It has been sitting unanswered for 17 days. Its design deliberately avoids touching `graphify/extract.py` at all — a strictly more conservative posture than the fork's, which needs 5 table lookups inside the core.

### 1.6 Keyword sweep across all issues and PRs

Searches run: `entry_points`, `importlib.metadata`, `plugin`, `LANGUAGE_EXTRACTORS`, `_DISPATCH`, `rewire dispatch`, `registry` (title+body); plus PR searches for `entry point extractor`, `plugin extractor`, `registry dispatch`, `extractors package`, and `extractor in:title`.

- `entry_points` / `importlib.metadata` as an extractor-plugin mechanism: **only #1070 and #3180**. Nothing else, anywhere.
- `rewire dispatch`: **zero hits** in issues or PRs. The phrase lives only in `graphify/extractors/MIGRATION.md` ("Do not rewire dispatch, add classes, or add lazy imports — mechanism layers come later, by separate agreement (see #1212 discussion)").
- `LANGUAGE_EXTRACTORS`: **only #1212**.
- **GitHub code search for a `graphify.extractors` entry-point group across all of GitHub returns `total_count: 0`.** No fork, no downstream package, has implemented this.
- Upstream branches (`gh api repos/.../branches`): `main`, `v1`…`v8`, `feat/codebuddy-support`, `fix/default-import-export-edges`, `prototypes/resolution-experiments`. **No plugin/registry branch.**
- **Conclusion: no implementation of entry-point extractor discovery exists anywhere — not upstream, not on a branch, not in a PR, not in a published fork.** The fork is not duplicating work.

### 1.7 The decisive context: upstream does not merge pull requests any more

| Metric | Value | Source |
|:--|--:|:--|
| Total PRs ever opened | 1,658 | `search/issues q=repo:… is:pr` |
| Total merged | **135** | `is:pr is:merged` |
| Total closed unmerged | **867** | `is:pr is:closed is:unmerged` |
| Currently open | **656** | `gh pr list --state open` |
| **Merged in the last 60 days (since 2026-07-09)** | **0** | `is:pr is:merged merged:>=2026-07-09` |
| Last 100 closed PRs that were merged | **0** | `gh pr list --state closed --limit 100` |
| Last merged PR | **#1737, 2026-07-08** "refactor: decompose extract.py and __main__.py into focused modules" (author `TPAteeq`) | `is:pr is:merged sort:updated-desc` |
| Open issues | 1,261 | repo meta |
| Stars / forks | 115,653 / 11,223 | repo meta |

How work actually lands instead: contributions are absorbed as maintainer-authored commits crediting the **issue** and the reporter. E.g. CHANGELOG 0.9.56 "Fix: Rust trait method declarations … (#3366, thanks @santoshpy)" → `#3366` is an **issue**, not a PR (`gh api …/issues/3366` → `pull_request: null`, opened by `santoshpy`), and the code landed as `43de793 fix(rust): extract trait method declarations (#3366)`.

Commit authorship on `upstream/v8`, last 30 days (324 commits total): `safishamsi` 114, `abhay-codes07` 31, `hopstreax` 14, `rajashidattapy` 13, `Ousama Ben Younes` 10, `Synvoya` 7, then a long tail. So external names *do* appear as commit authors — but via direct commits on `v8`, not via merged PRs.

**Implication for the fork's roadmap phase 6.** "Open a PR for the registry alone" has an empirically near-zero landing probability as a PR. The mechanism with a track record is: **open a precise, measured ISSUE** (like #3366, #3381, #1689 — all of which produced code within days) and let the maintainer implement, or accept that the fork carries the registry indefinitely. #1084 is the closest working precedent for a registry-shaped feature landing this way (see §1.8).

### 1.8 Precedent that matters: issue #1084 (custom LLM providers)

- URL: https://github.com/Graphify-Labs/graphify/issues/1084 — **CLOSED 2026-05-30**, two days after filing.
- The ask: register a provider without editing `llm.py`.
- `safishamsi` @ 2026-05-30: "Landed in commit a9d6be6. Your analysis was right — the architecture was already there. Three changes: **1. Provider registry loaded at import** — `~/.graphify/providers.json` (global) and `.graphify/providers.json` (per-project) are merged into `BACKENDS` at module import time. **Built-in provider names are protected and cannot be overridden.** Missing `pricing` defaults to zero … 2. CLI commands … 3. `detect_backend()` updated — custom providers are tried after all built-ins."

**Three design signals the fork should copy verbatim**, because the maintainer has already blessed them in an adjacent subsystem:
1. **Merge external registrations into the built-in table at import time** (not lazily on a dispatch miss). This settles the fork's open question 2.
2. **Built-in names are protected and cannot be overridden.** This is a direct answer — and a *negative* one — to the fork's open question 3 (whether a package may claim `.lsp`, which `_DISPATCH` already owns). Expect precedence to fall to the built-in unless argued explicitly.
3. **Custom entries are tried after all built-ins.** Ordering is built-ins-first.

Note also that #1084 used a **config file**, not an entry point. A `~/.graphify/languages.json` style discovery would be more in keeping with what the maintainer has actually shipped than `importlib.metadata`.

### 1.9 Adjacent open requests that a registry would serve

Each of these is an unserved language/format request that a plugin layer answers generically — useful as motivation in an upstream issue:

| Issue | State | Ask |
|:--|:--|:--|
| #2942 | open | generic `.xml` unclassified/skipped; ~1,062 XML files → 0 nodes |
| #2851 | open | `.properties`, plugin XML, `Dockerfile*`, `META-INF/services/*` unclassified. **Explicitly demands classify+extract land together**, citing #1689 |
| #2848 | open | systemd `.service`/`.timer` in no extension set |
| #2349 | open | Gherkin `.feature` invisible |
| #1689 | open | `.r`/`.R` in `CODE_EXTENSIONS` with no extractor — 43 files → 0 nodes; partially addressed by a warning (`377dc7f`), the extractor still missing |
| #2214 | open | deterministic ingestion of structured data files (the canonical YAML/JSON-config issue; #2637 was closed as its duplicate) |
| #2152 / #1424 / #2935 / #2127 | open | GDScript / Haxe / MATLAB / 1C-BSL |

Open PRs adding languages that have never been merged and would all be unnecessary under a registry: #1836 + #1929 (GDScript), #2083 (OpenEdge ABL), #2480 (Pine Script), #2481 (MQL5), #2742 (AdvPL/TLPP), #2996 (AL), #3013 + #1788 (Perl), #3221 (F#), #2828 (Monkey C), #1874 + #458 (Solidity), #2001 (Twig), #2754 (Jenkinsfile), #2043 (K8s YAML), #2409 (dbt SQL), #1759 + #2065 (R), #2476 (VHDL/TCL), #2835 (zsh/SAS).

---

## 2. Diff v0.9.55 → v0.9.56 (`git diff v8..upstream/v8`) in the six files

```
graphify/extract.py               |  76 +++++++++++++++++---
graphify/extractors/dart.py       | 120 ++++++++++++++++++++-----------
graphify/extractors/engine.py     |  19 ++++-
graphify/extractors/resolution.py | 146 +++++++++++++++++++++++++++++++++++++-
graphify/extractors/rust.py       |  31 ++++++++
5 files changed, 339 insertions(+), 53 deletions(-)
```

**`graphify/detect.py`, `graphify/watch.py`, `graphify/cli.py`, `graphify/resolver_registry.py`: ZERO changes between `v8` and `upstream/v8`.**

### 2.1 Table-by-table verdict (the question the fork actually asked)

| Symbol | Location at `upstream/v8` | Changed 0.9.55→0.9.56? |
|:--|:--|:--|
| `_DISPATCH` | `graphify/extract.py:5689` | **No** (content byte-identical; the definition simply moved from line 5630 to 5689) |
| `_EXTRA_FOR_EXTENSION` | `graphify/extract.py:5799` | **No** (was 5740) |
| `_SHEBANG_DISPATCH` | `graphify/extract.py:5830` | **No** |
| `_get_extractor` | `graphify/extract.py:5921` | **No** (was 5862) |
| `collect_files` | `graphify/extract.py:7633` | **No** (was 7573); still `_EXTENSIONS = set(_DISPATCH.keys())` at `:7638` |
| `extract()` | `graphify/extract.py:6196` | Body touched only by one added cache clear (`_PACKAGE_IMPORTS_CACHE.clear()`); signature unchanged (was 6137) |
| `CODE_EXTENSIONS` | `graphify/detect.py:44` | **No** |
| `DOC_EXTENSIONS` | `graphify/detect.py:45` | **No** |
| `_WATCHED_EXTENSIONS` | `graphify/watch.py:278` | **No** |
| `_HOOK_SOURCE_EXTS` | `graphify/cli.py:71-75` | **No** |
| `LANGUAGE_EXTRACTORS` | `graphify/extractors/__init__.py:34` | **No** |
| `resolver_registry.register` | `graphify/resolver_registry.py:48` | **No** (file untouched since `86ecb76`, 2026-06-29) |

`graphify/extract.py` grew 7,645 → 7,705 lines. **Every fork line-number citation into `extract.py` above line ~1360 is still valid; every citation below it is off by +59 or +60.** Corrected values are in the table above. The README's `extract.py:6371` (install hint) is now `:6431`.

### 2.2 What the 16 commits actually did

```
67f99bd 2026-09-07 release: 0.9.56
20a631e 2026-09-07 test(ts): measure CPU time in the normalizer scaling test to de-flake it
3b9356b 2026-09-07 Add source_location to Dart extraction
82b25b9 2026-09-07 fix(extract): make _TsRangeIndex a real type alias
1dcb1e1 2026-09-07 fix(extract): remove quadratic scan in TS import-type normalization (#3359)
98d62e2 2026-09-07 test(labeling): pin max_concurrency=1 so batch-order assertion is deterministic
4a7653b 2026-09-07 Kill workers inside the SIGALRM handler too, before it raises
2226fd9 2026-09-07 Kill orphaned workers before the rebuild watchdog exits
462f89a 2026-09-07 Let builtin named member calls through to cross file resolution
7f87c3b 2026-09-06 fix(paths): bound atomic temp filename length
6e420a0 2026-09-06 test(rust): cover trait method declarations and decl/impl id distinctness
43de793 2026-09-06 fix(rust): extract trait method declarations (#3366)
29b7a21 2026-09-06 fix(serve): traverse the MCP query_graph undirected
5aef7f4 2026-09-05 fix: resolve unmapped @/ imports in JS projects
2d54b05 2026-09-04 fix(js): resolve Node subpath imports via package.json `imports`
b09c839 2026-08-26 fix(hooks): a graphify skip must not terminate the whole git hook (#2986)
```

Per-file characterisation:

- **`extract.py` (+76/−17)**: adds `from bisect import bisect_right`; a new type alias `_TsRangeIndex` and two helpers `_ts_ranges_containing` / `_ts_build_range_index` replacing an O(matches × ranges) linear scan in `_normalize_ts_import_types` (#3359); an `@/`-prefix fallback in `_resolve_rescued_specifier`; `_PACKAGE_IMPORTS_CACHE` imported from `resolution` and cleared in `extract()`. **All TypeScript-normalisation internals. Nothing structural.**
- **`extractors/resolution.py` (+145/−1)**: new `_PACKAGE_IMPORTS_CACHE` plus `_find_js_project_anchor`, `_load_package_imports`, `_match_subpath_import`, `_resolve_package_import` — Node `#subpath` imports via `package.json` `imports` (#3382).
- **`extractors/engine.py` (+17/−2)**: the `_extract_generic` builtin-member-call carve-out (#3381) — `_builtin_member_call = is_member_call and callee_name in _LANGUAGE_BUILTIN_GLOBALS`, then let it through but force `tgt_nid = None` so it can only reach an edge through a receiver-typed resolver. **Relevant to the fork**: `_LANGUAGE_BUILTIN_GLOBALS` (`extractors/base.py:13`) is now explicitly documented as "one union across every language", and the mitigation for false suppression is the *member-call* carve-out, not per-language denylists. An AutoLISP `vla-`/`vlax-` denylist would be adding to a global union and would suppress those names for every other language too.
- **`extractors/rust.py` (+31)**: trait method declarations (#3366).
- **`extractors/dart.py` (+81/−39)**: `source_location` stamping (#3365).

### 2.3 Rebase burden

- **19 release tags in the 30 days to 2026-09-08** (`v0.9.38` 2026-08-09 … `v0.9.56` 2026-09-07). Median gap ≈ 1.5 days.
- **324 commits on `upstream/v8` in the same 30 days**; **103 of them touch `graphify/extract.py` or `graphify/extractors/`** (~32%).
- 90-day commit counts on the other four files: `detect.py` 66, `cli.py` 70, `watch.py` 44, `resolver_registry.py` **1**.
- Last touch: `extract.py` 2026-09-07, `extractors/` 2026-09-07, `cli.py` 2026-09-04, `watch.py` 2026-09-03, `detect.py` 2026-08-30, `resolver_registry.py` 2026-06-29.

A fork branch that adds ~5 one-line lookups will rebase cleanly against churn of this shape **only if each lookup is placed on its own line adjacent to a stable anchor**. `extract.py` is the hot file (≈3.4 touching commits per day); `resolver_registry.py` is effectively frozen and is the safest place to put anything.

---

## 3. Non-code files the fork wants plugins for

### 3.1 Current classification (all at `upstream/v8`, unchanged from 0.9.55)

`graphify/detect.py:44-49`:
```python
CODE_EXTENSIONS = {'.py', '.ts', ..., '.json', '.tf', '.tfvars', '.hcl', ..., '.lisp', '.cl', '.lsp', '.asd', '.robot', '.resource'}
DOC_EXTENSIONS  = {'.md', '.mdx', '.qmd', '.skill', '.txt', '.rst', '.html', '.yaml', '.yml'}
PAPER_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
```

| Suffix | `CODE_EXTENSIONS` | `DOC_EXTENSIONS` | in `_DISPATCH` | Effective fate |
|:--|:--|:--|:--|:--|
| `.yaml` / `.yml` | no | **yes** | **no** | Walked, classified `document`, hashed into the manifest → **LLM semantic path only**. Zero deterministic nodes. |
| `.txt`, `.rst`, `.html` | no | **yes** | **no** | Same: LLM semantic path only. |
| `.md`, `.mdx`, `.qmd`, `.skill` | no | **yes** | **yes** (`extract_markdown`) | Both: deterministic AST nodes *and* the semantic path. The only doc suffixes with a deterministic extractor. |
| `.toml` | no | no | no | **Invisible.** Never collected at all. Sole exception: `manifest_ingest.is_package_manifest_path()` matches `pyproject.toml` / `cargo.toml` by *filename* (`manifest_ingest.py:31-32`) and `_get_extractor` routes those to `extract_package_manifest` before suffix dispatch (`extract.py:5930`). |
| `.ini`, `.cfg`, `.conf`, `.config` | no | no | no | **Invisible.** (They appear only in `detect.py:193`, a secret-scanning suffix list.) |
| `.xml` | no | no | no | **Invisible** (issue #2942). `.csproj`/`.fsproj`/`.vbproj`/`.xaml`/`.slnx` are separate suffixes with their own extractors; `pom.xml` is a filename special case in `manifest_ingest`. |
| `.jsonc` | no | no | no | **Invisible.** `_DISPATCH` has `.json` only. `extractors/json_config.py:12-14` names `deno.jsonc` / `biome.jsonc` in its *filename* list, but a `.jsonc` file never reaches `collect_files` because its suffix is not a `_DISPATCH` key. `_strip_jsonc` (`resolution.py:68`) exists purely for `tsconfig.json` parsing. |

### 3.2 Is there a deterministic (AST) extractor for YAML or TOML? **No.**

- `grep` for `yaml` across `graphify/`: hits are (a) markdown frontmatter parsing in `extractors/markdown.py:63-69` (`import yaml` guarded by `try/except ImportError` — **PyYAML is not a declared dependency**), (b) `pnpm-workspace.yaml` filename checks in `extractors/resolution.py:25,335,367,529`, (c) `_yaml_str` escapers in `export.py:126` for *writing* Obsidian frontmatter, (d) the `DOC_EXTENSIONS` membership. **No YAML extractor.**
- `grep` for `toml`: `cargo_introspect.py` (opt-in `--cargo` flag, `tomllib`/`tomli`) and `manifest_ingest.py` (`pyproject.toml` / `Cargo.toml` by filename). **No general TOML extractor.**
- `grep` for `jsonc`: comment-stripping only.
- Open PR #2043 "feat(extract): add Kubernetes/ArgoCD/Helm-values YAML extractor" (open since 2026-08-03) would add `graphify/extractors/k8s.py` (+284) and 8 lines to `detect.py` — **still unmerged**, like every other language PR.

### 3.3 How `extract_markdown` models the document — the template to copy

`graphify/extractors/markdown.py` (467 lines, no tree-sitter dependency, pure line scanning).

**Nodes**

| Node | `file_type` | `node_kind` | `id` recipe | `source_location` |
|:--|:--|:--|:--|:--|
| the file | `"document"` | `"page"` | `_make_id(str(path))` | `L1` |
| each heading `#`…`######` | `"document"` | `"heading"` | `_make_id(stem, title)`, `stem = _file_stem(path)`; on collision `_make_id(stem, title, str(line_num))` | `L<line>` |

The page node additionally carries `frontmatter` (a dict) when YAML frontmatter is present, passed through `security.sanitize_metadata`.

**Edges** (all `confidence: "EXTRACTED"`, `weight: 1.0`, stamped with `source_file` and `source_location`)

| Relation | From → to | Source form |
|:--|:--|:--|
| `contains` | file → top-level heading | position |
| `contains` | parent heading → child heading | level nesting via a `heading_stack` |
| `references` | file → linked document | `[text](./other.md)`, `[label]: ./other.md`, `[[wikilink]]` |

**The `node_kind` precedent — the single most important design fact for the fork's node model.** From the `extract_markdown` docstring, verbatim:

> "``node_kind`` exists because ``file_type`` cannot carry this distinction: it is a closed enum (build.py rewrites anything outside ``code|document|paper|image|rationale|concept`` to ``"concept"``) and ``"document"`` on both endpoints is load-bearing for the twin-merge pass."

Confirmed in `graphify/build.py:856-857`:
```python
if ft and ft not in {"code", "document", "paper", "image", "rationale", "concept"}:
    node["file_type"] = _FILE_TYPE_SYNONYMS.get(ft, "concept")
```

So the fork's planned node kinds (function, command, global, module, dialog, sidecar doc) **cannot** go in `file_type` — they must go in `node_kind`, with `file_type` staying `"code"`. `node_kind` is currently used by exactly one extractor (markdown, values `page` and `heading`); the fork would be the second user and is free to define its own vocabulary there.

Other transferable mechanics in `markdown.py`:
- **`target_file` stamping** (`markdown.py`, `add_link`): a cross-file edge stamps `edge["target_file"] = str(resolved)` **only when the target exists on disk**, so the #2169 remap pass can canonicalise the target id on an incremental run. Without it a cross-file edge built from an absolute path matches no node in the merged graph and silently drops (#2211). **The fork's `loads` / `sidecar_doc` / `dcl_references` edges need this same stamp.**
- **Deduplication of link edges by resolved target** (`linked_targets` set), so weights stay meaningful.
- **Fenced-code-block suppression** and an unterminated-fence guard (`_MD_FRONTMATTER_MAX_LINES = 200`).
- Failure contract: `except` on read returns `{"nodes": [], "edges": [], "error": str(e)}`; success returns `{"nodes", "edges", "input_tokens": 0, "output_tokens": 0}`.

### 3.4 `file_type` vocabulary (whole codebase)

Closed enum, enforced at `build.py:856`: **`code`, `document`, `paper`, `image`, `rationale`, `concept`**. Literal-occurrence tally across `graphify/` (`"file_type": "..."` plus `file_type="..."` kwargs):

| value | occurrences |
|:--|--:|
| `code` | 79 |
| `concept` | 12 |
| `rationale` | 4 |
| `document` | 2 |
| `doc_ref` | 1 (`build.py` synonym source; rewritten to `concept`) |

`_FILE_TYPE_SYNONYMS` (`build.py:93-101`) maps `pattern`, `principle`, `constraint`, `tech`, `technology`, `data-source`, `data_source`, `gotcha`, `framework` → `concept`.

### 3.5 `relation` vocabulary (whole codebase)

**Open, not enforced.** `ARCHITECTURE.md:60` documents the edge schema as `{"source", "target", "relation": "calls|imports|uses|...", "confidence": "EXTRACTED|INFERRED|AMBIGUOUS"}` — the `|...` is literal; there is no validation of relation strings. `confidence` is the closed part (`ARCHITECTURE.md:69-73`).

Distinct literals across `graphify/` (`relation:`/`relation=`/`_rel=` followed by a string literal; many edges use a variable, so this undercounts call sites but captures the vocabulary):

| relation | literal occurrences |
|:--|--:|
| `calls` | 21 |
| `imports` | 19 |
| `contains` | 10 |
| `references` | 8 |
| `imports_from` | 7 |
| `inherits` | 4 |
| `uses` | 2 |
| `rationale_for` | 2 |
| `method` | 2 |
| `indirect_call` | 2 |
| `implements` | 2 |
| `defines` | 2 |
| `uses_static_prop` | 1 |
| `uses_component` | 1 |
| `requires_env` | 1 |
| `references_constant` | 1 |
| `re_exports` | 1 |
| `mixes_in` | 1 |
| `listened_by` | 1 |
| `instantiates` | 1 |
| `includes` | 1 |
| `depends_on` | 1 |
| `crate_depends_on` | 1 |
| `cites` | 1 |
| `bound_to` | 1 |
| `binds_method` | 1 |

Also present in 0.9.49+ CHANGELOG: `dispatches_to` (C# single-implementer interface dispatch).

Precedent for language-specific relation names: `crate_depends_on` (Rust/cargo), `binds_method`, `listened_by`, `uses_component`, `mixes_in`. **The fork's proposed `dcl_references`, `dcl_action`, `command_invokes`, `module_depends`, `sidecar_doc`, `loads` are all admissible** — nothing validates the string. Files carrying the most `"relation"` occurrences: `extract.py` (84), `engine.py` (14), `analyze.py` (14).

---

## 4. CHANGELOG since 0.9.40, and release cadence

`CHANGELOG.md` at `upstream/v8` is 1,984 lines. `## 0.9.56 (unreleased)` at line 5 (note: the tag `v0.9.56` exists on 2026-09-07 but the heading still says unreleased); `## 0.9.40 (2026-08-11)` at line 233.

### 4.1 Entries mentioning `extractors/`, registry, plugin, dispatch, or a new language

Scanning lines 1-248 (i.e. 0.9.40 → 0.9.56) for those terms:

| Version | Entry (abridged) | Category |
|:--|:--|:--|
| 0.9.56 | Rust trait method declarations extracted (#3366) | extractor fix |
| 0.9.56 | Dart `source_location` stamping (#3365) | extractor fix |
| 0.9.56 | builtin-named member calls handed to cross-file resolution (#3381) | engine |
| 0.9.55 | Common Lisp node ids derived from full path stem (line 84) | **the `.lsp` extractor the fork replaces** |
| 0.9.54 | duplicate reference edges collapsed at extractor level (#3251) | extractor |
| 0.9.49 | C# `dispatches_to` edge for single-implementer interfaces (#3003) | **new relation string** |
| 0.9.48 | C# `references` edges for generic type arguments (#2911) | extractor |
| 0.9.47 | data-shaped JSON declined by extractor no longer counted as failure (#2879) | extractor |
| 0.9.45 | Go exported/unexported case-collision id fix (#2779) | extractor |
| 0.9.43 | Bash `source` path form resolution (#2596) | extractor |
| 0.9.41 | `Cargo.toml` recognised as a package manifest (#2434, PR #2494) | **manifest_ingest — the TOML answer** |
| 0.9.40 | `graphify update` refuses shrunken graph on extractor failure (#2663) | pipeline |

**There is no CHANGELOG entry in this range — or anywhere in the file — mentioning a plugin API, entry-point discovery, an extractor registry, or dispatch rewiring.** The `extractors/` package itself landed via PR #1737 (merged 2026-07-08), i.e. before 0.9.40's window in this scan and unaccompanied by any dispatch change.

Also note: **no "new language" entry at all between 0.9.40 and 0.9.56** — 16 releases, zero languages added, while ~20 language PRs sit open. That is the strongest single argument for the registry, and the strongest evidence it will not arrive from upstream soon.

### 4.2 Release cadence

19 tags in the 30 days to 2026-09-08:

```
v0.9.38 2026-08-09   v0.9.44 2026-08-15   v0.9.50 2026-08-25
v0.9.39 2026-08-10   v0.9.45 2026-08-16   v0.9.51 2026-08-28
v0.9.40 2026-08-11   v0.9.46 2026-08-17   v0.9.52 2026-08-29
v0.9.41 2026-08-12   v0.9.47 2026-08-19   v0.9.53 2026-08-30
v0.9.42 2026-08-13   v0.9.48 2026-08-20   v0.9.54 2026-09-05
v0.9.43 2026-08-14   v0.9.49 2026-08-24   v0.9.55 2026-09-05
                                          v0.9.56 2026-09-07
```

≈ one release every 1.6 days; 324 commits / 30 days ≈ 10.8 commits/day, of which ≈ 3.4/day touch `extract.py` or `extractors/`.

---

## 5. Test-suite constraints on a registry

### 5.1 `tests/test_extractors_registry.py` (44 lines)

Two tests, and they are the *only* things guarding the registry seam:

1. `test_every_registry_extractor_is_reexported_from_facade` — for every `(lang, fn)` in `LANGUAGE_EXTRACTORS`, `graphify.extract` must have an attribute named `fn.__name__` and it must be **the same object** (`is`).
2. `test_terraform_migrated` — `facade.extract_terraform is extract_terraform is LANGUAGE_EXTRACTORS["terraform"]`.

**Constraint on the fork.** If a plugin's extractor is inserted into `LANGUAGE_EXTRACTORS`, test 1 fails immediately: `graphify.extract` will not have an attribute named `extract_autolisp`. **Therefore the plugin registry must be a separate structure, not an injection into `LANGUAGE_EXTRACTORS`** — or the sweep must be scoped to built-ins. This directly contradicts the fork README's mapping of the manifest `name` field onto "the same role as the `LANGUAGE_EXTRACTORS` key".

Also from the module docstring: the registry seed came from #1721/@Cekaru and #1737, "generalized here to sweep the whole registry so a future move that forgets the facade re-export (or re-exports a different object) fails loudly."

### 5.2 `tests/test_extract.py` — the `_DISPATCH` sweeps

- `test_collect_files_from_dir` (`:379-384`): `supported = set(_DISPATCH.keys()); assert all(f.suffix in supported for f in collect_files(FIXTURES))`. **A registry that widens `collect_files` beyond `_DISPATCH` breaks this the moment a fixture file with a plugin suffix exists.** Safe while the registry is empty.
- `_legacy_collect_files` + `test_collect_files_parity_with_legacy_on_fixtures` / `..._synthetic` (`:442-470`): a parity oracle that re-implements the walk reading `set(_DISPATCH.keys())` directly. **If `collect_files` starts reading `_DISPATCH | registry` and the oracle does not, parity breaks for any registered suffix.** This is the sharpest single constraint on the fork's design: the registry must either be merged *into* `_DISPATCH` itself (so both readers see it) or accept that the oracle diverges.
  - **The #1084 precedent resolves this cleanly**: merge external registrations *into the built-in table at import time*, exactly as custom LLM providers are merged into `BACKENDS`. Then `_DISPATCH` is the only table, `collect_files` is untouched, the oracle still passes, and no core lookup is needed in `collect_files` at all.
- `test_extract_warns_on_code_files_with_no_ast_extractor` (`:3796`) and `test_extract_no_warning_when_all_code_has_extractors` (`:3816`): the #1689 warning fires per extension for code files with no extractor. A registry that adds `.lsp` handling must not change the `.r` behaviour these pin.
- `test_dispatch_has_shell_entries` (`:2447-2449`): `.sh`, `.bash`, `.json` in `_DISPATCH`.
- `monkeypatch.setitem(extract_mod._DISPATCH, ".go", ...)` at `:2359`, `:2420` and in `test_extract_cli.py:1224,1238,1266,1321` — `_DISPATCH` must stay a **plain mutable dict supporting `setitem`**. A registry that replaces it with a property, a `MappingProxyType`, or a class breaks 6 tests.

### 5.3 Other suffix-set assertions

| Test | Assertion |
|:--|:--|
| `tests/test_cjs_module_extension.py:26-48` | `.cjs` in `CODE_EXTENSIONS`; `_DISPATCH[".cjs"] is extract_js`; **`.cjs` in `cli._HOOK_SOURCE_EXTS`** — the only test touching `_HOOK_SOURCE_EXTS` |
| `tests/test_pascal.py:124-142, 316-321` | 8 suffixes in `_DISPATCH`, 6 in `CODE_EXTENSIONS`, `.dfm` in `_DISPATCH` |
| `tests/test_dotnet.py:725-727` | a set of .NET suffixes in `CODE_EXTENSIONS` |
| `tests/test_astro_extraction.py:37` | `.astro` in `CODE_EXTENSIONS` |
| `tests/test_languages.py:343-344` | `.metal` in `CODE_EXTENSIONS` |
| `tests/test_detect.py:38` | `.psm1` (#1315) |

All are **membership** assertions (`in`), never exact-equality assertions on the whole table. **No test asserts the exact contents of `_DISPATCH`, `CODE_EXTENSIONS`, or `_HOOK_SOURCE_EXTS`.** Adding entries is therefore safe; removing or reshaping is not.

### 5.4 `tests/test_oversized_document_slicing.py` — the DOC_EXTENSIONS contract

```python
missing = sorted((DOC_EXTENSIONS - BINARY_DOC_SUFFIXES) - _SPLITTABLE_TEXT_SUFFIXES)
assert not missing
```
plus a parametrised `test_an_oversized_document_reaches_the_model_whole` over every non-PDF doc suffix. **Any suffix added to `DOC_EXTENSIONS` must simultaneously be added to `file_slice._SPLITTABLE_TEXT_SUFFIXES` (`file_slice.py:33-40`) or the suite fails.** This binds the fork if a language package ever registers a *document* suffix (and would bind an upstream registry that lets a plugin extend `DOC_EXTENSIONS`).

### 5.5 `tests/test_architecture_doc.py` (87 lines) — narrower than the fork assumes

The fork's `README.md` and `.claude/CLAUDE.md` say "`tests/test_architecture_doc.py` imports every symbol it names". **Precisely**: it parses only the `## Module responsibilities` table (`text.index("## Module responsibilities")` to the next `##`), extracts `` `module.py` `` rows and `` `func(` ``/`` `func` `` cells from them, and asserts `hasattr(module, func)` for each. It also asserts `extract()`'s first parameter is named `paths` and annotated `list`, that the doc does not contain `` `extract(path)` ``, and that it tells callers to pass `root=`.

Consequences:
- The `## Adding a new language extractor` section (`ARCHITECTURE.md:75-80`) is **not** test-pinned. Its 5 steps still describe the pre-registry procedure ("Register the file suffix in `extract()`'s dispatch table and in `collect_files()` (both in `extract.py`)" — collect_files now derives from `_DISPATCH`, so that is already one edit, not two). A fork or upstream PR may update that prose freely.
- A new public entry point only needs an ARCHITECTURE.md update **if it is added to the module-responsibilities table**. A registry module that is not listed there is unconstrained by this test.
- `test_the_table_was_actually_parsed` requires ≥10 parsed symbols and that `{graphify.extract, graphify.build, graphify.serve}` are present — so the table cannot be gutted.

---

## 6. Risks and constraints for the fork

1. **Upstream has merged zero pull requests in 60 days (135 of 1,658 ever; 656 open; last merge 2026-07-08).** Roadmap phase 6 ("open a PR for the registry alone") is, on the evidence, the lowest-probability path to landing anything. The mechanism that demonstrably works is a **precise, measured issue** — #3366, #3381, #1689, #1084 all produced maintainer-authored code, often within days — with the fork's implementation offered as reference. Plan for the fork to carry the registry indefinitely and treat upstreaming as a bonus.
2. **`tests/test_extractors_registry.py` forbids putting a plugin extractor into `LANGUAGE_EXTRACTORS`.** The facade-identity sweep requires `graphify.extract` to expose an attribute named `fn.__name__` that is the same object. Injecting `extract_autolisp` fails that test on the first run. The fork's manifest `name` field must key a *separate* structure. (`tests/test_extractors_registry.py:24-38`)
3. **`test_collect_files_parity_with_legacy_on_fixtures` re-implements the walk from `set(_DISPATCH.keys())`.** If `collect_files` learns to read a registry that the oracle does not, parity breaks for any registered suffix. **The lowest-risk design is `#1084`'s: merge registered suffixes into `_DISPATCH` itself at import time**, leaving `collect_files` and both oracles untouched — which also removes one of the five planned core lookups. (`tests/test_extract.py:442-467`)
4. **`_DISPATCH` must remain a plain mutable dict.** Six tests call `monkeypatch.setitem(extract_mod._DISPATCH, ...)`. No `MappingProxyType`, no property, no class wrapper. (`tests/test_extract.py:2359,2420`; `tests/test_extract_cli.py:1224,1238,1266,1321`)
5. **Precedence is already decided against the fork, by precedent.** #1084's registry "protect[s] built-in provider names [so they] cannot be overridden" and tries custom entries "after all built-ins". `.lsp` is currently owned by `extract_commonlisp` (`extract.py:5691`) and `commonlisp` is a documented pip extra (`_EXTRA_FOR_EXTENSION[".lsp"] = "commonlisp"`, `extract.py:5799+`). A registry that lets a package *steal* `.lsp` runs against the only precedent there is. Options: (a) make override explicit and opt-in with a loud warning; (b) claim `.lsp` only when the CommonLisp grammar is absent; (c) argue the case separately, on the measured evidence in the fork README (79 files → 79 nodes, 0 edges).
6. **`file_type` is a closed enum; the fork's node kinds must go in `node_kind`.** `build.py:856` rewrites anything outside `code|document|paper|image|rationale|concept` to `"concept"`. `extract_markdown` documents exactly this and uses `node_kind` (`page`, `heading`) for the distinction. The fork's `function`/`command`/`global`/`module`/`dialog`/`sidecar doc` therefore go in `node_kind` with `file_type: "code"`. `node_kind` is currently used by one extractor, so the vocabulary is the fork's to define.
7. **`relation` is unvalidated and open** (`ARCHITECTURE.md:60` says `"calls|imports|uses|..."`), with per-language precedent (`crate_depends_on`, `binds_method`, `dispatches_to`). The fork's `dcl_references`, `dcl_action`, `command_invokes`, `module_depends`, `loads`, `sidecar_doc` are admissible with no core change. `confidence` is the closed part: `EXTRACTED|INFERRED|AMBIGUOUS`.
8. **Cross-file edges need the `target_file` stamp or they silently drop on incremental runs.** `extractors/markdown.py`'s `add_link` stamps `edge["target_file"]` only when the target exists on disk (#2211/#2169), so the remap pass can canonicalise the id. The fork's `loads`, `sidecar_doc`, and `dcl_references` edges cross files and need the same treatment; the `load_dialog` variable-argument case (`pltrn.lsp:10903`) must stay dangling with no stamp.
9. **`_LANGUAGE_BUILTIN_GLOBALS` is one union across every language and got *more* load-bearing in 0.9.56.** Commit `462f89a` (#3381) added a member-call carve-out precisely because the union was wrong per-language. Adding `vla-`/`vlax-` names to it would suppress those tokens for every other language. The fork's COM-call decision should be a local filter inside the AutoLISP extractor, not an addition to the shared union. (`extractors/base.py:13`, `extractors/engine.py:5607-5660`)
10. **Rebase cost is real and concentrated in exactly the file the fork must touch.** 324 commits / 30 days on `v8`; 103 of them (~32%) touch `extract.py` or `extractors/`; 19 releases in 30 days. `extract.py` grew 7,645 → 7,705 lines in 16 commits and all fork line citations below ~line 1,400 shifted by +59/+60. Keep each core lookup to one line adjacent to a stable anchor, and prefer `resolver_registry.py` (1 commit in 90 days) for anything that can live there.
11. **`detect.py`, `watch.py`, `cli.py`, `resolver_registry.py` did not change at all in 0.9.55→0.9.56**, so those four fork citations are still exact: `detect.py:44` (`CODE_EXTENSIONS`), `detect.py:45` (`DOC_EXTENSIONS`), `watch.py:278` (`_WATCHED_EXTENSIONS`), `cli.py:71-75` (`_HOOK_SOURCE_EXTS`), `cli.py:881` (its consumer), `resolver_registry.py:28-42/48/59-85`. Only the `extract.py` citations need the +59/+60 correction (table in §2.1).
12. **`_HOOK_SOURCE_EXTS` has exactly one test** (`test_cjs_module_extension.py:47-48`, a membership check) and no override mechanism; it is consumed at `cli.py:881` via a `tails` suffix test. Making it registry-aware is the least-constrained of the five core edits.
13. **`.dcl` and `.mnl` are in no extension set at all** (`CODE_EXTENSIONS`, `DOC_EXTENSIONS`, `PAPER_EXTENSIONS`, `IMAGE_EXTENSIONS`, `_DISPATCH`) — the same invisible-file class as `.toml`, `.ini`, `.xml`, `.jsonc`. If the fork ever routes a suffix into `DOC_EXTENSIONS` rather than `CODE_EXTENSIONS`, `tests/test_oversized_document_slicing.py` requires a matching entry in `file_slice._SPLITTABLE_TEXT_SUFFIXES`.
14. **Issue #2851's constraint applies to the fork too**: "do **not** only append these suffixes to `CODE_EXTENSIONS`" — a file that enters `manifest.json` with no graph node is a regression (that is #1689's failure mode, still open after 3 months and a warning-only fix at `377dc7f`). Classification and extraction must land together for `.lsp`, `.dcl`, `.mnl`.
15. **The `## Adding a new language extractor` section of `ARCHITECTURE.md` is not test-pinned** (only the `## Module responsibilities` table is). A registry PR should update that prose — it is the doc every language contributor follows — and doing so costs nothing in tests.
16. **PR #2951 is the strongest structural precedent available and it is also unanswered.** A sibling top-level package (`graphify_semantic_providers/`) with a manifest-driven registry, an optional extra, and zero changes to `graphify/extract.py` — sitting 17 days with no human reply. If a *zero-core-change* extension layer cannot get a response, a five-core-lookup one will not either. Consider whether the fork's AutoLISP layer can be delivered as a sibling package that monkey-patches `_DISPATCH` at import time (the #1084 shape) with **no upstream diff at all** — that would reduce the fork's diff against upstream to zero core files and make rebases trivial.
