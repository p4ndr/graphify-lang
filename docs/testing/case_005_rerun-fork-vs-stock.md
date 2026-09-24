# Case 005 — fork vs stock re-run after plan 02

**Date:** 2026-09-24
**Method:** same as case 003 (`extract(files, cache_root=<per-venv scratch dir>, root=repo)`, fresh caches), plus `graphify update` on `git ls-files` copies. Fork `.venv`, stock pipx `graphifyy 0.9.55`. Working tree uncommitted, after ag-build plan 02.

## 1. Extraction

| Repo | Side | Nodes | Edges | Time | Kinds / relations |
|:-----|:-----|------:|------:|-----:|:------------------|
| autolisp-pvcase (29 .lsp) | stock | 29 | 0 | 0.1 s | file only |
| | fork | 1,176 | 4,972 | 0.2 s | 999 function, 11 command, 137 global; 3,825 calls, 1,147 contains |
| autolithp (81 .lsp, 3 .dcl) | stock | 81 | 0 | 0.3 s | file only |
| | fork | 4,212 | 19,157 | 1.5 s | 3,962 function, 64 command, 72 global, 8 dialog, 22 module; 15,017 calls, 4,128 contains, 4 dcl_references, 8 module_depends |
| autolithp02 | stock | 80 | 0 | 0.2 s | |
| | fork | 3,160 | 13,178 | 1.1 s | |
| autolithp-snap-rework | stock | 81 | 0 | 0.1 s | |
| | fork | 3,069 | 12,430 | 1.0 s | |

Case 003 fork, for contrast: autolithp 394,394 nodes, 0 edges, 41.4 s.

## 2. Quality (fork)

| Check | pvcase | autolithp | autolithp02 | snap-rework |
|:------|:--|:--|:--|:--|
| Missed defuns vs regex | 0 | 0 | 0 | 0 |
| Commands found / truth | 11/11 | 64/64 | 49/49 | 51/51 |
| Globals / top-level `*x*` setq (regex) | 137/137 | 72/70 | 66/64 | 66/64 |
| Token nodes | 0 | 0 | 0 | 0 |
| Duplicate ids | 0 | 0 | 0 | 0 |
| `calls` edges whose target name is absent from caller file | — | 0 of 15,017 | — | — |
| Cross-file `calls` | — | 1,110 | — | — |
| Built-in targets (`car`, `setq`, …) | — | 0 | — | — |

## 3. End-to-end `graphify update`

| Repo | Side | Nodes | Edges | Edges on .lsp/.dcl | Communities | graph.html | Time |
|:-----|:-----|------:|------:|------:|------:|:--|-----:|
| autolisp-pvcase | stock | 627 | 726 | 0 | 70 | yes | 0.6 s |
| | fork | 1,740 | 5,572 | 4,846 | 66 | yes | 1.1 s |
| autolithp | stock | 8,656 | 10,257 | 0 | 526 | yes | 4.6 s |
| | fork | 12,786 | 29,407 | 19,150 | 490 | yes | 7.5 s |

No extraction warnings, no `DEBUG` lines, 0 self-loops.

## 4. Open

| Item | State |
|:-----|:------|
| D11 cache shared between fork and stock (both `v0.9.55`) | open, `docs/50-PENDING.md` P9 |
| `dcl_action` edges | 0: no `.dcl` in the repos for the dialogs behind literal `action_tile` calls |
| `sidecar_doc` | 0 in extract, 1 after build: `x.lsp` and `x.md` share one file id |
| D-001, D-002 (ag-build decisions) | need owner review, `docs/40-DECISIONS.md` |
