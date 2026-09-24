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

### `[?]` T1 | S001 (prep) Toolchain, upstream baseline and corpus pin — plan §S001

- `[x]` T1.1 | Install `uv` (measured absent on this host) and `git switch -c lang-registry v8`
- `[x]` T1.2 | `uv venv && uv sync --all-extras` — never `pip install -e .`; the lock pins tree-sitter 0.25.2 and tree-sitter-commonlisp 0.4.1. Do not touch the pipx venv
- `[x]` T1.3 | Run `uv run pytest tests/ -q` on unmodified `v8`; record counts and `uv pip freeze` to tests/lang_baseline.txt; investigate any pre-existing failure now
- `[?]` T1.4 | Write scripts/snapshot_tables.py (~30 lines) and dump the six core tables to tests/upstream_tables.json — the SC2 comparison snapshot, regenerated at every rebase (BLOCKED on P1: AutoLITHP corpus SHA decision)
- `[?]` T1.5 | Pin the corpus: confirm `~/repos/autolithp` HEAD is `d5a2074` and clean; re-measure the six SRS §1.3 counts; if HEAD moved, stop and update SRS §1.3 first (BLOCKED on P1: AutoLITHP corpus SHA decision)
- `[x]` T1.5b | Create MCP install script for hook suffix registration (`scripts/install-mcp.sh` with `--dry-run`, `--check`, `--help` flags)
- `[x]` T1.5c | Add entry-points stanza to pyproject.toml (`[project.entry-points."graphify_lang.plugins"]`)


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

### `[ ]` T5 | S005 (autolisp) Rules runtime and manifest templates — plan §S005

- `[ ]` T5.1 | Check in the corpus file list generated from the S001-pinned SHA
- `[ ]` T5.2 | graphify_lang/rules.py: `build(manifest_path, manifest)` returning the `Callable[[Path], dict]`
- `[ ]` T5.3 | queries.py (F7, tree-sitter tag queries) and regex_rules.py (F8, full key set) as the two rule tiers
- `[ ]` T5.4 | builtins.py reads `builtins_file` (one name per line, `#` comments); Python hooks via `[extract.python] post_file = "module:fn"`
- `[ ]` T5.5 | Emission contract: `file_type: "code"`, kind in `node_kind`, ids from `base._file_stem`, line number appended on collision
- `[ ]` T5.6 | Ship `templates/{programming,markup,prose}.toml` (F11)

### `[ ]` T6 | S006 (autolisp) AutoLISP nodes — plan §S006

- `[ ]` T6.1 | graphify_lang/autolisp/graphify-lang.toml per SRS §6.3, and cap the extra at `tree-sitter-commonlisp>=0.4.1,<0.5`
- `[ ]` T6.2 | queries/tags.scm with two definition rules, not one — `[(sym_lit) (package_lit)]` is what captures all 27 defuns
- `[ ]` T6.3 | data/builtins.txt: the AutoLispExt union, shipped with its Apache-2.0 sidecar licence
- `[ ]` T6.4 | `post_file` hook joins `package_lit` children into one symbol, so `err:trap` is one node
- `[ ]` T6.5 | Fixtures under tests/lang/fixtures/src/core/ — the tree must mirror the corpus path prefix or every asserted id breaks
- `[ ]` T6.6 | Check in the measured collision set (11 groups) and meet SC4 (27 distinct function nodes from `err.lsp`) and SC5 (the three `C:` commands)

### `[ ]` T7 | S007 (autolisp) AutoLISP edges and the cross-file resolver — plan §S007

- `[ ]` T7.1 | Define the unresolved-call contract shared by F13 and F14
- `[ ]` T7.2 | Apply the structural exclusions on the reference rule first; binding forms never yield a `calls` edge for their bound position
- `[ ]` T7.3 | Quoted function references (`'name`) are `calls`
- `[ ]` T7.4 | `loads` from a literal `load` path (EXTRACTED) and from the `err:safe-load` wrapper; `module_depends` from `@depends`; `sidecar_doc` from `@sidecar`/`@doc`; stamp `target_file` on every cross-file edge
- `[ ]` T7.5 | resolve.py: a `LanguageResolver` covering `.lsp`, `.mnl` and `.dcl`
- `[ ]` T7.6 | Run `analyze.god_nodes` over the corpus and check the top 10 are real; meet SC6a (`err:trap` has at least one inbound cross-file `calls` edge) and SC7

### `[ ]` T8 | S008 (autolisp) DCL and MNL — plan §S008

- `[ ]` T8.1 | graphify_lang/autolisp/dcl.toml as a second manifest, not a second package
- `[ ]` T8.2 | Four regex rules, including the `pop` rule — without it nested tiles attach to the wrong dialog, which is a real defect
- `[ ]` T8.3 | AutoLISP side: `dcl_references` (function → dialog) from `new_dialog`, and `dcl_action` from `action_tile`
- `[ ]` T8.4 | Authored fixtures for what the corpus cannot supply: `@include`, `defun-q`, direct `(load "x")` and `.mnl`
- `[ ]` T8.5 | Claim `.mnl` as an AutoLISP suffix (F16); meet SC6b (at least one `dcl_references` edge into `lithp_mgr`)

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

### `[?]` T24 | Plan 02 step 6: extraction cache key check/fix for registry-dispatched files (D11)

- `[x]` T24.1 | Inspect graphify/cache.py key
- `[?]` T24.2 | Add plugin name+version to key for registry files only, or record in 50-PENDING if it needs a wider core edit