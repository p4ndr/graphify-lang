---
TEMPLATE-VERSION: 1.0.0
---

# Implementation Plan

<!-- TEMPLATE ZONE START — Do not edit between TEMPLATE markers -->

| Field | Value |
|-------|-------|
| ID | IP000.001 |
| Date | 2026-09-08 |
| Status | Draft |
| Repository | `~/repos/graphify-lang` (fork of `Graphify-Labs/graphify`, base branch `v8` = `a5dcc70`) |
| SRS Reference | `cc-RS000.001.md` v2 (adjudication log `cc-RS000.001.squad-check.md`) |
| Author | ag-build |
| Version | v1 |

---

## Overview

Ship a language-extension layer for graphify in two commit groups, and an
AutoLISP/DCL plugin on top of it.

The whole plan is shaped by one constraint: **`git diff v8...lang-registry
-- graphify/` must be an artefact an upstream maintainer can read and
apply.** Everything generic goes on the `lang-registry` branch and touches
exactly four files under `graphify/`; everything AutoLISP-specific goes on
`autolisp`, branched off it. Nothing on `lang-registry` mentions AutoLISP.

Three branches, per SRS §4.2 Workflow 5:

| Branch | Off | Carries | Ends at |
|:-------|:----|:--------|:--------|
| `v8` | `upstream/v8` | nothing of the fork's; only ever fast-forwards | — |
| `lang-registry` | `v8` | `graphify/lang_registry.py`, the three core call sites, `tests/test_lang_registry.py`, the `ARCHITECTURE.md` row, and the fork's CI/release/pytest infrastructure | S004 |
| `autolisp` | `lang-registry` | `graphify_lang/`, `tests/lang/`, packaging, corpus fixtures | S009 |

**Format note.** This is a single self-contained plan rather than a hub plus
ten spoke files. Each section below is ~60 lines and already carries
everything an executor needs (objective, prerequisites, tasks, files,
acceptance, verification, commit boundary), so ten extra files would add
churn and no capability. Split to spokes only if sections are to be executed
concurrently by separate instances.

---

## Section Index

| Section | Group | Status | Description | Gated by |
|---------|-------|--------|-------------|----------|
| S001 | prep | Pending | Toolchain, upstream baseline, SC2 snapshot, corpus SHA pin | — |
| S002 | registry | Pending | Fork CI, release safety, perf marker | — |
| S003 | registry | Pending | `lang_registry.py`: manifest schema, discovery, precedence | — |
| S004 | registry | Pending | Core merge: three call sites, lazy dispatch, thunked resolver | — |
| S005 | autolisp | Pending | Rules runtime (query + regex + builtins + hooks), templates | — |
| S006 | autolisp | Pending | AutoLISP nodes | — |
| S007 | autolisp | Pending | AutoLISP edges and cross-file resolver | — |
| S008 | autolisp | Pending | DCL and MNL | — |
| S009 | autolisp | Pending | Packaging, hook/watch, recorded measurements | **Q7**, **Q9** (two steps only) |
| S010 | registry | Pending | Upstream proposal (F19, Should Have) | — |

Open questions carried from SRS §7.1. Only S009 touches them:

| Q | Question | What it gates | What it does **not** gate |
|---|----------|---------------|---------------------------|
| Q7 | Which build do the agents reach (installed hook, MCP server)? | S009 step 6 (installed-hook manual run, MCP registration) | SC12's in-process assertion, which needs no install |
| Q8 | First `type = "prose"` corpus (F20)? | nothing in this plan — F20/F21/F22 are roadmap | — |
| Q9 | Is the global `.lsp` claim an accepted loss? | S009 step 5 (the shipped `[project.entry-points]` default) | every measurement S005–S008 makes: development and tests discover the plugin through `GRAPHIFY_LANG_PATH`, which is deterministic and needs no packaging |

---

## Cross-Cutting Concerns

### The never-edit list (mechanically checked, not trusted)

Forbidden by `.claude/CLAUDE.md` and SRS F25: any existing language
extractor, `graphify/extractors/engine.py`, `graphify/extractors/
resolution.py`, any upstream test file, and any hand-written entry in
`_DISPATCH`, `CODE_EXTENSIONS` or `_HOOK_SOURCE_EXTS`.

Three guard commands. **Every section's verification block runs `guard-all`.**

```bash
# guard-core: exactly four files under graphify/ may differ from v8.
git diff --name-only v8...HEAD -- graphify/ | sort > /tmp/g.txt
printf 'graphify/cli.py\ngraphify/detect.py\ngraphify/extract.py\ngraphify/lang_registry.py\n' | diff -u - /tmp/g.txt

# guard-tests: no upstream test file may differ from v8.
test -z "$(git diff --name-only v8...HEAD -- tests/ \
  | grep -Ev '^tests/(lang/|test_lang_registry\.py$)')"

# guard-tables: no literal suffix added by hand to any of the three tables.
git diff v8...HEAD -- graphify/detect.py graphify/cli.py \
  | grep -E "^\+.*'\.(lsp|dcl|mnl)'" && echo "FAIL: hand-added suffix" && exit 1 || true
```

`guard-all` = the three above, in order. A section is not complete until it
passes.

### Error handling

Every plugin-side failure returns
`{"nodes": [], "edges": [], "error": "<text>"}` where `<text>` contains
`not installed` (dependency absent) or `failed to load` (present but
broken) — the two substrings `_DEP_MISSING_MARKER` and
`_DEP_LOAD_FAILED_MARKER` at `graphify/extract.py:5763-5764`, matched by
the #1745 warning at `:6365-6370`. Without them a failure is completely
silent, because returning a callable from `_get_extractor` also suppresses
the #1689 'no AST extractor' warning (SRS F5, RV-7).

Each of the three core call sites is individually `try`-wrapped so a
registry exception degrades to one logged line. `graphify.cli` is the only
module `graphify hook` imports, so an uncaught exception there breaks every
agent tool call in every repository.

### Logging and observability

