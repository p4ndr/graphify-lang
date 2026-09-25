# Case 005 — plan 04 sniff router and plugins, corpus counts

Plan: `docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md`.
One section per plugin; S14 (KB augment value test) adds its own section.

## vba (S8, T29.1)

**Date:** 2026-09-25
**Branch:** `lang-vba` at `6486c9b` (off `lang-rules` `91f26cd`)
**Fork:** `/home/p4ndr/repos/graphify-lang/.venv` (editable fork; plugin `graphify_lang/vba`, no grammar)
**Corpus HEADs:** BentleyTools `83c526f`, bentley-model-management `ddd0b65`, bim-chk `d7ba56f`
**Instrument:** per repo, `extract(files, cache_root=<fresh temp dir>, root=repo)` over `git ls-files`
entries ending `.bas` / `.cls` / `.frm` (`.frx` not extracted); truth = lines matching
`^\s*(public |private |friend )?(static )?(sub|function|property (get|let|set)) ` (case-insensitive),
summed over the same files, each decoded as Windows-1252.
**Test suite:** `.venv/bin/python -m pytest tests/ -q` → 6086 passed, 14 skipped.

### Start point (plan 04 §1)

| File | `extract_apex` nodes / edges | Fork (`sniff_router[.cls]` → `extract_vba`) nodes / edges |
|:--|--:|--:|
| bim-chk `src/document/ThisWorkbook.cls` | 1 / 0 | 8 / 8 (file, class, 6 procedures; 7 contains, 1 calls) |

### Procedure counts against grep

| Repo | Files .bas / .cls / .frm | .cls routed to vba | Sub + Function + Property nodes | grep truth | Difference |
|:--|:--:|--:|--:|--:|--:|
| BentleyTools | 121 / 5 / 13 | 5 / 5 | 1166 + 1006 + 64 = 2236 | 2236 | 0 |
| bentley-model-management | 42 / 7 / 8 | 7 / 7 | 474 + 447 + 74 = 995 | 995 | 0 |
| bim-chk | 11 / 18 / 4 | 18 / 18 | 201 + 135 + 11 = 347 | 347 | 0 |

Per-file comparison: no file differs. Two BentleyTools `.bas` files have no
`Attribute VB_Name` header (`build/remap-levels.bas`,
`src/modules/BtDumpModels/DumpModels.bas`); `.bas` is not sniffed, so both are
extracted (module label = file stem).

### Other nodes and edges

| Repo | module / class / form | declare / type / enum | contains | calls EXTRACTED / INFERRED | uses | implements |
|:--|:--:|:--:|--:|:--:|--:|--:|
| BentleyTools | 121 / 5 / 13 | 15 / 8 / 4 | 2402 | 7518 / 6 | 106 | 0 |
| bentley-model-management | 42 / 7 / 8 | 7 / 5 / 5 | 1069 | 2804 / 0 | 148 | 0 |
| bim-chk | 11 / 18 / 4 | 0 / 0 / 3 | 383 | 719 / 8 | 5 | 0 |

No corpus file uses `Implements`; the edge is pinned by `tests/lang/test_vba.py`.
INFERRED calls: several same-named public procedures, the one sharing the
longest directory prefix with the caller wins (the AutoLISP resolver rule).
A 24-edge hand check of cross-module calls (12 BentleyTools, 12 bim-chk,
random sample) found every target correct.

### Known limits

- A user procedure named like a VBA-library routine (`Reset` in
  bentley-model-management, a public `.bas` Sub) is not reached by an
  unqualified call from another module: the builtins filter drops the name
  before the resolver. `Module.Reset` still resolves.
- `obj.Method` resolves only when `obj` is declared `As <Class>` in the
  procedure, its parameters or the module; `Variant` / `Object` receivers and
  `With` blocks give no edge.
- The form → code-behind relation is the `contains` edge from the form node to
  its procedures: a `.frm` holds both the designer and the code, so there is no
  second node to link.
