# AutoLISP extractor fixes from case 003

Fix defects D1-D12 from `docs/testing/case_003_local-autolisp-repos.md` and add the edges agreed on 2026-09-24, so that an AutoLISP repo gives a graph of files, functions, commands, globals and dialogs linked by real edges.

- Status: DONE
- Created: 2026-09-24
- Tasks: T19-T25 in `docs/30-TODO.md`
- Input: `docs/testing/case_003_local-autolisp-repos.md` (measurements, defects D1-D12)

## 1. Goal

`graphify update` on `~/repos/autolithp` gives a graph with one node per file, function, command, top-level global and dialog, `contains` / `calls` / DCL / header edges, no token nodes, and an extract time within 3× of stock.

## 2. Scope

In scope: D1-D12, D13 (below), and the improvements agreed with the owner:

| # | Decision (2026-09-24) |
|:--|:----------------------|
| A1 | `vla-` / `vlax-` / `vlr-` calls: denylist. No node, no edge. |
| A2 | `defun` forms lost after a tree-sitter `ERROR` node: regex fallback adds them as `INFERRED` function / command nodes. |
| A3 | Global node = top-level `(setq *name* ...)` only (each pair of a multi-pair setq); one node per name per file. |
| A4 | Archive folders: no fork change. Owner adds `.graphifyignore` per repo. |
| A5 | Calls to AutoLISP built-ins (`data/builtins.txt` + A1 prefixes): no edge. Other calls resolve case-insensitively, cross-file, to a `defun` in the corpus. Unresolved: dropped. |
| A6 | Edges (judgement from form counts in non-archive code of autolithp / autolisp-pvcase): **in** — `contains`, `calls` (direct), `calls` (quoted `'fn`: 272 / 62 `vl-catch-all-apply '`, 123 / 173 `mapcar '`), `dcl_references` (`new_dialog "x"`), `dcl_action` (`action_tile "k" "(fn ...)"`), `module_depends` (`@depends`, 25), `sidecar_doc` from `@sidecar` (63, file-level). **out** — `loads` (0 literal `(load "`; 15 `safe-load` with computed paths), `command_invokes` (18, low value), `@doc` per-function anchors (2,898 edges to anchors that match no graphify node). |
| A7 | Regression guard: fixture tests in `tests/lang/` + a corpus script that reruns the case 003 measurement (not in pytest). |

D13 (found while planning): `graphify/extract.py` imports `graphify_lang.autolisp.resolve` directly and registers `AUTO_LISP_RESOLVER`, and `resolve.py` also registers itself at import. This breaks README design goal 1 (no language import from core) and registers the resolver twice.

Out of scope: git branch moves and commits (owner decides the `lang-registry` / `autolisp` split); upstream PR; `.graphifyignore` files in the corpus repos.

## 3. Design

