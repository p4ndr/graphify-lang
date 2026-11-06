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
- `[x]` T9.5 | The MCP registration install script (scripts/install-mcp.sh); deleted in plan 05 S2.4 (M10): it wrote a config key nothing reads, so no manual run is needed
- `[x]` T9.6 | Take the SRS §1.3 tier-2 recorded measurements and write them into the documents (TODO: add to docs)
### `[ ]` T10 | S010 (registry) Upstream proposal — plan §S010

- `[ ]` T10.1 | Produce the artefact: `git diff v8...lang-registry -- graphify/`
- `[ ]` T10.2 | Open an ISSUE on Graphify-Labs/graphify, not a pull request (see D-002)
- `[ ]` T10.3 | Cite issues #3180 and #1070, which both ask for exactly this
- `[ ]` T10.4 | Include the `run_language_resolvers` casefold as a separate small fix
- `[ ]` T10.5 | Expect to carry the registry indefinitely; plan accordingly

### `[ ]` T39 | cc-kb incremental asymmetry: a changed doc gets a `cites` edge whose reverse an unchanged doc already holds (pair dedupe is undirected; the reverse edge is not in the resolver's all_edges); measured ~/.claude cc-IP000.012 -> cc-CR000.001 (case_008 §6)

### `[ ]` T40 | Plan 06 S1: AutoLISP baseline numbers (INFERRED share, duplicate labels, unlinked globals, module_depends)

- `[ ]` T40.1 | Extend tools/measure_autolisp.py
- `[ ]` T40.2 | Run on ust copy and autolisp-htt; write numbers into plan §5

### `[ ]` T41 | Plan 06 S2: shadow-copy pairing, shadow_of, pick_by_prefix drop, report section

- `[ ]` T41.1 | Pairing + shadow_of marking + pick_by_prefix drop
- `[ ]` T41.2 | Report section with .graphifyignore lines
- `[ ]` T41.3 | Tests: logs copy, commit-time pick, tie, under-80% not shadow
- Needs: T40

### `[ ]` T42 | Plan 06 S3: query ranking, god_nodes and get_neighbors skip shadows

- `[ ]` T42.1 | Skip shadow_of nodes in start ranking, god_nodes, get_neighbors ambiguity
- `[ ]` T42.2 | Rebuild ust copy in scratch; verify one ust:rget god node, one get_neighbors answer
- Needs: T41

### `[ ]` T43 | Plan 06 S4: query miss line and staleness line (CLI and MCP)

- `[ ]` T43.1 | Miss line for symbol-shaped terms with no exact label
- `[ ]` T43.2 | built_at_commit vs HEAD staleness line
- `[ ]` T43.3 | Tests for both paths

### `[ ]` T44 | Plan 06 S5: global read/write edges and load/autoload edges

- `[ ]` T44.1 | reads_global / writes_global edges
- `[ ]` T44.2 | load / autoload depends refs with unresolved-load report line
- `[ ]` T44.3 | Tests incl. variable argument and unresolved name

### `[ ]` T45 | Plan 06 S6-S8: re-measure, hand-offs, release wheel

- `[ ]` T45.1 | S6 re-measure ust and autolisp-htt against §5
- `[ ]` T45.2 | S7 hand-off texts + PENDING items
- `[ ]` T45.3 | S8 bump version, tag, build wheel, pipx install, verify
- Needs: T41, T42, T43, T44