The registry logs its own report through `logging` at `INFO` — plugin name,
source tier, suffixes, overrides, runtime, and the fork build identity
(`0.9.55+lang.<n>`). **This adds no core line**: the report is emitted from
inside `lang_registry.load()`, not from `extract.py`, which is how F26's
Must-Have half stays clear of a fourth core edit. The override notice
(`graphify-lang: <name> overrides <suffix> (was <extractor>)`) is logged
once per process at `WARNING`.

### Testing strategy

- `pytest tests/ -q` is the gate for every section and must exit 0 with the
  S001 baseline counts, no upstream test edited.
- Perf tests carry `@pytest.mark.perf` and are deselected by
  `addopts = "-m 'not perf'"` (S002), so wall-clock numbers never make the
  gate non-deterministic.
- **Anything comparing "with plugin" against "without plugin" is a
  `subprocess.run([sys.executable, "-c", ...])`, never an in-process
  assertion.** The three merges are irreversible in-process:
  `CODE_EXTENSIONS.update()` mutates the object `watch.py:279` aliases,
  `_HOOK_SOURCE_EXTS += ...` rebinds a module global, and
  `_WATCHED_EXTENSIONS` is a one-time union snapshot at watch import.
  `lang_registry.reset()` clears the discovery cache only.
- Fixture trees mirror the corpus path prefix
  (`tests/lang/fixtures/src/core/err.lsp`), and every fork test calls
  `extract(paths, root=fixture_root)`. `_file_stem` is the whole relative
  path minus suffix, so a flat fixture yields `err_*` where the corpus
  yields `src_core_err_*` and every asserted id silently fails to transfer.
- Four behaviours have **zero** corpus instances and are carried by
  authored fixtures only: `defun-q`, direct `(load "x")`, DCL `@include`,
  and `.mnl`.

### Naming conventions

Node ids come from `graphify.extractors.base._file_stem` for the symbol
prefix and `graphify.extract._file_node_id` for the file node. On collision
within a file, append the definition's line number — the recipe
`extractors/markdown.py` already uses for repeated headings. Node kinds go
in `node_kind` with `file_type: "code"`; `file_type` is a closed enum
(`build.py:856` rewrites anything else to `concept`). Relations are
unvalidated and open.

---

## S001 — Toolchain, upstream baseline, corpus pin

**Group** prep · **Branch** `lang-registry` (created here) · **Gated by** nothing

**Objective.** Produce SC1's oracle. Until the upstream suite has been run
on unmodified `v8`, any later failure or skip is unattributable.

**Prerequisites.** None. This is the first task in the project.

**Tasks.**

1. Install `uv` (measured absent: `command -v uv` returns nothing).
2. `git switch -c lang-registry v8`.
3. `uv venv && uv sync --all-extras`. **Not** `pip install -e .`: pip
   re-resolves from PyPI within the `pyproject.toml` ranges, while CI
   installs from the committed lock, which pins `tree-sitter 0.25.2`
   (`uv.lock:4473-4474`) and `tree-sitter-commonlisp 0.4.1` (`:4564-4565`).
   The user's pipx venv `~/.local/share/pipx/venvs/graphifyy` is **not
   touched**.
4. Run `uv run pytest tests/ -q` on unmodified `v8`. Record pass/fail/skip
   counts and `uv pip freeze` output to `tests/lang_baseline.txt`.
   Investigate any pre-existing failure before proceeding — it must be
   known, not discovered later.
5. Write `scripts/snapshot_tables.py` (fork-owned, ~30 lines): imports
   `graphify.extract`, `graphify.detect`, `graphify.cli`, `graphify.watch`,
   `graphify.resolver_registry` and dumps the six tables of SRS §1.1 as
   sorted JSON — `_DISPATCH` keys plus values by `__name__`,
   `_EXTRA_FOR_EXTENSION`, `CODE_EXTENSIONS`, `_WATCHED_EXTENSIONS`,
   `_HOOK_SOURCE_EXTS`, `[r.name for r in registered_resolvers()]`. Run it
   on `v8` into `tests/upstream_tables.json`. This is SC2's comparison
   snapshot and is regenerated at every rebase.
6. **Pin the corpus.** Verify `~/repos/autolithp` HEAD is `d5a20743b007431521c4f9a0507560d5feb94b27` and the
   tree is clean. Re-measure the six SRS §1.3 counts (81 `.lsp`, 4,027
   defuns, 52 `C:`, 3 `.dcl`, 8 dialogs, 3.1 MiB). If HEAD has moved,
   **stop and update SRS §1.3 before continuing** — the criteria are
   defined against a SHA, not against `HEAD`. The checked-in file list is
   generated in S005 (it belongs on the `autolisp` branch).
**Files.** `tests/lang_baseline.txt`, `tests/upstream_tables.json`,
`scripts/snapshot_tables.py`. No `graphify/` file.

**Acceptance.** Baseline counts recorded; snapshot exists; corpus SHA
confirmed.

**Verification.**
```bash
uv run pytest tests/ -q                      # matches tests/lang_baseline.txt
uv run python scripts/snapshot_tables.py | diff -u tests/upstream_tables.json -
git -C ~/repos/autolithp rev-parse --short HEAD   # d5a2074
guard-all
```

**Commit.** `chore(lang): pin upstream test baseline, table snapshot and corpus SHA`

---

## S002 — Fork CI and release safety

**Group** registry · **Branch** `lang-registry` · **Gated by** nothing

**Objective.** Give every later section a CI gate, and stop the inherited
release workflows from firing on a fork that does not own the PyPI name.
This comes second, not last, so S003 onward are verified by machine.

**Prerequisites.** S001.

**Tasks.**

