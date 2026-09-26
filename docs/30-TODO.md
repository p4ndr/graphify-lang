<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 30-TODO.md

This document is a LIVE file containing a list of TASKS to be carried out.

- `§3` is the TASKS in priority order, each with STEPS. Marks: `[ ]` open, `[~]` in progress, `[x]` done, `[?]` blocked by owner input.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`todo_add`, `todo_step_add`, `todo_set`); hand edits by the owner are fine. They number TASKS and STEPS, write the progress lines, and move finished TASKS to `35-DONE.md`.
- To block a TASK or STEP: `pending_add` an ITEM with it as the source, then `todo_set` it `blocked` with that ITEM.
<!-- TEMPLATE-END -->

## 3. TASK LIST

### `[x]` T2 | S002 (registry) Fork CI, release safety and the perf marker — plan §S002

- `[x]` T2.1 | Add .github/workflows/graphify-lang-ci.yml (new file; ci.yml stays unedited): triggers on every branch, `permissions: contents: read`, `uv sync --locked`, matrix ubuntu × 3.10/3.12/3.13 plus windows × 3.12, and a leg pinned to `tree-sitter==0.23.*`
- `[x]` T2.2 | Add `if: github.repository == 'Graphify-Labs/graphify'` to every job in publish.yml and release-graph.yml so the fork's first release does not publish to PyPI
- `[x]` T2.3 | Add `addopts = "-m 'not perf'"` and register the `perf` marker under `[tool.pytest.ini_options]`
- `[x]` T2.4 | Leave `pyproject.toml` `version` alone; fork releases are git tags only, `0.9.55+lang.<n>`
### `[x]` T3 | S003 (registry) lang_registry.py: manifest schema, discovery and precedence — plan §S003

- `[x]` T3.1 | `LanguageManifest` frozen dataclass with `from_toml(path)`, and the complete schema v1 key set (SRS F1)
- `[x]` T3.2 | Validation: every failure is a one-line reason and a rejected manifest, never an exception
- `[x]` T3.3 | Discovery in a fixed tier order: entry-point group, then `GRAPHIFY_LANG_PATH`; `GRAPHIFY_LANG_DISABLE=1` disables it entirely; cache per process
- `[x]` T3.4 | Precedence: a built-in suffix is taken only when listed in `overrides`, with a once-per-process WARNING
- `[x]` T3.5 | tests/test_lang_registry.py: schema round-trip and each validation failure. No core file is edited in this section

### `[x]` T4 | S004 (registry) Core merge: three call sites, lazy dispatch, thunked resolver — plan §S004

- `[x]` T4.1 | One line after `CODE_EXTENSIONS` (graphify/detect.py:44), one after `_EXTRA_FOR_EXTENSION` (`graphify/extract.py`), one after `_HOOK_SOURCE_EXTS` (graphify/cli.py:71) — each individually `try`-wrapped
- `[x]` T4.2 | `apply_dispatch` inserts a per-suffix callable with a stable `__name__`; `_DISPATCH` stays a plain mutable dict
- `[x]` T4.3 | Thunk the resolver and register case variants, because `run_language_resolvers` gates on exact suffix match
- `[x]` T4.4 | Add one row to the `## Module responsibilities` table in `ARCHITECTURE.md` (test-pinned by `tests/test_architecture_doc.py`)
- `[x]` T4.5 | Tests are subprocess-based wherever they compare with-plugin against without-plugin; SC2, SC3, SC13, SC14 must pass and `guard-core` must show exactly four files

### `[x]` T9 | S009 (autolisp) Packaging, hook and watch coverage, recorded measurements — plan §S009

- `[x]` T9.1 | Append the plugin to `[tool.setuptools] packages` (graphify_lang.autolisp added to packages list)
- `[x]` T9.2 | One test that resolves the manifest and its data files through `importlib.resources` (TODO: write test)
- `[x]` T9.3 | SC12 in-process half: `_run_hook_guard('read')` — not gated, needs no install (TODO: implement)
- `[x]` T9.4 | The shipped `[project.entry-points."graphify_lang.plugins"]` stanza (one line)
- `[x]` T9.5 | The MCP registration install script (scripts/install-mcp.sh) and manual run (TODO: run manually)
- `[x]` T9.6 | Take the SRS §1.3 tier-2 recorded measurements and write them into the documents (TODO: add to docs)
### `[ ]` T10 | S010 (registry) Upstream proposal — plan §S010

