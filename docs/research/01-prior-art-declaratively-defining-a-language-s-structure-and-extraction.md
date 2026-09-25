# Prior art: declaratively defining a language's structure and extraction

Which existing systems let a language be defined in a config file rather than in code, and what the `graphify-lang` plugin manifest should therefore look like.

- Status: FINAL
- Created: 2026-09-21
- Full document: `.claude/docs/cc-RF010.001.md` (746 lines, 10 sections, source index in its §10)

## 1. Question

What is the prior art for a declarative language definition (suffixes, node kinds, edge kinds, and the rules that find them), and what format and rule tiers should the fork's manifest use?

## 2. Findings

Ranked systems, taken from the full document's §0 executive summary.

| Rank | System | Take | Leave |
|---:|---|---|---|
| 1 | tree-sitter tag queries (`tags.scm`) | the whole extraction-rule layer; standard captures `@definition.function`, `@reference.call`, `@name`, `@doc`; grammars already ship the files | nothing — closest fit, cheapest |
| 2 | universal-ctags optlib | the model for grammar-less languages: kinds, roles (= edge types), scope stack from a text file | its POSIX-ERE engine and C-binary dependency |
| 3 | GitHub linguist `languages.yml` | the registry shape: `type` / `extensions` / `filenames` / `interpreters` / `aliases` | display keys (`color`, `ace_mode`, …) |
| 4 | Semgrep rule YAML | composable predicates as the shape of a regex/prose rule block | its pattern engine |
| 5 | SCIP / Kythe / LSIF | the output vocabulary for edge kinds and roles | their wire formats |
| — | tree-sitter-graph / stack-graphs | ideas only | do not adopt: Rust-only, no Python bindings, stack-graphs archived 2025-09-09 [VERIFIED] |

Headline measurement (full document §7): a two-line tree-sitter query recovers **27 function definitions and 298 call references** from `~/repos/autolithp/src/core/err.lsp`, where graphify's hand-written Common Lisp walker produces **1 node and 0 edges**. The AutoLISP gap is a *query* problem, not a parser problem. [VERIFIED]

Format: **TOML**. graphify already reads TOML (`tomllib`, `tomli>=2.0.1` at `pyproject.toml:18`) and explicitly refuses a PyYAML dependency (`graphify/ingest.py:23`). [VERIFIED]

## 3. Implications for this repo

1. The manifest is a file-backed superset of the existing `LanguageConfig` (`graphify/extractors/models.py:14-57`), not a parallel model.
2. Do not invent a rule DSL: rule tier 1 is tree-sitter queries; tier 2 is regex for grammar-less suffixes (DCL, MNL).
3. Ship `graphify_lang.toml` inside the language package, discovered through `importlib.resources`; the entry point carries only the name → package pointer.
4. Feeds decisions D-004 and D-005 in `docs/40-DECISIONS.md`.

## 4. Sources

Full URL list is in `.claude/docs/cc-RF010.001.md` §10 (research done 2026-09-08).