1. Add `.github/workflows/graphify-lang-ci.yml` — a **new file**;
   `ci.yml` stays unedited. It carries:
   - `on: push: branches: ['**']` plus `pull_request`. The inherited
     `ci.yml:4-7` triggers only on push to `v1`…`v8`/`main` and PRs to
     those, so no fork feature-branch push matches either trigger and SC1
     would run nowhere but the terminal.
   - `permissions: contents: read` at the top level. `ci.yml` declares no
     `permissions:` block at any level, so its jobs take the repository's
     default token scope.
   - `uv sync --locked`, **not** `--frozen`. `--frozen` syncs from the lock
     without checking it against `pyproject.toml`, so a dependency added
     and not re-locked is simply absent and surfaces as an unrelated
     `ModuleNotFoundError` inside a plugin test; `--locked` fails with
     "the lockfile needs to be updated" and names the real cause.
   - matrix `ubuntu-latest` × 3.10 / 3.12 / 3.13, plus `windows-latest` ×
     3.12. Windows is not optional: it is where `Path.glob` ordering and
     manifest path handling diverge. The registry is stdlib-only, so both
     added legs are cheap.
   - one extra leg `uv run --with 'tree-sitter==0.23.*' pytest tests/lang -q`
     pinned to the py-tree-sitter floor, so F7's `QueryCursor(Query(...))`
     shim for 0.23/0.24 is actually executed. It needs no second lock.
     (This leg is a no-op until S005 creates `tests/lang/`; add it now and
     let it collect nothing.)
2. Add `jobs.<id>.if: github.repository == 'Graphify-Labs/graphify'` to
   every job in `.github/workflows/publish.yml` and
   `.github/workflows/release-graph.yml`. `publish.yml:13-15` fires on
   `release: published` and uploads to `pypi.org/project/graphifyy/`
   (`:26-28`, `:54-55`); `release-graph.yml:3-6` fires on the same event
   holding `contents: write` (`:11-12`). SRS §1.5 puts PyPI publication out
   of scope, so without the guard the fork's first `gh release create` runs
   both. One line each, rebase-cheap.
3. Add `addopts = "-m 'not perf'"` and a `perf` marker registration under
   the existing `[tool.pytest.ini_options]` (`pyproject.toml:146-147`,
   which currently has no `addopts`).
4. Do **not** touch `pyproject.toml:7` `version`. A rebase adopts
   upstream's next number, and `publish.yml:43` greps `^version = `
   verbatim for its tag guard. Fork identity surfaces through the registry
   report instead (Cross-Cutting → Logging). Fork releases are git tags
   only, `0.9.55+lang.<n>`.

**Files.** `.github/workflows/graphify-lang-ci.yml` (new),
`.github/workflows/publish.yml`, `.github/workflows/release-graph.yml`,
`pyproject.toml`.

**Acceptance.** A push to `lang-registry` runs the fork workflow; the two
release workflows are inert on `p4ndr/graphify-lang`.

**Verification.**
```bash
uv run pytest tests/ -q            # unchanged from baseline
uv run pytest tests/ -q -m perf    # collects 0 (no perf tests yet), exits 5, not 1
python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" .github/workflows/*.yml
guard-all
```

**Commit.** `ci(lang): fork-only workflow, release guards, perf marker`

---

## S003 — Registry: manifest schema, discovery, precedence

**Group** registry · **Branch** `lang-registry` · **Gated by** nothing

**Objective.** `graphify/lang_registry.py` parses and ranks manifests.
**No core file is edited in this section** — the registry is inert until
S004 wires it up, which keeps the two changes separately reviewable.

**Prerequisites.** S001, S002.

**Tasks.** Implements SRS F1, F2, F3.

1. `LanguageManifest`, a frozen dataclass, with `from_toml(path)`. Loader
   is `try: import tomllib / except ImportError: import tomli as tomllib`
   — three lines; `tomli` is already a dependency below 3.11
   (`pyproject.toml:16`). Add a test asserting **which** module was
   imported, because the 3.10 CI leg is the only one exercising that branch.
2. Schema v1 key set, complete (SRS F1): top-level `schema`; `[language]`
   `name`, `type`, `suffixes`, `overrides`, `hook_suffixes`, `priority`,
   `case_insensitive`; `[grammar]` `kind`, `module`, `language_fn`,
   `extra`, `version`; `[extract]` `runtime`, `builtins_file`,
   `builtins_prefixes`, `queries`; `[[rule]]`; `[extract.python]`;
   `[[node_kind]]`; `[[edge_kind]]`. **No `filenames` key** — `_DISPATCH`
   is keyed by suffix and filename routing exists only as hard-coded
   special cases inside `_get_extractor` (`extract.py:5866-5875`), so
   honouring it would need a fourth core edit.
3. Validation, each failure a one-line reason and a rejected manifest, not
   an exception: unknown `schema`; unknown keys (warning only); a
   `[grammar] version` that does not match the installed grammar's
   version; **and any suffix already in `detect.DOC_EXTENSIONS`**.
   The last one matters more than it looks: `classify_file` tests
   `CODE_EXTENSIONS` (`detect.py:517`) *before* `DOC_EXTENSIONS` (`:526`),
   so a plugin claiming `.md` would reclassify every markdown file in
   every repository that venv graphs and take it off `extract_markdown`,
   globally and silently.
4. Discovery, in this fixed tier order: entry point group
   `graphify.languages`; then `~/.graphify/languages/*/graphify-lang.toml`;
   then `GRAPHIFY_LANG_PATH` entries in listed order. **Each directory tier
   is sorted by manifest path.** `Path.glob` yields `os.scandir` order —
   creation order on ext4, name order on NTFS — so without the sort F3's
   tie-break is a coin toss that passes on Linux and fails on Windows.
   There is **no project-local `./.graphify/languages/` tier** (SRS §1.5).
5. `GRAPHIFY_LANG_DISABLE=1` disables discovery entirely. Cache per
   process; `reset()` clears the cache **only** — document in the
   docstring that merged tables are not restored.
6. Precedence: a built-in suffix is taken only when listed in `overrides`,
   logged once; between plugins higher `priority` wins; a tie keeps the
   first discovered, which tasks 4's ordering makes deterministic.
