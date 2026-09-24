# Case 006 — fork vs stock re-run after T1, T5-T8, T24, T26

**Date:** 2026-09-24
**Method:** as case 005 (fresh per-venv caches; `graphify update` on `git ls-files` copies). Fork `.venv` now `0.9.55+lang.1`; stock pipx `graphifyy 0.9.55`.
**Test suite:** `pytest tests/ -q` → 5495 passed, 12 skipped.

## 1. Extraction

| Repo | Stock nodes / edges | Fork nodes / edges | Fork time | Missed defuns | Token nodes | Dup ids |
|:-----|:--|:--|--:|--:|--:|--:|
| autolisp-pvcase (32 .lsp; was 29) | 32 / 0 | 1,301 / 5,634 | 0.2 s | 0 | 0 | 0 |
| autolithp | 81 / 0 | 4,212 / 19,157 | 1.6 s | 0 | 0 | 0 |
| autolithp02 | 80 / 0 | 3,160 / 13,178 | 1.1 s | 0 | 0 | 0 |
| autolithp-snap-rework | 81 / 0 | 3,069 / 12,430 | 1.0 s | 0 | 0 | 0 |

autolithp, autolithp02 and snap-rework are identical to case 005. pvcase grew by 3 files (corpus commit `bf69f47`).

## 2. End-to-end `graphify update`

| Repo | Side | Nodes | Edges | Communities | graph.html | Time |
|:-----|:-----|------:|------:|------:|:--|-----:|
| autolisp-pvcase | stock | 659 | 754 | 75 | yes | 0.6 s |
| | fork | 1,928 | 6,386 | 79 | yes | 1.2 s |
| autolithp | stock | 8,656 | 10,257 | 526 | yes | 4.6 s |
| | fork | 12,786 | 29,407 | 490 | yes | 7.6 s |

## 3. New observations

| Item | Detail |
|:-----|:-------|
| Skill version warning | Fork CLI prints `skill at ~/.claude/skills/graphify is from graphify 0.9.55, package is 0.9.55+lang.1` (side effect of D-007). Do not run `graphify install` from the fork: it would overwrite the stock skill. |
| Open P-items | P15 (fork and stock sweep each other's cache dir), P16 (generic rules runtime), P17 (plan 01 steps replaced by plan 02). |
