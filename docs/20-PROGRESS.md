<!-- TEMPLATE-VERSION: 2026-09-20-006 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 20-PROGRESS.md

This document is a LIVE running changelog for all work in the repo.

- `§3` is the current session, `§4` the last one, `§5` the rest of the last 7 days; older sessions are in `25-HISTORY.md`.

## 1. INSTRUCTIONS

:- Change this document only through the repo-docs tools (`progress_add`; `todo_set` and `pending_settle` add their own lines); hand edits by the owner are fine.
:- IF the owner says "prepare for exit" or similar: `progress_add` the session's outcome, and record any valid learnings/gotchas in the knowledge layer.
<!-- TEMPLATE-END -->

## 3. CURRENT SESSION

### 2026-09-22 06:40 (UTC+10)

:- repo-docs migration: 30-TODO regained its TASK LIST heading; 20-PROGRESS moved to the current CURRENT/LAST/EARLIER layout

### 2026-09-22 07:00 (UTC+10)

:- T4.1: Fixed `detect.py` to re-add `CODE_EXTENSIONS` and add try-wrapped registry integration after `FILE_COUNT_UPPER`
:- T4.2: Added `apply_dispatch()` to `lang_registry.py` to merge registry extractors into `_DISPATCH`
:- T4.3: Registry merges case variants (`.LSP` → `.lsp`) for robustness
:- T4.4: Created `ARCHITECTURE.md` with `lang_registry.py` row
:- T4.5: All 5452 tests pass; `guard-core` shows 4 files: `graphify/cli.py`, `graphify/detect.py`, `graphify/extract.py`, `graphify/lang_registry.py`

## 4. LAST SESSION

### 2026-09-21 — T1.1 start

:- Created `docs/30-TODO.md`, `docs/35-DONE.md`, `docs/40-DECISIONS.md`, `docs/50-PENDING.md`, `docs/55-SETTLED.md`, `docs/90-OWNER.md` via repo-docs tools.
:- Installed `uv` (`pipx install uv`).
:- Created branch `lang-registry` from `v8`.
:- Created venv with `uv venv && uv sync --all-extras`.
:- Recorded `uv pip freeze` to `tests/lang_baseline.txt`.
:- Ran `uv run pytest tests/ -q` — 5433 passed, 12 skipped, exit 0.
:- Created `scripts/snapshot_tables.py` to dump the six core tables to `tests/upstream_tables.json`.
:- T1.5a: Updated SRS §1.3 corpus SHA to `d5a20743b007431521c4f9a0507560d5feb94b27` and re-measured counts (81 `.lsp`, 4,027 defuns, 52 `C:`, 3 `.dcl`, 8 dialogs, 3.1 MiB). Updated plan `cc-IP000.001.md` SHA and counts reference.
:- T1.5b: Created `scripts/install-mcp.sh` with `--dry-run`, `--check`, and `--help` flags. Added `docs/16-MCP-SETUP.md` documentation.
:- T1.5c: Added `[project.entry-points."graphify_lang.plugins"]` stanza to `pyproject.toml`.
:- T2: Created `.github/workflows/graphify-lang-ci.yml` with matrix for Ubuntu (3.10/3.12/3.13) and Windows (3.12). Added `if: github.repository == 'Graphify-Labs/graphify'` guards to `publish.yml` and `release-graph.yml`. Added `addopts = "-m 'not perf'"` to `[tool.pytest.ini_options]` in `pyproject.toml`.
:- T3: Created `graphify_lang/manifest.py` with `LanguageManifest` frozen dataclass and `from_toml()` method. Created `graphify_lang/registry.py` with discovery (entry-point group, then `GRAPHIFY_LANG_PATH`), validation (one-line reasons, no exceptions), precedence (built-in suffix warning), and caching. Created `tests/test_lang_registry.py` with 16 tests covering schema round-trip and validation failures.
:- Fixed pyproject.toml syntax errors: `package = true:`, `include-package-data = false:`, `target-version = "py310":`.
:- All 5449 tests pass.

## 5. EARLIER SESSIONS