7. `tests/test_lang_registry.py`: schema round-trip, each validation
   rejection, tier order, the sorted tie-break (two manifests, equal
   `priority`), the disable switch, and the `tomllib`/`tomli` assertion.

**Files.** `graphify/lang_registry.py` (new),
`tests/test_lang_registry.py` (new).

**Acceptance.** SRS F1–F3 implemented; registry importable and inert.

**Verification.**
```bash
uv run pytest tests/ -q
uv run pytest tests/test_lang_registry.py -q
uv run python scripts/snapshot_tables.py | diff -u tests/upstream_tables.json -   # still identical
guard-all
```

**Commit.** `feat(lang): manifest schema, discovery and precedence`

---

## S004 — Core merge: call sites, lazy dispatch, thunked resolver

**Group** registry · **Branch** `lang-registry` · **Gated by** nothing

**Objective.** Three one-line call sites, and the dispatch machinery behind
them. **This section ends the registry group: `git diff v8...lang-registry
-- graphify/` is the F19 upstream artefact from here on.**

**Prerequisites.** S003.

**Tasks.** Implements SRS F4, F5, F6; satisfies SC2, SC3, SC13, SC14.

1. `graphify/detect.py`, immediately after `CODE_EXTENSIONS` (`:44`):
   `CODE_EXTENSIONS.update(lang_registry.code_suffixes())`. `watch.py`
   computes `_WATCHED_EXTENSIONS` as a union after this import, so it needs
   no edit at all.
2. `graphify/extract.py`, immediately after `_EXTRA_FOR_EXTENSION`
   (`:5740`):
   `lang_registry.apply_dispatch(_DISPATCH, _EXTRA_FOR_EXTENSION, register_language_resolver)`.
   `collect_files` reads `set(_DISPATCH.keys())` at call time, so it sees
   plugin suffixes with no edit and both upstream parity oracles still pass.
   `_DISPATCH` stays a plain mutable `dict` — six upstream tests call
   `monkeypatch.setitem` on it.
3. `graphify/cli.py`, immediately after `_HOOK_SOURCE_EXTS` (`:71`):
   `_HOOK_SOURCE_EXTS += lang_registry.hook_suffixes()`. **`hook_suffixes()`
   returns `tuple[str, ...]`, lowercase.** `_HOOK_SOURCE_EXTS` is a tuple
   (`:71-75`), so returning a list or set raises `TypeError`; and
   `cli.py:881` compares lowercased tails, so any other case never matches.
4. Wrap each of the three individually so an exception degrades to one
   logged line. All three run at module import outside any `try`, and
   `graphify.cli` is the only module `graphify hook` imports.
5. `apply_dispatch` inserts a per-suffix callable with a stable `__name__`
   that imports the plugin runtime on **first call**, then delegates. On
   runtime import failure it returns the F5 error dict carrying
   `not installed` or `failed to load`.
6. **Thunk the resolver.** `LanguageResolver` is a frozen dataclass holding
   a concrete `resolve` callable (`resolver_registry.py:29-40`), so
   constructing one eagerly would import the plugin's `resolve.py`, the
   plugin package and any grammar it loads on every `graphify` run,
   including corpora with no `.lsp` file. Register a `LanguageResolver`
   whose `resolve` is a thunk that imports on first call;
   `run_language_resolvers` already try/excepts each pass (`:78-83`).
7. **Register case variants.** `run_language_resolvers` gates on
   `{p.suffix for p in paths}` with no casefold (`:76`), while
   `collect_files` (`extract.py:7609`) and `_get_extractor` (`:5881`) both
   fall back to `.lower()`. Register at minimum `.lsp` and `.LSP` per
   claimed suffix. Record the residual mixed-case gap (`Err.Lsp`); the
   casefold itself goes into F19.
8. Ship the `python` runtime inside `lang_registry.py` — it imports
   `[extract.python] extractor` and optional `resolver` by `module:attr`.
   `[extract] runtime` names a **module**; the registry calls its
   module-level `build(manifest_path, manifest) -> (extract, resolver)`.
9. Add one row to `ARCHITECTURE.md`'s `## Module responsibilities` table:
   `lang_registry.py`, `load()`, `registered_languages()`.
   `tests/test_architecture_doc.py` parses only that table and asserts
   `hasattr` per named symbol, so the row must name symbols that exist.
10. Tests, all subprocess-based where they compare states: SC2 (six tables
    vs `tests/upstream_tables.json` under `GRAPHIFY_LANG_DISABLE=1`), SC3
    (a stub plugin on `GRAPHIFY_LANG_PATH` dispatched, collected,
    classified and hook-matched), SC13 (unknown `schema`, and a
    non-importable runtime module: same counts as no plugin, all three
    modules still import, exactly one warning line whose text contains the
    F5 substrings), SC14 (no `graphify_lang` in `sys.modules` after
    importing `graphify.extract`/`graphify.cli`; present after one dispatch).

**Files.** `graphify/lang_registry.py`, `graphify/detect.py`,
`graphify/extract.py`, `graphify/cli.py`, `ARCHITECTURE.md`,
`tests/test_lang_registry.py`.

**Acceptance.** SC2, SC3, SC13, SC14 pass. `guard-core` shows exactly four
files. Core diff is three one-line call sites plus the new module.

**Verification.**
```bash
uv run pytest tests/ -q                        # equals the S001 baseline
uv run pytest tests/test_lang_registry.py -q   # SC2, SC3, SC13, SC14
uv run pytest tests/test_architecture_doc.py tests/test_extract.py tests/test_extractors_registry.py -q
git diff --stat v8...lang-registry -- graphify/   # 4 files; 3 one-line additions + 1 new
guard-all
```

**Commit.** `feat(lang): merge registered languages into the core tables at import`
→ **the `lang-registry` branch is complete. Create `autolisp` from it:**
`git switch -c autolisp lang-registry`

---

## S005 — Rules runtime and templates

**Group** autolisp · **Branch** `autolisp` · **Gated by** nothing

