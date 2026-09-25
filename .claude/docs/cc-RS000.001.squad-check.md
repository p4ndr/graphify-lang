# cc-RS000.001 — squad review adjudication log

| Field | Value |
|-------|-------|
| Adjudicator | ag-build (PHASE 1) |
| Date | 2026-09-08 |
| Subject | `.claude/docs/cc-RS000.001.md` v1 → v2 |
| Reviewers | ag-reqs (RQ-1..15), ag-review (RV-1..11), ag-test (TS-1..13), ag-devops (DV-1..15), ag-writer (WR-1..14) |
| Comments adjudicated | 68 |
| Outcome | **68 action, 0 reject, 0 discuss** |
| Open QUERY blocks | **none** — PHASE 2 may start |

Every measured claim was independently re-verified against the checkout at
`a5dcc70` and the corpus at `f7ab804` before being written into the SRS.
Nothing was accepted on the reviewer's assertion alone. Corrections to
reviewer figures are noted in the rows below.

---

## Decisions

| ID | Originator | Decision | Resolution |
|----|-----------|----------|------------|
| RQ-1 | ag-reqs | action | Added §1.5 'Out of Scope for v1', naming CUIx/macro strings, VLX namespace semantics, the LLM/semantic path, PyPI publication, other AutoLISP corpora, upstream file edits, and the project-local discovery tier. |
| RQ-2 | ag-reqs | action | §1.3 corpus pinned to `f7ab804`; the `.graphifyignore` write to AutoLITHP withdrawn; exclusion re-expressed as a checked-in fork-side file list passed to `extract(paths, root=…)`. |
| RQ-3 | ag-reqs | action | Settled as **one distribution**, in-tree; SC2's 'no plugin' state restated as `GRAPHIFY_LANG_DISABLE=1` with no manifest on any discovery path. Two distributions rejected on DV-4's cost. |
| RQ-4 | ag-reqs | action | SC2 extended to all six tables of §1.1 including `_EXTRA_FOR_EXTENSION`, `_WATCHED_EXTENSIONS` and an empty plugin-resolver list. |
| RQ-5 | ag-reqs | action | SC5 restated as `count(node_kind in {function, command})` within 2% of the same grep over the checked-in file list, computed in the test run; 2,980 is no longer a hard-coded constant. |
| RQ-6 | ag-reqs | action | Verified `cli.py:3088-3103` never passes `questions` and `benchmark.py:85` compares against whole-corpus `corpus_words`. SC8 demoted to a recorded measurement with a fork-owned script calling `run_benchmark(questions=…)`; the 20% threshold no longer gates release. |
| RQ-7 | ag-reqs | action | Verified `install.py:341-349` / `:327-329`. Workflow 2 now names the exact command, cwd and PATH requirement; the user-facing half moved to §7.1 Q7, merged with DV-15. |
| RQ-8 | ag-reqs | action | User question moved to §7.1 as **Q9** with both options (accepted loss vs. opt-in `GRAPHIFY_LANG_PATH` manifest claiming `.lsp`, entry point claiming `.mnl`/`.dcl` only). |
| RQ-9 | ag-reqs | action | Verified `_get_extractor`'s filename routing is hard-coded special cases. `filenames` dropped from schema v1 (F1, F3, §6.3 manifest); the `acad.lsp`/`acaddoc.lsp` entries were redundant. |
| RQ-10 | ag-reqs | action | `graphify lang list` given ID **F26**, Should Have, depends on F2; the Must-Have form is the `--verbose` line plus `registered_languages()`, needing no fourth core edit. |
| RQ-11 | ag-reqs | action | F16 split: F16 (`.mnl` claimed and parses) stays Must; **F16b** (basename→CUIx edge) demoted to Could Have with entry condition 'a corpus containing `.mnl` files exists'. Verified 0 `.mnl`/`.cui`/`.cuix`/`.mnu` in the corpus. |
| RQ-12 | ag-reqs | action | §1.3 split into release gates and recorded measurements; F11 demoted to Should, F16b to Could; a `Verified by` column added so the priority column now carries information. |
| RQ-13 | ag-reqs | action | Settled as **two manifests** in one plugin package (`graphify-lang.toml` + `dcl.toml`, `[language] name = "dcl"`), F14's resolver spanning both. `[[grammar]]`-per-suffix rejected as schema complexity for one case. |
| RQ-14 | ag-reqs | action | **SC13** added (unknown `schema`, and non-importable runtime module: same counts as no plugin, all three modules still import, exactly one warning line). |
| RQ-15 | ag-reqs | action | F13 now states the contract: per file emit `calls` with target unresolved and `confidence: AMBIGUOUS`; F14 promotes to `EXTRACTED` and stamps `target_file`; still-unbound edges dropped. |
| RV-1 | ag-review | action | **Re-measured and extended.** `err.lsp`: 27 defuns → 26 distinct ids (`err:trap`/`err:_trap` collide) — RV-1 correct. Across the pinned 80-file corpus there are **11** colliding groups, not 5: RV-1's 5 of the `pkg:_private` kind, plus 6 where `*error*` is redefined in one file (24× in `pltrn.lsp`). Resolved by requiring line-number disambiguation on collision (upstream `extract_markdown` precedent), so SC4 stays 27 and the collision set is a checked-in fixture. |
| RV-2 | ag-review | action | Verified `llm.py:228`. Project-local `./.graphify/languages/` **dropped from v1**; entry points + `~/.graphify/languages/` + `GRAPHIFY_LANG_PATH` retained. Resolves RV-2, RV-8 and DV-1 together. |
| RV-3 | ag-review | action | Verified `detect.py:517` precedes `:526`. F1 now rejects any manifest claiming a suffix already in `DOC_EXTENSIONS`, and **F20 now depends on F21** rather than sitting beside it. |
| RV-4 | ag-review | action | Verified `resolver_registry.py:29-40` and `extract.py:4542-4575`. `apply_dispatch` must register a `LanguageResolver` whose `resolve` is a thunk; SC14 asserts it. |
| RV-5 | ag-review | action | Verified `base.py:58-81` and `extract.py:6498-6512`. Contract now names `_file_stem` and `_file_node_id` explicitly; §6.1 records the private-helper coupling with a test that fails loudly on an upstream rename. |
| RV-6 | ag-review | action | Verified `resolver_registry.py:76` has no casefold while `extract.py:7609`/`:5881` do. `apply_dispatch` registers case variants; the casefold goes into F19. |
| RV-7 | ag-review | action | Verified `_DEP_MISSING_MARKER = "not installed"` / `_DEP_LOAD_FAILED_MARKER = "failed to load"` (`extract.py:5763-5764`, consumed `:6365-6370`). Pinned in F5 as required error vocabulary; SC13 asserts the warning text. |
| RV-8 | ag-review | action | Verified `llm.py:266-281`'s `GRAPHIFY_ALLOW_LOCAL_PROVIDERS` gate. Resolved by dropping the tier (RV-2); §5 Security row rewritten to say which tier is trusted and why, with the gating conditions recorded should it ever be added. |
| RV-9 | ag-review | action | **Re-measured with `tree_sitter_commonlisp` 0.4.1:** `(defun-q q:legacy …)` parses as a plain `list_lit` with a `sym_lit` head — no `defun`, no `defun_header`. Second definition rule added to `tags.scm` with `#eq?`, plus an authored fixture (corpus has 0). |
| RV-10 | ag-review | action | **Re-measured:** 27 definitions vs 298 `@reference.call` on `err.lsp`; `caller` and `caller-sym` both captured. Structural exclusions (no reference from a `list_lit` that is a direct child of `defun_header`; none inside `quoting_lit`) stated in F13, with the 298 flagged for re-measurement because it feeds SC7. |
| RV-11 | ag-review | action | **Re-measured:** `manager.dcl` nests three deep; column-0 `}` count equals dialog count in both multi-dialog files (1/1 and 5/5). A `scope = "pop"` rule anchored to `^\}` added, with `post_file` brace tracking named as the fallback. |
| TS-1 | ag-test | action | Verified `~/.venvs` absent and pytest importable from neither interpreter. The plan's first task is now: create the venv, run the suite on unmodified `v8`, check in pass/fail/skip counts as SC1's oracle. |
| TS-2 | ag-test | action | SC2 specified as a `subprocess.run` with `GRAPHIFY_LANG_DISABLE=1` against a snapshot regenerated at each rebase; `reset()`'s contract stated as cache-only in §3.2. |
| TS-3 | ag-test | action | Verified `_HOOK_SOURCE_EXTS` is a **tuple** (`cli.py:71-75`) and `cli.py:881` lowercases. `hook_suffixes()` typed `tuple[str, ...]` lowercase; all three call sites required to be individually wrapped; SC13 extended to assert all three modules still import. |
| TS-4 | ag-test | action | Verified `_run_hook_guard` (`cli.py:814-881`) is stdin/stdout. SC12 restated as the in-process assertion plus one recorded manual run, and the missing watch half added (`'.lsp' in watch._WATCHED_EXTENSIONS`). |
| TS-5 | ag-test | action | **Independently re-measured, TS-5 exact:** `f7ab804`, clean, no `.graphifyignore`; 79 files / 2,978 defuns for three dirs, 80 / 2,980 with `build/`. Corpus defined as the **four-directory, 80-file, 2,980-defun** set so SC9 and §7.2's '80 files' stay consistent. |
| TS-6 | ag-test | action | **Re-measured, all four confirmed zero:** `defun-q` 0, direct `(load "` 0 (14 `err:safe-load` call sites), DCL `@include` 0, `.mnl`/`.cui`/`.cuix`/`.mnu` 0. Authored fixtures named as the acceptance evidence in F13, F15, F16b and F18; the SC8 question set carries the note. |
| TS-7 | ag-test | action | **Re-measured, TS-7 exact:** 3 `.dcl` files, 8 dialogs (1+2+5), 97 `key =`, 12 `action =`; the '18' is the `new_dialog` call-site count. Corrected in §1.1 and §3.1; §7.2 records that `cc-RF010.003.md` §3.1's '48 dialogs / 18 files' is worktree-inflated. |
| TS-8 | ag-test | action | Fixture tree required to mirror the corpus prefix (`tests/lang/fixtures/src/core/err.lsp`) with every fork test calling `extract(paths, root=…)`. |
| TS-9 | ag-test | action | F2 now sorts each directory tier by manifest path and fixes the tier order, so F3's tie-break is an assertion rather than `os.scandir` order. |
| TS-10 | ag-test | action | §2.3 `collect_files` row rewritten: the oracle re-derives from `_DISPATCH` at call time and every other upstream table assertion is membership-only, so a green upstream suite is not evidence the merge worked. SC1's weight moved onto SC2 and the fork's tests. |
| TS-11 | ag-test | action | Verified `[tool.pytest.ini_options]` has no `addopts`. SC9 and the import budget become `@pytest.mark.perf`, deselected via a new `addopts = "-m 'not perf'"`; import cost measured as a median of subprocess runs. |
| TS-12 | ag-test | action | Verified `testpaths = ["tests"]` (`:147`), explicit `packages` (`:135`), `include-package-data = false` (`:136`). Tests moved to `tests/lang/`; package-data entries specified in §6.1; a non-editable-install `importlib.resources` test required. |
| TS-13 | ag-test | action | **SC14** added: in a subprocess, no `graphify_lang` or `tree_sitter_commonlisp` in `sys.modules` after importing `graphify.extract`/`graphify.cli`, both present after one `.lsp` dispatch. |
| DV-1 | ag-devops | action | Verified `.gitignore:15-16`. Resolved by dropping the tier (RV-2); `GRAPHIFY_LANG_PATH` named as the supported way to carry a checked-out plugin. |
| DV-2 | ag-devops | action | **Re-measured over 30 days:** `pyproject.toml` 24, `uv.lock` 18, `extract.py` 39 — DV-2 exact. Both files added to §2.2 and the §2.3 Rebase-cost row; Workflow 5 resolves `uv.lock` by regeneration, never by merge. |
| DV-3 | ag-devops | action | Verified `pyproject.toml:97` has no specifier and `:126` no ceiling. Extra capped `>=0.4.1,<0.5`; `[grammar] version` added to schema v1 with F1 rejecting a mismatch loudly. |
| DV-4 | ag-devops | action | Layout settled with RQ-3 (one distribution); the entry-point stanza and `[tool.setuptools.package-data]` entries written into §6.1. |
| DV-5 | ag-devops | action | Verified `ci.yml:71,74` use `uv sync --all-extras --frozen`, `uv.lock` pins `tree-sitter 0.25.2` / `tree-sitter-commonlisp 0.4.1`, and `uv` is absent from PATH. Workflow 1 step 1 is now install-uv → `uv venv` → `uv sync --all-extras`. |
| DV-6 | ag-devops | action | Verified `install.py:644` and `:674`. Workflow 2 now states the exact command, its cwd, and which executable must be first on PATH; the residual decision is §7.1 Q7. |
| DV-7 | ag-devops | action | Two-branch layout (`lang-registry` off `v8`, `autolisp` off it) written into Workflow 5, making `git diff v8...lang-registry -- graphify/` both the F19 artefact and the §5 core-diff instrument. |
| DV-8 | ag-devops | action | Verified `ci.yml:4-7`. A fork-only workflow with `on: push: branches: ['**']` added as a §5 CI row; upstream's file stays unedited. |
| DV-9 | ag-devops | action | Verified `--frozen` at `:71,74,98`. Fork workflow uses `--locked`; 're-run `uv lock` and commit it' made part of any dependency change. |
| DV-10 | ag-devops | action | Kept the 0.23/0.24 shim (upstream's own pin admits that range, so dropping it ships a real break) **and** added the floor-pinned CI leg `uv run --with 'tree-sitter==0.23.*' pytest tests/lang -q`; F18 names it. |
| DV-11 | ag-devops | action | Verified the matrix is `ubuntu-latest` × 3.10/3.12 with no Windows leg. Fork workflow matrix extended to 3.13 + `windows-latest`; a test asserting which TOML module was imported added to the 3.10 leg's requirements. |
| DV-12 | ag-devops | action | Verified `publish.yml:13-15,26-28,54-55` and `release-graph.yml:3-6,11-12`. A `github.repository == 'Graphify-Labs/graphify'` job guard and a §5 Release row added; fork releases are git tags only. |
| DV-13 | ag-devops | action | Verified `pyproject.toml:7` and `publish.yml:43`'s verbatim `^version = ` grep. `version` left untouched; fork identity surfaces through the registry report and `registered_languages()`. |
| DV-14 | ag-devops | action | Verified `ci.yml` declares no `permissions:` block and `release-graph.yml:11-12` grants `contents: write`. `permissions: contents: read` required on the fork's own workflow; hardening upstream's mutable action tags recorded as a separate F19-shaped proposal. |
| DV-15 | ag-devops | action | Verified `pyproject.toml:104-106` declares both `graphify` and `graphify-mcp`. Merged with RQ-7 into a restated §7.1 **Q7** carrying both options and the MCP-repointing consequence. |
| WR-1 | ag-writer | action | §1.1 now names the six tables once, in a table, and fixes the phrase 'six tables across five files'; the §2.2 core row updated to match. |
| WR-2 | ag-writer | action | Changed to 'learning id 1212', with a note reserving `#` for GitHub issue/PR numbers. |
| WR-3 | ag-writer | action | DCL and MNL expanded at first use; §1.4 Abbreviations added (COM, CUIx, DCL, MNL, MoSCoW, NFR, SC). |
| WR-4 | ag-writer | action | §2.3 Upstream-process row now cites `README.md:305-327` explicitly and states that F19 supersedes its phase 6; §7.1 Q4 restated the same way. |
| WR-5 | ag-writer | action | Fork-rules row now points at Workflow 5's branch layout and at `cc-IP000.001.md` for the commit plan. |
| WR-6 | ag-writer | action | `PY` moved into the `lang_registry.py` subgraph; the resolver hook named `register_language_resolver` in the diagram, the call-site table and §6.2 alike. |
| WR-7 | ag-writer | action | Version stated once in §1.1; the anchor table now cites checkout (`v0.9.55`) numbers throughout. |
| WR-8 | ag-writer | action | §4.1 states the MoSCoW vocabulary and that `Could Have` deliberately replaces the template's `Nice to Have`. |
| WR-9 | ag-writer | action | F1 and F8 made the complete key sets (`case_insensitive`, `builtins_prefixes`, `version`, `edge_from_scope`, `target`), with a rule that later features declare any key they add. |
| WR-10 | ag-writer | action | `Verified by` column added to the feature register; F3, F6 and F10 now each name a criterion or fixture. |
| WR-11 | ag-writer | action | All six workflows and the SC8 question set promoted to `####` headings. |
| WR-12 | ag-writer | action | Stated once: `[extract] runtime` names a module; the registry calls its module-level `build`; `RuleSet` is an implementation detail behind it. |
| WR-13 | ag-writer | action | Node/edge kind lists aligned with F12/F13/F15 (`contains`, `defines` in the AutoLISP manifest; `dialog`, `tile`, `contains`, `includes`, `dcl_action` in the DCL manifest). |
| WR-14 | ag-writer | action | §7.2 states that repo-local RF numbering is independent of the global `cc-RF000.000.md` ranges; no renumbering required. |

---

## Open QUERY blocks

**None.** No comment required its originator's input: every factual claim
was verifiable against the checkout or the corpus, and every design fork
was decidable from the evidence already in the SRS and the three research
documents. PHASE 2 (implementation plan) is unblocked.

## Escalated to the user (not queries — recorded in SRS §7.1)

| ID | Question |
|----|----------|
| Q7 | Which build do the agents actually reach — the installed hook and the MCP server? (from RQ-7, DV-6, DV-15) |
| Q8 | Which prose corpus is the first `type = "prose"` target for F20? (pre-existing) |
| Q9 | Is the global `.lsp` claim an accepted loss, or should it be opt-in per project? (from RQ-8) |

None of the three blocks the implementation plan: Q8 gates only the F20
roadmap item, Q7 gates only SC12's manual half, and Q9 changes one line of
the entry-point stanza.

---

## Design decisions taken in adjudication

Recorded here because each closed a fork the reviewers left open, and
PHASE 2 inherits them.

| Decision | Chosen | Rejected | Because |
|----------|--------|----------|---------|
| Packaging | One distribution, plugin in-tree | Two distributions | setuptools' explicit `packages` list cannot express a second distribution; it needs a second project dir, version and build step, and the venv must install both (DV-4). SC2 is expressible with `GRAPHIFY_LANG_DISABLE=1` regardless (TS-2). |
| Project-local discovery tier | Dropped from v1 | Kept, gated by `GRAPHIFY_ALLOW_LOCAL_LANGUAGES=1` | Dropping resolves RV-2, RV-8 and DV-1 at once and removes machinery v1 has no use for; `GRAPHIFY_LANG_PATH` already covers the checked-out-plugin case and is the only deterministic tier for tests. |
| `filenames` in schema v1 | Dropped | Kept, with a fourth core edit to `_get_extractor` | The AutoLISP entries are redundant once `.lsp` is claimed, and the edit would break F4's 'no other core line changes' and add a rebase conflict surface for nothing (RQ-9). |
| AutoLISP + DCL manifests | Two manifests, one package | One manifest with `[[grammar]]` arrays | A per-suffix grammar array is schema complexity carried by every plugin to serve one case; two manifests need no schema change and F14's resolver already spans suffixes (RQ-13). |
| Id collisions | Disambiguate on collision (append line number) | Accept the merge, restate SC4 as 26 | Merging `err:trap` with `err:_trap`, and 24 `*error*` handlers into one node, is a graph defect rather than a cosmetic one; upstream's `extract_markdown` already sets the precedent (RV-1). |
| py-tree-sitter 0.23/0.24 shim | Kept, plus a floor-pinned CI leg | Dropped as unbuilt speculation | Upstream's own pin is `>=0.23.0,<0.26`, so a user venv can legitimately resolve the floor and the plugin would break with an obscure `AttributeError`; the shim is three lines and the CI leg needs no second lock (DV-10). |
