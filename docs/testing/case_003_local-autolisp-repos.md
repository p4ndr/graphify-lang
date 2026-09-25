# Case 003 — fork vs stock graphify on local AutoLISP repos

**Date:** 2026-09-24
**Branch:** `lang-registry` at `0b2d2e4` plus uncommitted working tree
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork + `graphify_lang`)
**Stock:** `~/.local/share/pipx/venvs/graphifyy` (`graphifyy 0.9.55`)
**Instrument:** `graphify.extract.extract(files, cache_root=<per-venv dir>, root=repo)` over every
`.lsp` / `.dcl` / `.mnl` file (excluding `.git/`, `graphify-out/`); ground truth by regex
`^\s*\(defun\s+(\S+)` over the same files. Scripts: session scratchpad `measure.py`, `check.py`.
**Test suite:** `pytest tests/ -q` → 5468 passed, 12 skipped.

## 1. Extraction totals

| Repo | Files (.lsp/.dcl) | Stock nodes | Stock edges | Fork nodes | Fork edges | Fork time |
|:-----|:-----------------:|------------:|------------:|-----------:|-----------:|----------:|
| autolisp-pvcase | 28 / 0 | 28 | 0 | 105,064 | 0 | 8.1 s |
| autolithp | 81 / 3 | 81 | 0 | 394,394 | 0 | 41.4 s |
| autolithp02 | 80 / 3 | 80 | 0 | 290,590 | 0 | 29.5 s |
| autolithp-snap-rework | 81 / 3 | 81 | 0 | 274,493 | 0 | 27.3 s |

Stock time is 0.1–0.2 s per repo.

## 2. Node quality (fork)

| Repo | Function nodes / unique / regex truth | Missed defuns | Command nodes / unique | Global nodes / unique / top-level `*x*` setq | Noise nodes¹ | Duplicate ids | File nodes |
|:-----|:------|--:|:--|:--|--:|--:|--:|
| autolisp-pvcase | 954 / 949 / 960 | 0 | 12 / 12 | 2,872 / 854 / 129 | 99,881 | 494 | 0 |
| autolithp | 3,930 / 3,878 / 3,974 | 33 | 67 / 64 | 16,377 / 2,411 / 70 | 365,958 | 1,098 | 0 |
| autolithp02 | 2,900 / 2,863 / 2,944 | 33 | 52 / 49 | 12,304 / 2,188 / 64 | 269,171 | 901 | 0 |
| autolithp-snap-rework | 2,806 / 2,768 / 2,851 | 33 | 54 / 51 | 11,660 / 2,222 / 64 | 254,041 | 893 | 0 |

¹ `sym_lit`, `str_lit`, `num_lit`, `list_lit`, `call`, `name`, `package_lit` nodes — one per syntax
token, not graph entities.

## 3. README acceptance test (autolithp)

| Check | Expected | Result |
|:------|:---------|:-------|
| Function nodes from `src/core/err.lsp` | 27 | **PASS** — 27 (27 unique) |
| `C:` commands from `src/core/ldr.lsp` | `C:LITHP`, `C:LITHP-MGR`, `C:LITHP-INIT` | **PASS** |
| `err:trap` is one symbol | one node, not `err` + `trap` | **PASS** — `src_core_err_defun_err_trap_caller_fn_args` |
| `dcl_references` edge into `lithp_mgr` | ≥ 1 | **FAIL** — 0 edges; 8 `dialog_name` + 97 `control_name` nodes only |
| No upstream regression | pytest exit 0 | **PASS** |
| Phase 3: inbound `calls` edge to `err:trap` | ≥ 1 | **FAIL** — 0 edges of any relation |

## 4. End-to-end build (`graphify update`, copy of autolisp-pvcase)

| | Stock | Fork |
|:--|--:|--:|
| Nodes | 613 | 105,155 |
| Edges | 712 | 712 |
| Edges touching a `.lsp` node | 0 | 0 |
| Communities | 69 | 104,611 |
| Function nodes | 0 | 954 |
| `graph.html` | built | skipped (> 5,000 node limit) |
| Validation warnings | 0 | 2,690 (1,345 nodes missing `source_file` and `label`) |
| Wall time / peak RSS | — | 25.7 s / 652 MB |

## 5. Defects found

| # | Defect | Evidence |
|:--|:-------|:---------|
| D1 | No edges of any kind (`contains`, `calls`, `loads`, `dcl_*`, `module_depends`, `sidecar_doc`). | §1, §4: 0 `.lsp` edges in every repo |
| D2 | Every syntax token becomes a node; graph is unusable (one community per node, no HTML). | §2 noise column, §4 communities |
| D3 | No file node per `.lsp` file (stock mints one). | §2 file nodes = 0 |
| D4 | `name` nodes lack `source_file` and `label` (ids like `up_7_0`). | 8,062 in autolithp; build warnings §4 |
| D5 | `global` rule matches every `setq` line, incl. locals; one node per occurrence. | 16,377 nodes vs 70 top-level `*x*` setq (autolithp) |
| D6 | `command` rule matches every `C:X` symbol, not only `defun` names; duplicates. | `C:CBC` at `cbc_app_main.lsp:245` and `:278` |
| D7 | Command regex `^[cC]:[a-zA-Z0-9_-]+$` rejects names with a second colon. | `C:log:list-vars`, `Import-Refactor/Archive/core/log_app_main.lsp:886`, missed |
| D8 | Defuns after a tree-sitter `ERROR` node are lost (32 of 33 misses). | `src/modules/blk/mod.lsp:257`, `Import-Refactor/Archive/dialogs/cbc_dlg_main.lsp:287` |
| D9 | Duplicate node ids. | 494–1,098 per repo, §2 |
| D10 | `DEBUG` `print` calls on stdout in `graphify_lang/rules.py` and `graphify_lang/autolisp/extract.py`. | every extract call |
| D11 | Extraction cache is shared across extractor versions: stock graphify read the fork's cache and returned fork nodes. | first run in scratchpad, same `graphify-out/cache` |
| D12 | Fork extract is ~200× slower than stock (all token nodes). | §1 time column |