**Objective.** Turn a manifest into a `Callable[[Path], dict]`. Generic
code, but fork-owned (`graphify_lang/` is not an upstream candidate), so it
lives on this branch.

**Prerequisites.** S004.

**Tasks.** Implements SRS F7, F8, F9, F10, F11.

1. **Check in the corpus file list.** From the S001-pinned SHA, generate
   `tests/lang/corpus_files.txt` — the 80 `.lsp` and 3 `.dcl` paths under
   `src/`, `tests/`, `Import-Refactor/`, `build/`. This is SC5's oracle and
   the reason no criterion writes to `~/repos/autolithp`. Record `f7ab804`
   in the file's header comment.
2. `graphify_lang/rules.py`: module-level `build(manifest_path, manifest)`
   returning `(extract, resolver)`. `RuleSet` is the implementation detail
   behind it and is never addressed by the registry.
3. `graphify_lang/queries.py` — query rules (F7). `tags.scm` capture
   vocabulary (`@definition.<node_kind>`, `@name`, `@doc`,
   `@reference.<relation>`). Predicates `#eq?`, `#match?`, `#not-match?`,
   `#any-of?` **implemented in Python**: the C library does not run them.
   Target `QueryCursor(Query(lang, src)).captures(node)` (py-tree-sitter
   0.25) with the three-line shim for 0.23/0.24, exercised by S002's
   floor-pinned CI leg. Compile each query once per language per process.
4. `graphify_lang/regex_rules.py` — regex rules (F8) with the full key set:
   `pattern`, `name_group`, `node` or `edge`, `scope`
   (`push`/`pop`/`ref`/`set`), `edge_from_scope`, `target`, `multiline`,
   `suffix`. ctags-optlib semantics: `push` opens a scope owning following
   `ref` edges until `pop` or end of file.
5. `graphify_lang/builtins.py` — `builtins_file` (one name per line, `#`
   comments) plus `builtins_prefixes`, applied to `@reference` captures and
   regex `ref` edges, case-folded when `case_insensitive = true`. Applied
   **inside the plugin only**; never added to the shared
   `_LANGUAGE_BUILTIN_GLOBALS`, which is one union across every language
   and which upstream commit `462f89a` had to carve out precisely because
   it was too coarse.
6. Python hooks (F10): `[extract.python] post_file = "module:fn"` receiving
   `(path, tree, nodes, edges, manifest)` after rules run.
7. Node/edge emission contract: `file_type: "code"`, kind in `node_kind`,
   symbol prefix from `base._file_stem`, file node from
   `extract._file_node_id`, **line-number disambiguation on id collision**,
   `target_file` stamped on a cross-file edge only when the target exists
   on disk.
8. `tests/test_lang_registry.py` addition: assert `base._file_stem`,
   `extract._file_node_id` and the two `_DEP_*` markers exist with the
   expected shape, so an upstream rename fails on the fork's own test
   rather than at extraction time.
9. `graphify_lang/templates/{programming,markup,prose}.toml` (F11),
   commented field by field. `prose.toml` carries `section`/`reference`/
   `entity` marked "not yet implemented until F20".

**Files.** `graphify_lang/{__init__,rules,queries,regex_rules,builtins}.py`,
`graphify_lang/templates/*.toml`, `tests/lang/corpus_files.txt`,
`tests/lang/test_rules.py`, `tests/lang/test_templates.py`.

**Acceptance.** SC11. A synthetic two-rule manifest over a fixture yields
the expected nodes and edges under both query and regex tiers.

**Verification.**
```bash
uv run pytest tests/ -q
uv run pytest tests/lang -q
uv run --with 'tree-sitter==0.23.*' pytest tests/lang -q     # the shim
wc -l tests/lang/corpus_files.txt                            # 83
guard-all
```

**Commit.** `feat(lang): declarative rules runtime and manifest templates`

---

## S006 — AutoLISP nodes

**Group** autolisp · **Branch** `autolisp` · **Gated by** nothing

**Objective.** SC4 and SC5: real function, command, global and module nodes
from the corpus.

**Prerequisites.** S005.

**Tasks.** Implements SRS F12.

1. `graphify_lang/autolisp/graphify-lang.toml` per SRS §6.3: suffixes
   `.lsp`, `.mnl`; `overrides = [".lsp"]`; `case_insensitive = true`;
   `[grammar] module = "tree_sitter_commonlisp"`, `version = "0.4.1"`,
   `extra = "commonlisp"`; runtime `graphify_lang.rules`. **No `filenames`
   key.**
2. Cap the extra: `commonlisp = ["tree-sitter-commonlisp>=0.4.1,<0.5"]`
   (`pyproject.toml:97` currently has no specifier at all, unlike every
   grammar in `[project.dependencies]`). Re-run `uv lock` and commit it.
   The `[grammar] version` field then lets F1 reject a mismatch loudly
   instead of F5 reporting an empty extraction.
3. `queries/tags.scm`, **two** definition rules, not one:
   - `(defun_header function_name: [(sym_lit) (package_lit)] @name) @definition.function`
     — the whole AutoLISP gap closes on that one-token alternation;
     measured 27 definitions on `src/core/err.lsp` against 0 for upstream's
     `(sym_lit)`-only line.
   - `(list_lit . (sym_lit) @kw (#eq? @kw "defun-q") . [(sym_lit) (package_lit)] @name) @definition.function`
     — measured, `(defun-q q:legacy …)` parses as a **plain `list_lit`**
     with a `sym_lit` head: no `defun` node, no `defun_header`, so rule 1
     matches nothing for it. Relies on `#eq?` in Python (F7).
4. `data/builtins.txt` — union of AutoLispExt's `alllispkeys.txt` (2,730
   names) and the `functions` keys of `webHelpAbstraction.json`, lowercased
   and de-duplicated; plus `builtins_prefixes = ["vla-", "vlax-", "vlr-"]`,
   which alone collapses 2,189 of the 2,730. Ship
   `data/LICENSE.AutoLispExt` (Apache-2.0 text, upstream file names, commit
   SHA, and the transformation applied).
