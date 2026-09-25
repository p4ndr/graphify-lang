# Content sniffing, augment plugins, and five new languages

A content-sniff router for suffixes that two languages share, an `augment` manifest kind that adds to a built-in extractor's output, and plugins for VBA, bmake, Cargo TOML, ast-grep YAML, Bentley ECSchema XML, and the harness KB markdown.

- Status: DONE
- Created: 2026-09-25
- Tasks: T27 (S1-S6), T28 (S7), T29 (S8-S12), T30 (S13-S14), T31 (S15-S17)

## 1. Goal

Each file in the local repos goes to the extractor for its real content, not only for its suffix. Measured start point (2026-09-25): `extract_apex(Path('~/repos/bim-chk/src/document/ThisWorkbook.cls'))` gives 1 node and 0 edges for a VBA class that has 6 procedures. `.bas`, `.frm`, `.mki`, `.mke` have no extractor. `.toml` and `.xml` are not graphed, and `.yml` goes only to the LLM step.

## 2. Scope

Decisions (owner, 2026-09-25):

| # | Decision |
|:--|:---------|
| D1 | A plugin declares its content test as a `[sniff]` table in the manifest TOML: regex rules with weights, read on the first `head_bytes` of the file, plus `min_score`. No Python sniff callables. |
| D2 | A built-in extractor is the fallback. A plugin gets a shared-suffix file only when its sniff score is at or above `min_score`. Otherwise the built-in runs as it does today. No sniff profile for built-ins. |
| D3 | Plugins for data formats (`.yml`, `.xml`, `.toml`) use a `[match]` glob and a sniff. A file is code only when both pass. Every other file with that suffix stays as it is today. |
| D4 | One plan. Generic engine work goes on branch `lang-sniff`, in its own commits, for upstream. Each language goes on its own branch off `lang-sniff` (`MIGRATION.md`: one language per PR). |
| D5 | New manifest kind `augment`. It runs after a built-in extractor and adds nodes, edges and attributes to that result. The built-in extractor file is not edited. First use: the harness KB markdown (`cc-*.md`). |
| D6 | The KB augment adds `cc-*` cross-link edges, class and group attributes with hub-to-spoke edges, a `cc_id` key that matches `kb.db` rows, and edges from code paths in backticks. Any element that makes query results worse is removed (S14 measures this). |
| D7 | Each new plugin has its own Python extractor, as AutoLISP and DCL do after plan 02 (`graphify_lang/autolisp/extract.py`). No tree-sitter grammar. The regex rules runtime (`graphify_lang/rules.py`, `queries.py`, `regex_rules.py`, `builtins.py`, `templates/`) is repaired to the S005 emission contract and kept as a fallback and utility layer (P16 option 2). A plugin may call it; no plugin depends on it. |
| D8 | The XML plugin takes only files whose root element is `<ECSchema`. PSMaml `.xsd` and all other XML stay as today. |
| D9 | (2026-09-25, after T27) Upstream sends `Cargo.toml` to `extract_package_manifest` before `_DISPATCH` is used. S10 therefore becomes an augment on top of `extract_package_manifest`: one registry-lookup hook in `_get_extractor`, and it adds workspace-to-member and path-dependency edges only. |
| D10 | (2026-09-25, after T27) The augment runs only in the AST pass. At the start of S13, count the `cc-*.md` docs in `~/.claude` that skip that pass (semantic-backed docs, `watch.py` #1915, and reconciliation calling `extract_markdown` directly). Add registry hooks in those paths only if the count is material. |
| D11 | (2026-09-25, after T30) The `cc-kb` augment also reads root `*.md` files and the agent and skill `*.md` files (`agents/**/*.md`, `skills/**/*.md`) for `cc-*` and code-path references. Class and group attributes and hub-to-spoke edges stay limited to `docs/cc-*.md`. |
| D12 | (2026-09-25) `cc-kb` `cites` edges (`cc_ref`, `code_ref`) are also added from the heading node whose section holds the mention, one per section and target, on top of the unchanged page-level edges; text above the first heading keeps the page edge only. Chosen over heading-only (S14 Q1 7->16, Q5 9->14) and over one heading edge per target (Q1 7->8): S14 Q1 7, Q2 18->14 (17 citers), Q3 -->3, Q4 2, Q5 9; edges 22863->29969. |

In scope: the repair of the regex rules runtime; engine work in `graphify/lang_registry.py` and `graphify_lang/`; the registry lookup lines in `graphify/detect.py` and `graphify/extract.py`; six plugins under `graphify_lang/`; test fixtures; a rebuild of the affected graphs.

Out of scope: edits to any existing extractor file, `engine.py` or `resolution.py`; general YAML, TOML or XML graphing; a sniff profile for Apex; the Windows host; the upstream PR itself (plan 01 T10).

Target corpora:

| Plugin | Suffixes | Repos |
|:-------|:---------|:------|
| `vba` | `.bas` `.cls` `.frm` (`.frx` skipped) | BentleyTools, bentley-model-management, bim-chk |
| `bmake` | `.mki` `.mke` | BentleyHelp |
| `cargo` | `Cargo.toml` | moxide, oa-graph, oag-dev, tmllm, llm-linter-tool, comment-sidecar |
| `astgrep` | `sgconfig.yml`, `rules/**/*.yml`, `rule-tests/**/*.yml` | llm-linter-tool |
| `ecschema` | `.xml` (root `<ECSchema`), `.ecschema.xml` | BentleyHelp, bentley-pyplace |
| `cc-kb` (augment) | `.md` under `docs/cc-*.md` | `~/.claude`, claude-config |

## 3. Design

### 3.1 Sniff router (D1, D2)

- Manifest schema gains two optional tables. `[sniff]`: `head_bytes` (default 4096), `rules = [{ re, weight, flags }]`, `min_score`. `[match]`: `globs` and `filenames`, matched on the repo-relative path.
- The registry groups claimants by suffix: at most one built-in (from `_DISPATCH` before the registry runs) plus each plugin that lists the suffix. Today a second claimant only logs a warning (`graphify_lang/registry.py`, `_register_manifest`). That warning is replaced by the router.
- For a suffix with more than one claimant, `apply_dispatch` puts a router function in `_DISPATCH[suffix]`. The router reads the file head once, scores each plugin, and calls the best plugin at or above its `min_score`. If no plugin passes, it calls the built-in. If there is no built-in, it returns an empty result, which is the same as the upstream `.m`/MATLAB path in `_get_extractor`.
- Ties: the higher manifest `priority` wins. If the priorities are equal, the router logs one warning per suffix for each process, and the first registered plugin wins.
- A plugin that has only a sniff and no `[match]` competes for the whole suffix. A plugin that has a `[match]` competes only for the files that match it.
- The existing `overrides` key (`.lsp` in `graphify_lang/autolisp/graphify-lang.toml`) stays. It means "wins with no sniff". The loader rejects a manifest that sets `overrides` and `[sniff]` on the same suffix.
- The router has a stable `__name__` (`sniff_router[.cls]`), so cache keys and the log show which path ran.

### 3.2 Detect hook for data suffixes (D3)

- `classify_file` puts `.yml` in DOC and does not graph `.toml` or `.xml`. One registry lookup is added before the extension test: if a plugin's `[match]` and sniff pass for this path, the file is CODE. Otherwise the result is the same as today.
- The lookup reads the file head only for suffixes that some plugin with a `[match]` claims. Detect cost for other files does not change.
- These suffixes are not added to `CODE_EXTENSIONS`. The per-file hook is the only change, and it is a registry lookup, which `.claude/CLAUDE.md` 'Tracking upstream' permits.

### 3.3 Augment kind (D5)

- `[language] kind = "augment"` and `augments = [".md"]`, plus `[match]`. The plugin module exports `augment(path, base_result) -> dict` and returns extra `nodes`, `edges` and node `attrs`, keyed by the base node IDs.
- The registry wraps the built-in: `wrapped(p) = merge(builtin(p), augment(p, builtin(p)))`. This runs only when the `[match]` passes. The wrapper is composed with the router: first route, then augment the result of the extractor that ran.
- Merge rules: the augment cannot delete or rename a base node. New node IDs use the plugin prefix. An attribute that already exists is not overwritten, and each clash is logged.
- A cross-file target (for example, the `cc-*` doc that a link names) uses the existing resolver hook (`LanguageResolver`, as AutoLISP does), not a lookup in the extractor.

### 3.4 Plugins

| Plugin | Nodes | Edges | Sniff / match |
|:-------|:------|:------|:--------------|
| `vba` | module (`Attribute VB_Name`), class, form, `Sub`/`Function`/`Property`, `Declare`, `Type`, `Enum` | calls (case-insensitive, VBA builtins list), `Implements`, `New`/`As <Class>` uses, form -> code-behind | `^VERSION 1\.0 CLASS`, `^Attribute VB_Name`, `^VERSION 5\.00` (form), `(Sub\|Function) \w+\(`; `.bas`/`.frm` are single-claimant, so the sniff is used only for `.cls` |
| `bmake` | makefile, macro definitions, targets | `%include` -> `.mki`, target -> source (`.cpp`, `.h`, `.r`, `.mke`) | `%include`, `^\w+\s*=`, `$(` macro use |
| `cargo` | crate, workspace | workspace -> member, crate -> path/workspace dependency (external crates are attributes, not nodes) | filename `Cargo.toml`; `^\[(package\|workspace)\]` |
| `astgrep` | rule (`id`), language, util | rule -> test file, rule -> snapshot, `sgconfig` -> rule dirs | globs in the corpus table; `^id:` plus `^rule:` or `^language:` |
| `ecschema` | schema, class, property, enumeration | schema -> referenced schema, class -> base class, relationship source/target | `<ECSchema` in the head |
| `cc-kb` | none new (augment) | doc -> doc (`cc-*` mention or link), hub -> spoke, doc -> code path (backtick path that exists in the repo) | `docs/cc-*.md`; attrs `cc_id`, `doc_class`, `group`, `subgroup`, `is_hub` |

`cc-kb` does not read `kb.db` at extract time, because the DB is per-host. The `cc_id` attribute is the join key that an agent uses with `mcp__db__db_query`.

## 4. Steps

| Step | Branch | Action | Check |
|:-----|:-------|:-------|:------|
| S1 | `lang-sniff` | Write the heuristic tests first (red): fixtures `tests/fixtures/sniff/vba_class.cls`, `vba_class_bom_crlf.cls`, `apex_class.cls`, `apex_with_vb_comment.cls`, `empty.cls`, `binary.cls`. Test file `tests/test_lang_sniff.py`: routing per fixture, the fallback to Apex, ties, `head_bytes` truncation, CRLF, UTF-8 BOM, Windows-1252 bytes, an undecodable head. | The tests fail for the correct reason: the router does not exist. |
| S2 | `lang-sniff` | Manifest schema: `[sniff]` and `[match]` tables, the `kind`/`augments` keys, validation errors (a bad regex, `min_score` without rules, `overrides` + `[sniff]` on one suffix). | `tests/test_lang_registry.py` passes; new schema tests pass. |
| S3 | `lang-sniff` | Registry claimant table, the router (§3.1), a stable router name, and the tie warning. `graphify lang list` gets a `sniff` column and a `shared` marker. | S1 tests pass with a minimal test-only VBA manifest (sniff only, one stub node). `.lsp` routing and `tests/lang_baseline.txt` do not change. |
| S4 | `lang-sniff` | Detect hook for `[match]` data suffixes (§3.2), with tests: `Cargo.toml` is CODE, `pyproject.toml` is not graphed as before, `rules/x.yml` is CODE, `.github/workflows/ci.yml` stays DOC. | `pytest tests/ -q` exits 0; `tests/upstream_tables.json` snapshot is not changed. |
| S5 | `lang-sniff` | Augment kind (§3.3): wrapper, merge rules, and composition with the router. Test with a stub augment on `.md`. | The base markdown nodes are the same with and without the augment; the stub edges are added. |
| S6 | `lang-sniff` | Update `README.md` (fork design), `ARCHITECTURE.md` only where it names changed registry symbols (test-pinned), and plan 01 T10 notes (these commits go upstream). Tag `v0.9.67+lang.2`. | `tests/test_architecture_doc.py` passes. |
| S7 | `lang-rules` | Repair the regex rules runtime (P16 option 2): emit a file node, `label`/`source_file`/`file_type`, `_file_stem` IDs, a line suffix on ID clashes, `@reference` call edges and the builtins filter; make the query tier fail loudly; add `templates/` to package data; replace the empty-list checks in `tests/lang/test_rules.py`. Test on a DCL manifest built from rules, compared with `extract_dcl`. | A rules-based DCL run on `tests/lang/fixtures` gives the same file and dialog nodes as `extract_dcl`; the wheel contains `graphify_lang/templates/`. |
| S8 | `lang-vba` | VBA plugin (own extractor, builtins list, resolver for cross-module calls). Replace the S3 test-only manifest. Corpus run on the 3 VBA repos. | `ThisWorkbook.cls` gives more than 1 node; the counts of Sub/Function nodes match `grep -ciE '^(public \|private \|friend )?(static )?(sub\|function\|property (get\|let\|set)) '` per repo; `tests/fixtures/sample.cls` (Apex) output is unchanged. |
| S9 | `lang-bmake` | bmake plugin. Corpus run on BentleyHelp. | Each `%include` in `.mki`/`.mke` gives an edge; the count matches `grep -c '%include'`. |
| S10 | `lang-cargo` | Cargo plugin. Corpus run on the 6 Rust repos. | The workspace-member edges match `cargo metadata --no-deps` for each repo. |
| S11 | `lang-astgrep` | ast-grep plugin. Corpus run on llm-linter-tool. | Rule node count = `rules/**/*.yml` files with `^id:`; each rule that has a test has one test edge. |
| S12 | `lang-ecschema` | ECSchema plugin. Corpus run on BentleyHelp and bentley-pyplace. | Class node count matches `grep -c '<ECEntityClass\|<ECStructClass\|<ECCustomAttributeClass\|<ECRelationshipClass'`; PSMaml `.xsd` files in claude-config are not claimed. |
| S13 | `lang-cc-kb` | KB augment. Run on `~/.claude/docs` and claude-config. | Each `cc-*` link resolves, or is listed as dangling in the corpus report; hub-to-spoke edges match `cc-RF000.000`. |
| S14 | `lang-cc-kb` | Value test for D6: run 5 fixed `graphify query` questions on `~/.claude` with and without each augment element. Remove an element that pushes relevant nodes out of the default 2000-token budget. | The kept elements and the query results are written in `docs/testing/case_007_plan04-sniff-and-plugins.md`. |
| S15 | `autolisp` | Add `pyyaml` to the runtime dependencies (the pipx venv has no `yaml`; the astgrep plugin otherwise uses its fallback parser, owner 2026-09-25). Delete `build/` before the wheel build. Merge the language branches into the release line. Tag `v0.9.67+lang.3`, build the wheel, `pipx install --force` (plan 03 S5). | `graphify lang list` shows all 8 languages; both MCP servers start. |
| S16 | - | Rebuild the affected graphs: back up `graph.json`, delete `graphify-out/cache/ast/`, run `graphify update <path>` (plan 03 S7) for the 12 repos in the corpus table plus `~/.claude`. | Each repo exits 0; `mcp__graphify__graph_stats` works on each. |
| S17 | - | Add learnings (sniff router, augment kind). Update `$CLAUDE_HOME/CLAUDE.md` graphify paragraph: VBA, bmake, and KB augment are now graphed. | `graphify lang list` output matches the paragraph. |

## 5. Acceptance criteria

- `pytest tests/ -q` exits 0 on every branch, and no upstream test file is edited.
- VBA `.cls` goes to `vba`, and Apex `.cls` goes to `extract_apex`, with the S1 fixtures as proof.
- No existing extractor file, `engine.py` or `resolution.py` is changed (`git diff upstream/v8 -- graphify/extractors/` shows no change).
- A `.yml`, `.toml` or `.xml` file that no `[match]` claims is classified as it is on `upstream/v8`.
- The engine commits on `lang-sniff` contain no language-specific code.
- `case_007` records the counts for each plugin and the S14 result.

## 6. Risks and open questions

| # | Item | Handling |
|:--|:-----|:---------|
| R1 | A VBA `.cls` that has no header (hand-written, not exported) scores below `min_score` and goes to Apex. | The S1 fixture `vba_class` without a header and a body-only rule (`(Sub\|Function) \w+\(` weight 3, `Dim \w+ As` weight 3) cover this case. Tune in S8 on the corpus. |
| R2 | The detect hook reads file heads for claimed data suffixes, which adds I/O to the detect step. | Read only for suffixes that some `[match]` claims, and only for glob hits. Measure the detect time on `~/.claude` before and after S4. |
| R3 | Upstream adds its own `.cls` or `.bas` handling. | Rebase conflicts are limited to the registry lookup lines. The router still falls back to the built-in (D2). |
| R4 | The augment adds noise to `~/.claude` query results. | S14 measures this; D6 lets an element be removed. |
| R5 | (S16) A rebuilt graph or the release is bad. | Per repo: `cp graphify-out/graph.pre-plan04.json graphify-out/graph.json`. Global: `pipx install --force "graphifyy[mcp,commonlisp] @ file://$HOME/.local/share/graphify-lang/wheels/graphifyy-0.9.67+lang.1-py3-none-any.whl"` (no lang.2 wheel was built), then `rm -rf graphify-out/cache/ast` and `graphify update <path>` per repo. |