- `[ ]` T10.1 | Produce the artefact: `git diff v8...lang-registry -- graphify/`
- `[ ]` T10.2 | Open an ISSUE on Graphify-Labs/graphify, not a pull request (see D-002)
- `[ ]` T10.3 | Cite issues #3180 and #1070, which both ask for exactly this
- `[ ]` T10.4 | Include the `run_language_resolvers` casefold as a separate small fix
- `[ ]` T10.5 | Expect to carry the registry indefinitely; plan accordingly

### `[ ]` T32 | P05-S001 (rr-s1) Security and crash safety — H4 E6 L1 L2 L4 N4

- `[ ]` T32.1 | S1.1 Red tests: alias bomb, self-alias, deep nesting, large schema, bad manifest sections
- `[ ]` T32.2 | S1.2 H4/E6 memoised _matches + per-document try
- `[ ]` T32.3 | S1.3 L1 RecursionError fallback, L2 edge-key sets, N4 bisect line numbers
- `[ ]` T32.4 | S1.4 L4 manifest validation never raises; lower-case suffix keys
- `[ ]` T32.5 | S1.5 Stage close: hub §3 checks; move findings to cc-CR000.002

### `[ ]` T33 | P05-S002 (rr-s2) Repo and CI hygiene — M7 M8 E9 M9 M10 N6

- `[ ]` T33.1 | S2.1 M7 restore publish/release-graph workflows + guard lines
- `[ ]` T33.2 | S2.2 M8/E9 CI triggers (autolisp, lang-*, rr-*, v* tags) + bandit graphify_lang
- `[ ]` T33.3 | S2.3 M9 deletions per D3 (git-sp.ps1 stays) + reference repoint
- `[ ]` T33.4 | S2.4 M10 delete install-mcp.sh; N6 T9.5 text
- `[ ]` T33.5 | S2.5 Ask owner, push rr-s2, read CI
- `[ ]` T33.6 | S2.6 Stage close

### `[ ]` T34 | P05-S003 (rr-s3) Shared plugin core — E2 L5 H2 M4 M6 E7 L3 E8 N3 L12

- `[ ]` T34.1 | S3.1 Red tests: same-stem lsp/mnl/dcl, vba same-stem, portable file ids, post_file prefix
- `[ ]` T34.2 | S3.2 graphify_lang/_common.py; move bmake
- `[ ]` T34.3 | S3.3 Move ecschema, astgrep, vba, autolisp, cc_kb (one commit each)
- `[ ]` T34.4 | S3.4 H2/M4 complete; case_008 id-form note
- `[ ]` T34.5 | S3.5 M6 (D1), N3, L3/E8, L12
- `[ ]` T34.6 | S3.6 Stage close; E7 closed per D1

### `[ ]` T35 | P05-S004 (rr-s4) Build coherence — H1 E3 E5 H3 L9 L11 M2 E1

- `[ ]` T35.1 | S4.1 E5 parity test + H3/L9/L11/M2 red tests
- `[ ]` T35.2 | S4.2 H1 watch.py context_fields registry hook + [resolve] context_fields
- `[ ]` T35.3 | S4.3 H3/L9 pure augments; cargo and cc-kb resolvers
- `[ ]` T35.4 | S4.4 L11 normpath ruleDirs
- `[ ]` T35.5 | S4.5 M2/E1 plugin-set fingerprint in cache namespace; update learning 1484
- `[ ]` T35.6 | S4.6 Stage close (E3 open until PR draft)

### `[ ]` T36 | P05-S005 (rr-s5) Registry robustness — M1 E4 M5 M3 L6 L7 L8 L10 L13 N5

- `[ ]` T36.1 | S5.1 Red tests for each finding
- `[ ]` T36.2 | S5.2 M1 isolation, L7 one group, M5 GRAPHIFY_LANG_PATH, E4 lang list --check
- `[ ]` T36.3 | S5.3 M3 watch.py claimed-path hooks
- `[ ]` T36.4 | S5.4 L6, L8, L10, N5
- `[ ]` T36.5 | S5.5 Stage close

### `[ ]` T37 | P05-S006 (rr-s6) Tests, docs, release lang.4 — M12 M11 N1 N2 PR drafts

- `[ ]` T37.1 | S6.1 M12 corpus marker + checked-in corpus samples
- `[ ]` T37.2 | S6.2 M11 README, N1 CLAUDE.md symbols, N2 plan statuses
- `[ ]` T37.3 | S6.3 Upstream PR drafts (H1/E3, M3, L13, registry lookups)
- `[ ]` T37.4 | S6.4 Release v0.9.67+lang.4 + pipx install (README form)
- `[ ]` T37.5 | S6.5 Rebuild 12 graphs; incremental check on real corpora
- `[ ]` T37.6 | S6.6 Close-out: CR file, DONE statuses, learnings, ask owner then push