5. `extract.py` (`post_file`): join `package_lit` children into one symbol
   (`err` `:` `trap` → `err:trap`); split the parameter list on the `/`
   separator into params and locals; classify `C:`-prefixed names as
   `command` (case-insensitive); emit `global` nodes for top-level `setq`
   and every **odd** element of a multi-pair `setq`; parse the `;;;`
   header block for `@module`, `@prefix`, `@depends`, `@sidecar`, `@doc`;
   apply the **line-number collision disambiguation**.
6. Fixtures under `tests/lang/fixtures/src/core/`,
   `.../src/plugins/`, mirroring the corpus prefix. Add an authored
   `defun-q` fixture — the corpus has zero.
7. Check in the measured collision set (11 groups: 5 of the
   `pkg:name`/`pkg:_name` kind, 6 where `*error*` repeats in one file, 24×
   in `pltrn.lsp`) as a fixture, so SC4's `27` is derived from the recipe
   rather than asserted as a constant.

**Files.** `graphify_lang/autolisp/{__init__,extract}.py`,
`graphify-lang.toml`, `queries/tags.scm`, `data/builtins.txt`,
`data/LICENSE.AutoLispExt`, `tests/lang/fixtures/**`,
`tests/lang/test_autolisp_nodes.py`, `pyproject.toml`, `uv.lock`.

**Acceptance.** **SC4** (27 distinct function nodes from `err.lsp`;
`C:LITHP`, `C:LITHP-MGR`, `C:LITHP-INIT` as `command`; `err:trap` one node
keeping its first-seen spelling) and **SC5** (`node_kind in {function,
command}` within 2% of the grep over `corpus_files.txt`, both computed in
the same run).

**Verification.**
```bash
uv run pytest tests/ -q
GRAPHIFY_LANG_PATH=graphify_lang/autolisp uv run pytest tests/lang -q
uv run pytest tests/lang/test_autolisp_nodes.py -q -k "sc4 or sc5"
guard-all
```

**Commit.** `feat(autolisp): function, command, global and module nodes`

---

## S007 — AutoLISP edges and cross-file resolver

**Group** autolisp · **Branch** `autolisp` · **Gated by** nothing

**Objective.** SC6's first half and SC7: a call graph that survives a
god-node check.

**Prerequisites.** S006.

**Tasks.** Implements SRS F13, F14.

1. **The unresolved-call contract, which F13 and F14 share.** Per file the
   extractor emits a `calls` edge for every non-denylisted head symbol with
   the target **unresolved** and `confidence: AMBIGUOUS`. F14 promotes it
   to `EXTRACTED` and stamps `target_file` on binding. Edges still unbound
   after resolution are dropped. A per-file extractor cannot know whether a
   callee is defined in another file, so any other reading leaves F14 with
   no input and SC6 unreachable.
2. **Structural exclusions on the reference rule, before anything else.**
   Measured on `err.lsp`: 27 definitions against **298**
   `@reference.call` captures, whose names include `caller` and
   `caller-sym` — the heads of `defun` parameter lists, not callees. The
   rule also fires inside quoted data. So: no reference from a `list_lit`
   that is a direct child of `defun_header`, and none from within a
   `quoting_lit`. The denylist cannot filter these, because they are user
   symbols. **Re-measure the 298 afterwards** — it feeds SC7.
3. Binding forms never yield a `calls` edge for their bound position:
   `foreach`, `setq`, `lambda`, `defun`, `defun-q`, `cond`, `if`, `while`,
   `repeat`, `progn`, `quote`. `lambda` bodies are walked and attributed to
   the enclosing `defun`.
4. Quoted function references are `calls`: `'name` under
   `vl-catch-all-apply`, `apply`, `mapcar`, `function`, and the cdr of a
   quoted dotted pair whose car is a `:vlr-*` keyword.
5. `loads`: `load` with a literal path (`EXTRACTED`), the `err:safe-load`
   wrapper (14 call sites in the corpus), computed path (`INFERRED`),
   extension search `.vlx` → `.fas` → `.lsp`. The corpus has **zero**
   direct `(load "…")` sites, so the literal-path, computed-path and search
   clauses are carried by authored fixtures, not by the corpus.
6. `module_depends` from `@depends`; `sidecar_doc` from `@sidecar`/`@doc`;
   `command_invokes` from `(command "_.X" …)` strings with leading `_` and
   `.` stripped, to stub nodes.
7. `resolve.py`: a `LanguageResolver` named for `.lsp`, `.mnl`, `.dcl`
   **and their upper-case variants**, binding unresolved `calls` targets
   case-folded across files, resolving `loads` targets to file nodes, and
   stamping `target_file` only where the target exists on disk.
8. Run `analyze.god_nodes` over the corpus and check the top 10 are
   AutoLISP symbols. If COM names dominate, the `builtins_prefixes` filter
   is the lever — not `_LANGUAGE_BUILTIN_GLOBALS`.

**Files.** `graphify_lang/autolisp/{extract,resolve}.py`,
`tests/lang/fixtures/**` (authored `load` fixtures),
`tests/lang/test_autolisp_edges.py`.

**Acceptance.** **SC6a** (`err:trap` has ≥1 inbound `calls` edge from
another file) and **SC7** (top 10 god nodes by degree are AutoLISP
symbols, not Python helpers).

**Verification.**
```bash
uv run pytest tests/ -q
GRAPHIFY_LANG_PATH=graphify_lang/autolisp uv run pytest tests/lang -q
uv run python -m graphify_lang.tools.godnodes tests/lang/corpus_files.txt   # SC7, recorded
guard-all
```

**Commit.** `feat(autolisp): call, load, module and command edges plus the cross-file resolver`

---

## S008 — DCL and MNL

**Group** autolisp · **Branch** `autolisp` · **Gated by** nothing

**Objective.** SC6's second half. DCL is a second manifest, not a second
grammar block.

**Prerequisites.** S007.

**Tasks.** Implements SRS F15, F16.

