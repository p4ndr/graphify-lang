# Language-extension layer and AutoLISP plugin

A registry that lets a language be registered from outside `graphify/extract.py`, plus an AutoLISP/DCL plugin built on it.

- Status: ACTIVE
- Created: 2026-09-21
- Tasks: T1-T10 in `docs/30-TODO.md`
- Full documents: requirements `.claude/docs/cc-RS000.001.md` (SRS v2, 1,006 lines); plan `.claude/docs/cc-IP000.001.md` (882 lines, sections S001-S010); squad review `.claude/docs/cc-RS000.001.squad-check.md` (68 comments, all actioned)

## 1. Goal

Ship the extension layer in two commit groups and an AutoLISP/DCL plugin on top, so that `git diff v8...lang-registry -- graphify/` is an artefact an upstream maintainer can read and apply.

## 2. Scope

Three branches, per SRS §4.2 Workflow 5.

| Branch | Off | Carries | Ends at |
|---|---|---|---|
| `v8` | `upstream/v8` | nothing of the fork's; only ever fast-forwards | — |
| `lang-registry` | `v8` | `graphify/lang_registry.py`, three core call sites, `tests/test_lang_registry.py`, the `ARCHITECTURE.md` row, and the fork's CI/release/pytest infrastructure | S004 |
| `autolisp` | `lang-registry` | `graphify_lang/`, `tests/lang/`, packaging, corpus fixtures | S009 |

Nothing on `lang-registry` mentions AutoLISP.

Out of scope: F20/F21/F22 prose tiers (roadmap), and the `graphify lang list` subcommand (F26 Should Have — it would be a fourth core edit; the registry's own log line ships instead).

## 3. Design

- Manifest: TOML (`graphify_lang.toml`) inside the language package, found through `importlib.resources`; entry point carries the name → package pointer only. See `docs/research/01-...md`.
- Registered suffixes merge into `_DISPATCH` at import time so `collect_files` and both parity oracles stay untouched. See `docs/research/02-...md` finding 3.
- Node kinds go in `node_kind` with `file_type: "code"`; relations are open, `confidence` is the closed enum.
- Node ids from `base._file_stem` + `extract._file_node_id`; on collision within a file, append the definition's line number (the `extract_markdown` recipe).
- Every plugin-side failure returns `{"nodes": [], "edges": [], "error": "<text>"}` containing `not installed` or `failed to load`, so the #1745 warning at `extract.py:6365-6370` still fires.
- Each of the three core call sites is individually `try`-wrapped: `graphify.cli` is the only module `graphify hook` imports, so an uncaught exception there breaks every agent tool call in every repository.

## 4. Steps

One TASK in `docs/30-TODO.md` per section. Groups: `prep` (S001), `registry` (S002-S004, S010), `autolisp` (S005-S009).

| Section | Group | Description | Gated by |
|---|---|---|---|
| S001 | prep | Toolchain, upstream baseline, SC2 snapshot, corpus SHA pin | — |
| S002 | registry | Fork CI, release safety, perf marker | — |
| S003 | registry | `lang_registry.py`: manifest schema, discovery, precedence | — |
| S004 | registry | Core merge: three call sites, lazy dispatch, thunked resolver | — |
| S005 | autolisp | Rules runtime (query + regex + builtins + hooks), templates | — |
| S006 | autolisp | AutoLISP nodes | — |
| S007 | autolisp | AutoLISP edges and cross-file resolver | — |
| S008 | autolisp | DCL and MNL | — |
| S009 | autolisp | Packaging, hook/watch, recorded measurements | P1, P3 (two steps only) |
| S010 | registry | Upstream proposal (F19, Should Have) | — |

## 5. Acceptance criteria

`pytest tests/ -q` exits 0 with the S001 baseline counts and no upstream test file edited, at every section. Perf tests carry `@pytest.mark.perf` and are deselected by default.

Every section also runs `guard-all` — three commands from `.claude/docs/cc-IP000.001.md`:

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

AutoLISP output targets, against `~/repos/autolithp`: 27 function nodes from `src/core/err.lsp`; `C:LITHP`, `C:LITHP-MGR`, `C:LITHP-INIT` as command nodes; `err:trap` as one node; at least one `dcl_references` edge into `lithp_mgr`.

## 6. Risks and open questions

- Anything comparing "with plugin" against "without plugin" must be a `subprocess.run`, never an in-process assertion: the three merges are irreversible in-process (`CODE_EXTENSIONS.update()`, `_HOOK_SOURCE_EXTS +=`, the `_WATCHED_EXTENSIONS` snapshot). `lang_registry.reset()` clears the discovery cache only.
- Fixture trees must mirror the corpus path prefix (`tests/lang/fixtures/src/core/err.lsp`) and every fork test must call `extract(paths, root=fixture_root)`; `_file_stem` is the whole relative path, so a flat fixture silently breaks every asserted id.
- Four behaviours have zero corpus instances and need authored fixtures: `defun-q`, direct `(load "x")`, DCL `@include`, `.mnl`.
- Rebase cost is concentrated in `extract.py`; keep each lookup to one line next to a stable anchor.
- Open items P1, P2 and P3 in `docs/50-PENDING.md` (carried from SRS §7.1). Only S009 touches them, in two steps.
