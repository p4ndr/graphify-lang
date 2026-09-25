# graphify-lang fork — 10-READ-FIRST

**Project**: graphify-lang — language extension layer for Graphify

**Active branch**: v8 (mirrors upstream)

**Owner**: p4ndr

**Last updated**: 2026-09-22

---

## What this repo is

A fork of `Graphify-Labs/graphify` that adds a language-extension layer so a language can be registered from a package outside `graphify/extract.py`. First target: AutoLISP (`.lsp`, `.dcl`, `.mnl`).

---

## Authoritative docs

- **Core pipeline**: upstream's `ARCHITECTURE.md` and `AGENTS.md`
- **Extractor split**: `graphify/extractors/MIGRATION.md` (invariants)
- **Fork intent & roadmap**: `README.md`

See `.claude/CLAUDE.md` for more.

---

## Open tasks

See `docs/30-TODO.md` and `docs/50-PENDING.md`.

---

## Recent progress

See `docs/20-PROGRESS.md`.

---

## Database health

Run `/db-health` via MCP or `db.ps1 health` to verify all three DBs (`kb`, `ops`, `ltm`) are reachable and schema versions match expectations.

---

## Sidecar status

Run `sidecar_verify` to check for source/sidecar mismatches.

---

## How to update upstream

```bash
git fetch upstream
git rebase upstream/v8
```

Rebase, never merge. Never edit existing language extractors or core tables (`_DISPATCH`, `CODE_EXTENSIONS`, `_HOOK_SOURCE_EXTS`).

---

## Development setup

The fork is developed in a separate uv venv (not installed into the global `graphify` pipx venv). See `README.md` § Development setup.
