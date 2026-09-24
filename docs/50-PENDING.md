<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 50-PENDING.md

This document is a LIVE file containing pending ITEMS.

- `§3` is the pending ITEMS, in priority order.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`pending_add`); hand edits by the owner are fine. They number ITEMS.
- To settle an ITEM: `pending_settle`.
<!-- TEMPLATE-END -->

## 3. ITEMS
### `[?]` P7 | SRS §1.4, F18.4 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P8 | SRS §1.4, F18.5 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P9 | SRS §1.4, F18.6 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P10 | SRS §1.4, F18.7 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P11 | SRS §1.4, F18.8 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P12 | SRS §1.4, F18.9 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P13 | SRS §1.4, F18.10 — Should the fork add a `graphify lang list` subcommand?

**Source:** `cc-RS000.001.md` §1.4 F26.

### `[?]` P14 | T15 scope: T14 only or include T13 files? | 2026-09-23

- **Source:** T15
- **Context:** T15 will reconcile duplicate test documentation in docs/testing/. T13 and T14 both cover the autolisp-pvcase test run. Need to know if T13-related files should be included.
- **Options:** 
  1. T14 only — focus on T14-*.md and T14-*.json files
  2. Include T13 — also review T13-related files if they contain relevant duplicate content
- **Resolution:** T14 only (user confirmed)

---

### P9 | How should the fork stop sharing the AST cache with stock graphify 0.9.55 (D11)? | 2026-09-24

- Source: T24.2
- Context: graphify/cache.py:956 keys AST entries only by content hash under cache/ast/v{graphifyy version}-s{schema}; fork and stock both report 0.9.55, so they read each other's entries. load_cached runs before dispatch (extract.py:5461, 5719) and has no per-extractor hook, so a registry-only key is impossible; any fix edits cache.py. Measured side effect: the fork's own tests used to write into this repo's graphify-out/cache (now given cache_root=tmp_path).
- Options: (1) Fork version string: give the fork a distinct package version (e.g. 0.9.55+lang.1) so _EXTRACTOR_VERSION differs; no code edit, but stock and fork then sweep each other's version dir (cleanup) when sharing one graphify-out (2) Core edit in cache.py: add an optional per-suffix salt (registry-provided plugin name+version) to the AST hash key; propose upstream with the registry issue (3) Accept: document never to share graphify-out between stock and fork

### P10 | Restore upstream CODE_EXTENSIONS in graphify/detect.py (committed in 84d64c9 without 8 suffixes)? | 2026-09-24

- Source: docs/plans/02-autolisp-extractor-fixes-from-case-003.md §3 (Resolver wiring)
- Context: `git diff v8 -- graphify/detect.py`: the moved CODE_EXTENSIONS line drops .cls .trigger .lisp .cl .lsp .asd .robot .resource that v8 has; .lsp returns only via the registry, the other 7 are no longer detected. Also graphify/extract.py at HEAD differs from v8 by ~1,500 lines of comments replaced with `# @doc extract.md#C…` sidecar markers, so it cannot equal v8 except the registry lookup (plan 02 §3). Found during T22; not changed.
- Options: (1) Restore both files to v8 plus only the registry try-blocks (keeps README goal 1 and the upstream-proposal diff small) (2) Keep as is and document the divergence

## 4. RESOLVED ITEMS

### P8 | T15 scope: T14 only or include T13 files? | 2026-09-23

- **Source:** T15
- **Context:** T15 will reconcile duplicate test documentation in docs/testing/. T13 and T14 both cover the autolisp-pvcase test run. Need to know if T13-related files should be included.
- **Options:** 
  1. T14 only — focus on T14-*.md and T14-*.json files
  2. Include T13 — also review T13-related files if they contain relevant duplicate content
- **Resolution:** T14 only — focus on T14-*.md and T14-*.json files
- **Applied to:** T15
