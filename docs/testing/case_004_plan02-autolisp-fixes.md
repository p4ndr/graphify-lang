# Case 004 — plan 02 fixes, fork vs stock on local AutoLISP repos

**Date:** 2026-09-24
**Branch:** `lang-registry` at `0b2d2e4` plus uncommitted working tree (plan 02, T19-T25)
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork + `graphify_lang`, tree-sitter-commonlisp 0.4.1)
**Stock:** `~/.local/share/pipx/venvs/graphifyy` (`graphifyy 0.9.55`)
**Corpus HEADs:** autolisp-pvcase `6b5a73a`, autolithp `d5a2074`, autolithp02 `76ebb5b`, autolithp-snap-rework `73eab4c` (no `.graphifyignore`; archives included, as in case 003)
**Instrument:** `.venv/bin/python tools/measure_autolisp.py ~/repos/autolisp-pvcase ~/repos/autolithp ~/repos/autolithp02 ~/repos/autolithp-snap-rework`
— each engine in its own subprocess, `extract(files, cache_root=<fresh temp dir>, root=repo)` over every
`.lsp` / `.dcl` / `.mnl` (`.git/`, `graphify-out/` excluded); truth by regex
`^\s*\(defun\s+([^\s()]+)` (defuns) and `^\(setq\s+(\*[^*\s]+\*)` (top-level globals, first pair).
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 5485 passed, 12 skipped.

## 1. Extraction totals and node quality

| Repo | Files (.lsp/.dcl/.mnl) | Stock nodes | Stock edges | Stock s | Fork nodes | Fork edges | Fork s | ≤ 3× stock + 1 s |
|:--|:--:|--:|--:|--:|--:|--:|--:|:--:|
| autolisp-pvcase | 28 / 0 / 0 | 28 | 0 | 0.05 | 1133 | 4821 | 0.17 | yes |
| autolithp | 81 / 3 / 0 | 81 | 0 | 0.25 | 4212 | 19157 | 1.57 | yes |
| autolithp02 | 80 / 3 / 0 | 80 | 0 | 0.17 | 3160 | 13178 | 1.06 | yes |
| autolithp-snap-rework | 81 / 3 / 0 | 81 | 0 | 0.16 | 3069 | 12430 | 0.97 | yes |

| Repo | File nodes / files | Functions / commands | Unique fn / regex truth | Missed | Globals / unique / top-level truth | Non-`*x*` globals | Token nodes | Missing sf/label | Dup ids | Dialogs | Modules | DEBUG |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| autolisp-pvcase | 28 / 28 | 961 / 11 | 967 / 967 | 0 | 133 / 133 / 133 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| autolithp | 84 / 84 | 3962 / 64 | 3974 / 3974 | 0 | 72 / 58 / 57 | 0 | 0 | 0 | 0 | 8 | 22 | 0 |
| autolithp02 | 83 / 83 | 2932 / 49 | 2944 / 2944 | 0 | 66 / 52 / 51 | 0 | 0 | 0 | 0 | 8 | 22 | 0 |
| autolithp-snap-rework | 84 / 84 | 2838 / 51 | 2851 / 2851 | 0 | 66 / 52 / 51 | 0 | 0 | 0 | 0 | 8 | 22 | 0 |

| Repo | Edges by relation | `err:trap` inbound cross-file calls | `dcl_references` → `lithp_mgr` |
|:--|:--|--:|--:|
| autolisp-pvcase | calls 3716, contains 1105 | 0 | 0 |
| autolithp | calls 15017, contains 4128, dcl_references 4, module_depends 8 | 88 | 1 |
| autolithp02 | calls 10089, contains 3077, dcl_references 4, module_depends 8 | 88 | 1 |
| autolithp-snap-rework | calls 9433, contains 2985, dcl_references 4, module_depends 8 | 88 | 1 |

Case 003 → 004, autolithp: nodes 394,394 → 4,212; edges 0 → 19,157; extract time 41.4 s → 1.6 s;
missed defuns 33 → 0; duplicate ids 1,098 → 0; token nodes 365,958 → 0.
`sidecar_doc` is 0 in every repo: all 63 `@sidecar` targets share the `.lsp` file's stem, and graphify
already gives `x.lsp` and `x.md` one file-node id (`_file_node_id` drops the extension), so the edge would
be a self-loop and is skipped. `dcl_action` is 0: the corpus's literal `action_tile` calls sit in
functions whose dialog (`pltrn_set`, `pltrn_box`) has no `.dcl` in the repo.