1. `graphify_lang/autolisp/dcl.toml` — a **second manifest**,
   `[language] name = "dcl"`, `type = "markup"`, suffix `.dcl`,
   `[grammar] kind = "none"`, regex rules only. `[grammar]` is defined once
   per manifest and F15 needs `none` while AutoLISP needs `tree-sitter`, so
   one manifest cannot serve both and the rules runtime has no defined
   behaviour when a `.dcl` file reaches a Common Lisp parser.
2. Four regex rules: `dialog` node (`^\s*([A-Za-z_]\w*)\s*:\s*dialog\s*\{`,
   `scope = "push"`); a **`scope = "pop"` rule anchored to `^\}`**;
   `tile` node from `key = "..."` with `edge_from_scope = "contains"`; and
   `includes` from `@include "..."` with `target = "file"`.
3. The `pop` rule is the fix for a real defect, not a nicety: without it
   every tile in a multi-dialog file attaches to the first dialog, and SC6
   would still pass because its file (`src/ui/manager.dcl`) holds exactly
   one dialog. A bare `}` cannot be used — blocks nest three deep in
   `manager.dcl` (`: column { : boxed_column { : list_box {`). Column-0 `}`
   is the anchor: measured, `manager.dcl` has 1 dialog and 1 column-0 `}`,
   `dtk_app_dialogs.dcl` 5 and 5. **This is a heuristic, not a parse** — if
   a fixture defeats it, move brace tracking into `post_file`, which
   already re-reads `action = "(fn)"` string bodies.
4. AutoLISP side: `dcl_references` function → dialog from
   `new_dialog "name"` (literal, `EXTRACTED`; the `load_dialog` variable
   form at `pltrn.lsp:10903` stays `INFERRED` with no `target_file`
   stamp); `dcl_action` dialog-or-tile → function from
   `action_tile "key" "(fn …)"` and DCL `action = "(fn)"`. Both are
   AutoLISP source inside a string literal and need a **second read of the
   string body**, not the surrounding tree.
5. Authored fixtures for everything the corpus cannot supply: `@include`
   (zero in the corpus) and a multi-dialog file exercising the `pop` rule.
   The corpus is a smoke run only — 3 files and 8 dialogs cannot exercise
   the `dialog`/`tile`/`contains`/`includes`/`dcl_action` set.
6. `.mnl` (F16): claimed as an AutoLISP suffix by S006's manifest and
   asserted to parse without error. **F16b — the basename→CUIx `INFERRED`
   edge — is not built here**: the corpus has zero `.mnl`/`.cui`/`.cuix`/
   `.mnu` files, so it has no verification and is Could Have with the entry
   condition "a corpus containing `.mnl` files exists".

**Files.** `graphify_lang/autolisp/{dcl,extract}.py`, `dcl.toml`,
`tests/lang/fixtures/src/ui/manager.dcl` and authored DCL fixtures,
`tests/lang/test_dcl.py`.

**Acceptance.** **SC6b** — at least one `dcl_references` edge into
`lithp_mgr` from `src/ui/manager.dcl`. Plus fixture-level assertions for
`tile`, `contains`, `includes`, `dcl_action` and the multi-dialog `pop`.

**Verification.**
```bash
uv run pytest tests/ -q
GRAPHIFY_LANG_PATH=graphify_lang/autolisp uv run pytest tests/lang -q
uv run pytest tests/lang/test_dcl.py -q -k "sc6 or multi_dialog"
guard-all
```

**Commit.** `feat(autolisp): DCL dialog and tile extraction, MNL suffix`

---

## S009 — Packaging, hook and watch, recorded measurements

**Group** autolisp · **Branch** `autolisp` · **Gated by** Q9 (step 5), Q7 (step 6)

**Objective.** Make the plugin installable and take the measurements the
project exists to prove. Development up to here has used
`GRAPHIFY_LANG_PATH`, so **packaging gates nothing that has already been
measured.**

**Prerequisites.** S008.

**Tasks.**

1. `pyproject.toml` `[tool.setuptools] packages` (`:135`): append
   `"graphify_lang"`, `"graphify_lang.autolisp"`.
2. `[tool.setuptools.package-data]` (`:138`):
   `graphify_lang = ["templates/*.toml"]` and
   `"graphify_lang.autolisp" = ["*.toml", "queries/*.scm", "data/*"]`.
   Required because `include-package-data = false` (`:136`) — without these
   the manifest, the queries and the builtins list simply do not install,
   and `pip install -e .` hides it.
3. One test that resolves the manifest and its data files through
   `importlib.resources` **from a non-editable install** (`uv build` then
   install the wheel into a scratch venv). That is the only path a released
   plugin takes, and the only way this fault surfaces.
4. **SC12 in-process half (not gated).** `_run_hook_guard('read')`
   (`cli.py:814-881`) reads its payload from stdin and writes to stdout, so
   assert it with a `tmp_path` project holding `graphify-out/graph.json`,
   `CLAUDE_PROJECT_DIR` pointed at it, a monkeypatched `sys.stdin.buffer`
   carrying `{"tool_input": {"file_path": ".../err.lsp"}}`, and `capsys`.
   Plus the watch half: `'.lsp' in graphify.watch._WATCHED_EXTENSIONS`,
   which also pins the import-order invariant SC2 depends on.
5. **GATED BY Q9.** The shipped
   `[project.entry-points."graphify.languages"]` stanza. Option A (accepted
   loss) registers both manifests, so `.lsp` is claimed in every repository
   that venv graphs. Option B (opt-in) registers `.mnl`/`.dcl` only and
   leaves the `.lsp` claim to a `GRAPHIFY_LANG_PATH` manifest per project.
   **Until Q9 is answered, ship no entry point** and document
   `GRAPHIFY_LANG_PATH` as the install instruction — everything works, and
   nothing is silently claimed.