- **One purpose-built walker, not the generic query runtime.** `graphify_lang/autolisp/extract.py` gets an `extract_autolisp(path) -> dict` that parses with `tree_sitter_commonlisp` and walks top-level `list_lit` forms itself. `_get_autolisp_manifest` uses it instead of `rules_build`. `tags.scm` drops every capture that is not needed (`str_lit`, `num_lit`, `list_lit`, `cond`, `loop`, `reference.call`, the 10 setq captures); if nothing is left that the walker uses, delete the file and its manifest entry. Fixes D2, D4, D5, D6, D12.
- **Node model.** File node per file (id and shape as `extract_commonlisp`, `commonlisp.py:139-140`); function / command node per `defun` (label = name as written, id from `_file_stem` + casefolded name, line suffix only on a real in-file collision); global per A3. `contains` edge file → each. Fixes D3, D9.
- **Names.** A `package_lit` name is its full source text (`err:trap`). Command = defun name that starts with `c:` (casefold), any number of further colons. Fixes D7.
- **Calls.** Inside each `defun` body, collect the head symbol of every `list_lit` and every quoted symbol (`quoting_lit` / `(quote x)`) as a call candidate; skip binding positions (param list, `setq` targets, `lambda` params) and A5 built-ins. Emit same-file edges directly when the name is defined in the file; put the rest on the result as `autolisp_calls: [{caller_nid, callee, line, source_file}]` for the resolver.
- **Resolver.** `resolve.py` is rewritten: build a casefolded name → function-node-id index over `all_nodes`; for each `autolisp_calls` item emit `calls` (`EXTRACTED`) when exactly one target exists; drop ambiguous names (same god-node guard as `extract.py` member calls). Same pass resolves `dcl_references` (dialog name → dialog node) and `dcl_action` (dialog → function from the `action_tile` string, parsed as AutoLISP with the same walker). No self-registration at import.
- **Resolver wiring (D13).** Remove the `graphify_lang` import from `graphify/extract.py`. The registry registers each manifest's resolver through `graphify.resolver_registry.register` when the manifest is loaded (generic, no AutoLISP name in core). If `graphify/extract.py` then equals `v8` except the registry lookup, good.
- **DCL.** `extract_dcl(path)`: file node, dialog node per `name : dialog {`, `contains` edge. Controls are not nodes (97 control nodes, no edge target need them; `action_tile` keys go on the edge as `key`).
- **Headers.** `@module` → module node; `@depends a b` → `module_depends` to module nodes (resolver, by name); `@sidecar x.md` → `sidecar_doc` file → the `.md` path (target id = graphify's id for that file if it is in the corpus, else drop).
- **Parse errors (A2).** If `root.has_error`, regex `^\s*\(defun\s+([^\s()]+)` over the source; add each name not already found as an `INFERRED` node with `contains`. No calls for those.
- **Hygiene.** Remove every `print("DEBUG ...")` (D10); use `logging` if a message is needed.
- **Cache (D11).** Find how upstream keys `graphify-out/cache` (`graphify/cache.py`). If the key has no extractor/version part, add the plugin name + version to the key for registry-dispatched files only (so upstream behaviour is unchanged). If that needs a core edit beyond the registry lookup, stop and record it in `docs/50-PENDING.md` instead.

## 4. Steps

| Task | Step | Fixes |
|:-----|:-----|:------|
| T19 | Fixtures + failing tests first: `tests/lang/fixtures/` small `.lsp` (defuns, `C:` incl. `C:a:b`, multi-pair top-level setq, local setq, quoted calls, builtins, COM calls, unbalanced paren), `.dcl`, and a two-file cross-call pair. Tests pin exact nodes/edges. | guard |
| T20 | Walker + node model + names + parse-error fallback; switch manifest to it; strip `tags.scm`; remove DEBUG prints. | D2-D7, D9, D10, D12, A2, A3 |
| T21 | Calls (direct + quoted), builtins/COM denylist, `autolisp_calls` on the result. | D1, A1, A5 |
| T22 | Resolver rewrite + registry-side registration; remove core import (D13). | D1, D13 |
| T23 | DCL extractor + `dcl_references` / `dcl_action`; `@module` / `@depends` / `@sidecar` edges. | D1, A6 |
| T24 | Cache key check / fix per §3. | D11 |
| T25 | `tools/measure_autolisp.py` (corpus script, A7) reproducing case 003 tables; run on the 4 repos; write `docs/testing/case_004_*.md`; update README acceptance table status. | A7 |

## 5. Acceptance criteria

| Check | Expected | Instrument |
|:------|:---------|:-----------|
| Upstream suite | exit 0, no upstream test file edited | `pytest tests/ -q` |
| Token nodes | 0 `sym_lit` / `str_lit` / `num_lit` / `list_lit` / `call` / `name` / `package_lit` nodes | `tools/measure_autolisp.py` |
| Nodes missing `source_file` or `label` | 0; `graphify update` prints no extraction warning for `.lsp` | same + CLI output |
| File nodes | = number of `.lsp` + `.dcl` files | same |
| Functions + commands vs regex truth (autolithp) | 0 missed | same |
| Globals (autolithp) | ≤ 70 unique top-level `*x*` names per file set, no locals | same |
| Duplicate node ids | 0 | same |
| `err:trap` inbound `calls` from another file | ≥ 1 | edge list |
| `dcl_references` into `lithp_mgr` (`src/ui/manager.dcl:3`) | ≥ 1 | edge list |
| Communities, autolisp-pvcase build | < 1,000 and `graph.html` built | `graphify update` on a copy |
| Extract time | ≤ 3× stock + 1 s per repo | same |
| No stdout noise | no `DEBUG` lines | CLI output |
| `graphify/extract.py` | no `graphify_lang` / `autolisp` string | `grep` |

## 6. Risks and open questions

- The resolver seam signature is `resolve(per_file, all_nodes, all_edges)`; confirm that extra result keys (`autolisp_calls`) survive the cache round-trip before relying on them. If not, carry them on the caller node, as `resolve.py` T7.1 `unresolved_calls` does.
- `action_tile` strings may hold several forms or escaped quotes; parse the string with the walker and take only list heads that resolve.
- Registering resolvers from the registry must not run twice when the registry is reloaded (`registry.reset()` in tests).