## 2. End-to-end build (`graphify update .` on a `git ls-files` copy of autolisp-pvcase)

Copies under `/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/e2e/{fork,stock}`; `/usr/bin/time -v`.

| | Stock | Fork |
|:--|--:|--:|
| Nodes | 627 | 1,732 |
| Edges | 729 | 5,548 |
| Edges touching a `.lsp` node | 0 | 4,819 (calls 3,714, contains 1,105) |
| Function / command nodes | 0 | 972 |
| Communities | 70 | 77 |
| `graph.html` | built | built |
| Validation warnings / `DEBUG` lines | 0 / 0 | 0 / 0 |
| Wall time / peak RSS | 0.52 s / 54 MB | 0.94 s / 76 MB |

## 3. Plan 02 §5 acceptance

| Check | Expected | Result | Instrument |
|:------|:---------|:-------|:-----------|
| Upstream suite | exit 0, no upstream test file edited | **PASS** — 5485 passed, 12 skipped; `git diff --name-only v8 -- tests/` lists only fork files | `pytest tests/ -q` |
| Token nodes | 0 | **PASS** — 0 in all 4 repos | §1 |
| Nodes missing `source_file` / `label` | 0; no extraction warning | **PASS** — 0; `graphify update` log has no warning | §1, §2 |
| File nodes | = `.lsp` + `.dcl` files | **PASS** — 28/28, 84/84, 83/83, 84/84 | §1 |
| Functions + commands vs regex truth (autolithp) | 0 missed | **PASS** — 3974 / 3974, 0 missed | §1 |
| Globals (autolithp) | ≤ 70 unique top-level `*x*`, no locals | **PASS** — 58 unique (72 nodes, one per name per file), 0 non-`*x*` | §1 |
| Duplicate node ids | 0 | **PASS** — 0 in all 4 repos | §1 |
| `err:trap` inbound `calls` from another file | ≥ 1 | **PASS** — 88 (autolithp) | §1 |
| `dcl_references` into `lithp_mgr` | ≥ 1 | **PASS** — 1 (`mgr:show` → `lithp_mgr`, INFERRED, via `dtk:dcl-exec`) | §1 |
| Communities, autolisp-pvcase build | < 1,000 and `graph.html` built | **PASS** — 77, built | §2 |
| Extract time | ≤ 3× stock + 1 s | **PASS** — all 4 (max 1.57 s vs 0.25 s stock) | §1 |
| No stdout noise | no `DEBUG` lines | **PASS** — 0 | §1, §2 |
| `graphify/extract.py` | no `graphify_lang` / `autolisp` string | **PASS** — 0 matches; file equals `HEAD` | `grep -ci` |

## 4. Defects D1-D13

| # | Status | Evidence |
|:--|:-------|:---------|
| D1 no edges | fixed | §1 relations column; §2 |
| D2 token nodes | fixed | §1 token nodes 0 |
| D3 no file node | fixed | §1 file nodes |
| D4 nodes without `source_file`/`label` | fixed | §1 |
| D5 locals as globals | fixed | §1 non-`*x*` globals 0 |
| D6 command per symbol | fixed | commands = `defun C:` only; 64 in autolithp |
| D7 `C:a:b` rejected | fixed | name = source text up to the lambda list; fixture `C:log:list-vars` |
| D8 defuns lost after ERROR | fixed | regex fallback (INFERRED); 0 missed |
| D9 duplicate ids | fixed | §1 |
| D10 DEBUG prints | fixed | §1, §2 |
| D11 shared cache | **open** — needs a `graphify/cache.py` edit; `docs/50-PENDING.md` P9 | — |
| D12 slow | fixed | §1 time column |
| D13 core imports the plugin | fixed | §3 last row |

## 5. Decisions taken during the build

- D-005a: `dcl_references` also from an identifier-shaped string passed to a wrapper call (INFERRED) — the only path to `lithp_mgr` in autolithp.
- D-005b: a name defined in several files resolves to the copy sharing the longest directory prefix with the caller (INFERRED); ties dropped — `err:trap` is defined in `src/core/err.lsp` and `Import-Refactor/Archive/core/err_mod_main.lsp`.
