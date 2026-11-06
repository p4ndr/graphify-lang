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

### P18 | Send ust the plan 06 hand-off H1 (.graphifyignore logs/ line and the before/after numbers)? | 2026-11-06

- Source: P6 S7 (T45.2)
- Context: 31 ust shadow files: 30 logs/*.lsp copies of src/ plus lib/alsp-lib/tests/perfprobe.lsp. Text: /tmp/claude-1000/-home-p4ndr-repos-ag-toolbox/d0427e87-241c-46ff-b1e8-8c0409f08c13/scratchpad/plan06-handoffs.md H1. ust owns the change.
- Options: (1) Send H1 to ust as written (recommended: ust decides; queries already prefer src/) (2) Keep logs/ graphed as shadows; send nothing

### P19 | Change ag-toolbox G5/G7 so a stale or missed graphify query is not a full unlock (H2)? | 2026-11-06

- Source: P6 S7 (T45.2)
- Context: Query output now starts with 'no exact match for ...' and 'graph built at X, HEAD is Y'. Guard code is G1-protected: owner sets kb G1 to warn, or edits. Text: plan06-handoffs.md H2 in the same scratchpad.
- Options: (1) Owner sets G1 to warn; an agent makes the H2 change with tests (recommended: closes the stale-unlock gap) (2) Owner edits scripts/graphify-hook.ps1 (3) No change

### P20 | Install graphify post-commit hooks (graphify hook install) in ust, autolisp-htt, ag-toolbox and graphify-lang (H3)? | 2026-11-06

- Source: P6 S7 (T45.2)
- Context: The hook runs graphify update after each commit and checkout and sets the graph.json merge driver; it writes each repo's .git/ hooks and config. Commands: plan06-handoffs.md H3 in the same scratchpad.
- Options: (1) Yes, in all four (recommended: the stale graph was the root of the silent ust:bench-say miss) (2) Only in ust and autolisp-htt (3) No; keep the SessionStart rebuild only

## 4. RESOLVED ITEMS

### P8 | T15 scope: T14 only or include T13 files? | 2026-09-23

- **Source:** T15
- **Context:** T15 will reconcile duplicate test documentation in docs/testing/. T13 and T14 both cover the autolisp-pvcase test run. Need to know if T13-related files should be included.
- **Options:** 
  1. T14 only — focus on T14-*.md and T14-*.json files
  2. Include T13 — also review T13-related files if they contain relevant duplicate content
- **Resolution:** T14 only — focus on T14-*.md and T14-*.json files
- **Applied to:** T15
