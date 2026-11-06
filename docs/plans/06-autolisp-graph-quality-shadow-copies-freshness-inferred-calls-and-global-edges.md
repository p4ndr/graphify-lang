# AutoLISP graph quality: shadow copies, freshness, inferred calls and global edges

This plan makes AutoLISP graphs give one clear answer per symbol: stale copies of a module are marked, a stale graph is
named, cross-file calls are EXTRACTED when they can be, and global variables and `load` calls get edges.

- Status: DONE
- Created: 2026-11-06
- Tasks: T40, T41, T42, T43, T44, T45
- Stages: S1=T40; S2=T41; S3=T42; S4=T43; S5=T44; S6=T45

## 1. Goal

Measured on `/home/p4ndr/repos/autolisp/ust/graphify-out/graph.json` (26,064 nodes; built 2026-11-06 06:11):

| # | Fault | Evidence |
| :-- | :-- | :-- |
| F1 | Shadow copies | `logs/` holds 32 tracked `.lsp` copies of `src/` modules (commit `6cf756b manual push for logs`). They are older and differ, so a hash match does not find them. God nodes 1 and 2 are both `ust:rget` (`src/ust_m002_store.lsp:L1162`, `logs/ust_m002_store.lsp:L897`). `query "ust:rget"` starts at the `logs/` copy. `get_neighbors ust:cfg-from-drawing` answers "Ambiguous". |
| F2 | Stale graph, silent miss | `ust:bench-say` was added at 10:30 (`0399dfb`), and the graph does not have it. `query "ust:bench-say callers"` starts at `Say`, `Say()` and `UST`, with no warning that no node matched. |
| F3 | INFERRED calls | 15,326 of 34,350 AutoLISP-touching edges are INFERRED. Cause: `pick_by_prefix` (`graphify_lang/_common.py:144`) returns INFERRED whenever a name has more than one candidate, and F1 gives almost every `src/` name a second candidate. A name with one definition is already EXTRACTED. |
| F4 | Missing edges | 134 `global` nodes have no use edges, only `contains`. `(load "x")` and `(autoload "x" '("cmd"))` give no edge. Only 8 `module_depends` edges exist, all from the `;; depends:` header tags. Quoted function refs and `action_tile` callbacks are already handled (`extract.py` walk, `dcl_action`). |

## 2. Scope

In scope (graphify-lang):

- Shadow-copy detection, the report, and query ranking (F1).
- A miss warning in `query` and the MCP `query_graph`, and a staleness line (F2).
- A measured INFERRED share after F1, and a test that a unique cross-file call is EXTRACTED (F3).
- Global read/write edges and `load` / `autoload` edges in the AutoLISP plugin (F4).

