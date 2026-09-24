<!-- TEMPLATE-VERSION: 2026-02-28-001 -->
<!-- TEMPLATE-START -->
# cc-LR000.002.md

## Quick Reference

**Topics covered:** General (graphify-file-id-drops-extension, regex-rules-filter-kind, graphify-normalize-id-collapses-punctuation-merging-symbols) · Bug Fix (regex-rules-kind-filter) · Pattern (autolisp-package-lit-fix-is-a-query-not-a-walker)

Scan entries by category below, or search by topic tag.
<!-- TEMPLATE-END -->

---

<!-- CONTENT-START -->
## Register

### General (Language-Agnostic)

**2026-09-08 · graphify-normalize-id-collapses-punctuation-merging-symbols** — graphify.ids.normalize_id collapses EVERY run of non-word characters to "_" (graphify/ids.py:80-83), not just case. For a language whose symbols carry punctuation — AutoLISP pkg:name, and the pkg:_private convention — make_id silently MERGES distinct definitions: src/core/err.lsp in ~/repos/autolithp has 27 defuns but yields only 26 distinct ids (err:trap == err:_trap), with 11 colliding id groups across the 80-file corpus (6 of them *error* redefined per command in one file, 24x in pltrn.lsp). Any new graphify extractor for such a language MUST disambiguate on collision the way extractors/markdown.py already does for repeated headings (_make_id(stem, title, str(line_num))), or the node count silently under-reports and the graph merges unrelated functions. Verified 2026-09-08 against graphifyy 0.9.55 (source: graphify 0.9.55 source + ~/repos/autolithp@f7ab804)

**2026-09-23 · regex-rules-filter-kind** — regex_rules.py fix: when from_manifest() loads rules, filter to only rules with kind="regex" to avoid processing query rules with empty patterns which match every position in text (source: ag-build)

**2026-09-24 · graphify-file-id-drops-extension** — graphify file-node ids drop the extension (_file_node_id -> _make_id(_file_stem(rel))), so x.lsp and its x.md sidecar share one id; a file->sidecar edge becomes a self-loop. Markdown node ids are already root-relative when language resolvers run, while AST extractor ids are still absolute-stem ids (remapped after resolvers) — match cross-extractor targets by source_file, not by recomputed id. Also: extract() with no cache_root writes ./graphify-out/cache keyed only by content hash + graphifyy version, so fork tests pollute the repo's stock graph cache; always pass cache_root=tmp_path. (source: graphify-lang plan 02)

### Bug Fix

**2026-09-23 · regex-rules-kind-filter** — RegexRules.from_manifest() must skip [[rule]] entries whose kind != "regex"; query rules carry an empty pattern, and an empty regex matches every position in the text. (source: omp session 01a0c668 (restored by main 2026-09-23))

### Pattern

**2026-09-08 · autolisp-package-lit-fix-is-a-query-not-a-walker** — Measured 2026-09-08 with ~/.local/share/pipx/venvs/graphifyy/bin/python (tree-sitter 0.25.2, tree_sitter_commonlisp) against ~/repos/autolithp/src/core/err.lsp. The upstream tree-sitter-commonlisp queries/tags.scm line '(defun_header function_name: (sym_lit) @name) @definition.function' captures 0 definitions in AutoLISP, because names like err:trap parse as package_lit. Changing it to '[(sym_lit) (package_lit)]' captures all 27 defuns; adding '(list_lit . [(sym_lit) (package_lit)] @name) @reference.call' captures 298 calls. graphify's hand-written extract_commonlisp walker yields 1 node / 0 edges for the same file. Conclusion: the AutoLISP gap is a QUERY problem, not a parser problem - the Common Lisp grammar parses err.lsp with zero ERROR nodes. Consequence for the plugin manifest: a tree-sitter query rule type is the highest-value rule type, and it must be paired with a builtins denylist (base.py _LANGUAGE_BUILTIN_GLOBALS) because the call query also captures car/cdr/cond/and. Also note the AutoLISP suffix .lsp is already claimed by _DISPATCH for Common Lisp (and by GitHub linguist), so a plugin claiming it is overriding, not adding. (source: https://github.com/tree-sitter-grammars/tree-sitter-commonlisp/blob/master/queries/tags.scm)
<!-- CONTENT-END -->