6. **GATED BY Q7.** The installed-hook manual run and the MCP registration.
   `graphify install` bakes a resolved interpreter path into a user-scoped
   hook (`install.py:341-349`) and emits the **bare** `graphify` for a
   project-scoped one (`:327-329`), which resolves from PATH at hook time —
   the pipx 0.9.55 binary, which has no registry. The MCP server registered
   in the harness invokes `graphify-mcp`, also the pipx build. Both need
   the user's decision (Option A: separate venv plus a second MCP
   registration at `~/.venvs/graphify-lang/bin/graphify-mcp`; Option B:
   `pipx install --suffix=-lang -e .`, which renames **both** console
   scripts — `pyproject.toml:104-106` declares `graphify` and
   `graphify-mcp` — so the MCP registration must be repointed either way).
7. **Recorded measurements** (SRS §1.3 tier 2 — measured once, written into
   this plan's execution log, never re-gated):
   - **SC8**: a fork-owned script calling
     `benchmark.run_benchmark(questions=…)` **directly**, plus a
     procedurally-defined grep-then-read baseline (the exact grep per
     question, whole-file reads, `len(text)//4` tokens). The CLI cannot
     produce this: `cli.py:3088-3103` never passes `questions`, and
     `benchmark.py:85` compares against an estimate of the whole corpus. No
     threshold gates release.
   - **SC9**: corpus extraction under 5 s, `@pytest.mark.perf`.
   - **SC10**: file inventory showing the AutoLISP plugin is a TOML
     manifest plus one Python module, and the DCL manifest is regex-only.
   - The NFR import budget: median of N
     `subprocess.run([sys.executable, "-c", "import graphify.cli"])` with
     and without `GRAPHIFY_LANG_DISABLE=1`, `@pytest.mark.perf`.

**Files.** `pyproject.toml`, `uv.lock`, `tests/lang/test_packaging.py`,
`tests/lang/test_hook_watch.py`, `tests/lang/test_perf.py`,
`scripts/bench_sc8.py`.

**Acceptance.** SC12 (both halves, in-process); packaging test passes from a
wheel; SC8/SC9/SC10 recorded in the Execution Log. Steps 5 and 6 remain
open until Q9 and Q7 are answered — the section may be marked Complete
without them, with both listed as carried-forward.

**Verification.**
```bash
uv run pytest tests/ -q
uv run pytest tests/lang -q
uv run pytest tests/lang -q -m perf         # recorded, not gated
uv build && uv run --isolated --with dist/*.whl pytest tests/lang/test_packaging.py -q
uv run python scripts/bench_sc8.py          # SC8, recorded
guard-all
```

**Commit.** `feat(autolisp): packaging, hook and watch coverage, benchmark harness`

---

## S010 — Upstream proposal

**Group** registry · **Branch** `lang-registry` · **Gated by** nothing ·
**Priority** Should Have — cut this before cutting anything else

**Objective.** F19. File a measured **issue**, not a pull request.

**Prerequisites.** S004 (the artefact) and ideally S009 (the evidence).

**Tasks.**

1. Produce the artefact: `git diff v8...lang-registry -- graphify/`. It is
   four files — three one-line call sites and one new module.
2. Open an issue on `Graphify-Labs/graphify`, **not a PR**. Upstream has
   merged zero pull requests in 60 days (135 of 1,658 ever, 656 open, last
   merge #1737 on 2026-07-08), while precise measured issues — #3366,
   #3381, #1084 — produced maintainer-authored code within days. This
   supersedes `README.md` §Roadmap phase 6's "open a pull request".
3. Cite: #3180 and #1070 (both ask for exactly this and both are
   unanswered), #1084 (the precedent whose shape this copies: merge at
   import, built-ins protected, customs after built-ins), the unserved
   language requests in `cc-RF010.002.md` §1.9, and the measured AutoLISP
   result (79 files → 79 nodes, 0 edges before; 27 functions from one file
   after).
4. Include the `run_language_resolvers` casefold as a separate small fix —
   `resolver_registry.py:76` gates on raw suffixes while `collect_files`
   and `_get_extractor` both lowercase, so `ERR.LSP` is collected and
   dispatched but never resolved. It is a two-line fix in a file with one
   commit in 90 days and stands on its own merits.
5. Expect to carry the registry indefinitely. Plan accordingly.

**Files.** None in the repo (an issue body; keep a copy under
`.claude/docs/` if wanted).

**Acceptance.** Issue open, artefact linked.

**Verification.**
```bash
git diff --stat v8...lang-registry -- graphify/   # 4 files
uv run pytest tests/ -q                           # on lang-registry, clean
guard-all
```

**Commit.** none.

---

## Execution Log

| Date | Section | Status | Notes |
|------|---------|--------|-------|
| 2026-09-08 | — | Planned | Plan created from SRS v2. No code written, nothing committed. |

<!-- TEMPLATE ZONE END -->

---

<!-- CONTENT ZONE START -->

## Carried-forward items

| Item | Section | Blocked on | Effect if never answered |
|------|---------|-----------|--------------------------|
| Shipped entry-point stanza | S009 step 5 | Q9 | Plugin installs but is discovered only via `GRAPHIFY_LANG_PATH`. No measurement is affected. |
| Installed-hook run, MCP registration | S009 step 6 | Q7 | SC12's in-process half still passes; the manual confirmation is not recorded. |
| F16b `.mnl` → CUIx edge | — | a corpus containing `.mnl` files | Nothing; it has no verification today. |
| F20/F21/F22 prose tiers | — | Q8 | Roadmap only; not in this plan. |
| F26 `graphify lang list` subcommand | — | nothing — deliberately unscheduled | Should Have, and it would be a **fourth** core edit against F4's 'no other core line changes'. The Must-Have half (the registry logging its own report) ships in S003/S004 with no core line at all. Schedule the subcommand only if the log line proves insufficient in use. |

## Revision History

| Date | Author | Version | Change |
|------|--------|---------|--------|
| 2026-09-08 | ag-build | v1 | Initial creation from cc-RS000.001 v2 |

<!-- CONTENT ZONE END -->