Out of scope here (each one is other repos' work, done as a hand-off):

- ust: add `logs/` to `/home/p4ndr/repos/autolisp/ust/.graphifyignore`, and decide whether `logs/*.lsp` should be tracked at all.
  ust owns this change.
- ag-toolbox: G5 refuses an unlock from a graph older than HEAD (`scripts/graphify-hook.ps1`; guard code, so the owner sets G1 to
  warn first).
- The post-commit hook in each graphed repo (`graphify hook install`, `graphify/hooks.py:864`). The repo's owner must agree before
  anything is written to its `.git/hooks`.

## 3. Design

### 3.1 Shadow copies (F1)

- After the AutoLISP resolve, pair the `.lsp` / `.mnl` files that have the same basename. A pair is a shadow pair when 80% or more
  of the defun names in the smaller file are also in the other file.
- In each pair, the shadow is the file whose path has a segment in `log`, `logs`, `archive`, `backup`, `old`, `bak` or `tmp`
  (case-blind). When no path has such a segment, the shadow is the file with the older git commit time. When the commit times are
  equal, there is no shadow and the pair is listed as a tie.
- Mark the shadow's nodes with `shadow_of: <live file>`. Nodes stay in the graph, so a path query can still reach them.
- `pick_by_prefix` drops the shadow candidates first. When one live candidate stays, the call is EXTRACTED.
- Query start ranking, `god_nodes` and the `get_neighbors` ambiguity check skip `shadow_of` nodes unless the query names the
  shadow path (`logs/ust_m002_store.lsp::ust:rget`).
- `GRAPH_REPORT.md` gets a "Shadow copies" section that lists each pair and gives the `.graphifyignore` line that removes the
  shadow.

### 3.2 Miss warning and staleness (F2)

- When no start node has a label equal to a symbol-shaped query term (a term that holds `:`, `-` or `*`, or that ends in `()`), print
  `no exact match for '<term>'; nearest: <labels>` as the first line of the result, before the traversal.
- Put `built_at_commit` in the graph metadata (if it is not already there). When it is not HEAD, add
  `graph built at <sha>, HEAD is <sha> (N commits); run graphify update <path>` to the result header.
- ag-toolbox G5 then reads this line from the query output, so it needs no git calls of its own (hand-off).

### 3.3 INFERRED calls (F3)

- No new resolver logic. Section 3.1 removes the second candidate. Steps S3 and S6 measure the result.
- Add a regression test: two live files both define `a:x`, so the call is INFERRED. A shadow copy plus one live file give an
  EXTRACTED call. One definition gives an EXTRACTED call.

### 3.4 Global and load edges (F4)

- The walker records each `setq` target and each symbol read that matches `_GLOBAL_RE` (`*name*`), inside a defun. Resolve them to
  the `global` node: `writes_global` (from the defun, for each `setq`) and `reads_global` (for each symbol read).
  When the name has more than one `global` node, use the same rule as `pick_by_prefix`.
- Also record a global that a defun sets but no top-level `setq` defines. Make it a `global` node at its first `setq`, with
  confidence INFERRED.
- `(load "name")`, `(load "name" nil)` and `(autoload "name" '(...))` with a string literal emit a `depends` ref from the
  file node. It resolves to the `.lsp` / `.mnl` / `.fas` / `.vlx` file node with that basename (`.lsp` is added when the name has
  no suffix). When the name does not resolve, there is no edge, and the report lists it as an unresolved load.
- A `(load (strcat ...))` or a variable argument gives no edge, and nothing is guessed.

## 4. Steps

| Step | Action | Verify |
| :-- | :-- | :-- |
| S1 | Baseline: extend `tools/measure_autolisp.py` to print the INFERRED share, the duplicate-label count, the unlinked `global` count and the `module_depends` count. Run it on ust and autolisp-htt and write the numbers into this plan. | the numbers are in §5 |
| S2 | Shadow-copy pairing, `shadow_of`, the `pick_by_prefix` drop, and the report section (§3.1), with tests: a `logs/` copy, a commit-time pick, a tie, and a file under 80% overlap that is not a shadow. | the new tests pass; the full suite passes |
| S3 | Query ranking, `god_nodes` and `get_neighbors` skip shadows (§3.1). Rebuild ust into a scratch output dir (never write in ust). | `god_nodes` has one `ust:rget`; `get_neighbors ust:cfg-from-drawing` gives one answer |
| S4 | Miss warning and staleness line (§3.2), in both the CLI and MCP query paths, with tests. | `query "ust:bench-say"` on the old graph prints the miss line and the staleness line |
| S5 | Global read/write edges and `load` / `autoload` edges (§3.4), with tests that include a variable argument (no edge) and an unresolved name (report line). | the new tests pass; the plugin selftest passes |
| S6 | Re-measure with S1's tool on ust and autolisp-htt. | §5 targets are met |
| S7 | Hand-offs: send ust the `.graphifyignore` line and the S3 numbers. Give the ag-toolbox G5 change to the owner as a G1-warn request. Give the `graphify hook install` command to each repo owner. | each hand-off is sent; its answer is logged in `docs/50-PENDING.md` |
| S8 | Rebuild the pinned wheel, as in README 'Installing the fork', and update `CHANGELOG.md`. | `graphify lang list` runs from the new wheel |

## 5. Acceptance criteria

Measured with `tools/measure_autolisp.py --graph` on fresh `.venv/bin/graphify update` builds of scratch clones
(ust `7a01984`, autolisp-htt `b1b253a1`):

| Number | ust S1 | ust S6 | autolisp-htt S1 | autolisp-htt S6 |
| :-- | --: | --: | --: | --: |
| AutoLISP `calls` edges | 28,240 | 28,304 | 41,357 | 41,357 |
| INFERRED share of `calls` | 55.9% | 0.1% | 0.0% | 0.0% |
| EXTRACTED `calls` | 12,456 | 28,281 | 41,357 | 41,357 |
| Function labels defined in 2+ files (all / live) | 2,364 / 2,364 | 2,364 / 4 | 30 / 30 | 30 / 30 |
| Shadow files / nodes | 0 / 0 | 31 / 2,779 | 0 / 0 | 0 / 0 |
| Repeated labels in the AutoLISP top 10 by degree | 4 | 0 | 0 | 0 |
| `global` nodes / with a use edge | 222 / 0 | 866 / 795 | 1,063 / 0 | 1,637 / 1,134 |
| `module_depends` edges | 8 | 8 | 0 | 0 |
| All edges | 63,695 | 66,733 (+4.8%) | 63,300 | 68,167 (+7.7%) |

S6 notes: the 31 ust shadows are 30 of the 32 `logs/` copies (`logs/ust.lsp` and `logs/ust-test.lsp` have no live
twin) plus `lib/alsp-lib/tests/perfprobe.lsp` (older commit than `tests/perfprobe.lsp`). The new global nodes are
defun-set globals (INFERRED, one per writing file). Neither corpus has a string-literal `load` / `autoload` in code,
so their `module_depends` count is unchanged; the tests cover that path.

- [x] The ust rebuild (scratch output) has no AutoLISP god node twice, and the report lists the `logs/` shadows
  (30 of 32; 2 have no live twin).
- [x] The INFERRED share of AutoLISP `calls` edges in ust is below 5% (from 45%).
- [x] A query for a symbol that is not in the graph prints the miss line first. A graph that is not at HEAD prints the staleness line.
- [x] Every ust `global` node that a defun uses has at least one `reads_global` or `writes_global` edge.
- [x] A string-literal `load` / `autoload` gives a `module_depends` edge, or an unresolved-load report line.
- [x] The full graphify-lang suite passes (except 20 erlang / r / solidity / vbnet / ollama tests that fail the same
  way before plan 06), and the autolisp-htt rebuild has no fewer EXTRACTED `calls` edges than before.

## 6. Risks and open questions

| # | Item | Default |
| :-- | :-- | :-- |
| R1 | The 80% overlap threshold marks a real fork module (two live variants) as a shadow. | A path-segment match is needed, or an older commit time. A tie is never a shadow. A `shadow: off` line in `.graphifyignore` turns the check off. |
| R2 | Global read edges inflate the graph: `*acad*`-style globals are read everywhere. | Globals in the builtins list are skipped. When the edge count rises more than 10%, cap each global at the first read per defun. |
| R3 | The staleness line needs git at query time. | Read `built_at_commit` and compare it with `git rev-parse HEAD` once per query. When there is no git, there is no line. |
| R4 | Upstream graphify changes the query and `god_nodes` code paths. | Keep the shadow filter in one helper in `graphify_lang/_common.py`, and call it from the core paths through the existing plugin hook. |
| R5 | ust may want `logs/` in the graph on purpose. | The report only proposes the `.graphifyignore` line, and ust decides. |
