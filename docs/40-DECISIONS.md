<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 40-DECISIONS.md

This document is a LIVE register of the decisions made for this repo.

- `§3` is the decision log, newest first.

## 1. INSTRUCTIONS

- Change this document only with the repo-docs tools (`decision_add`, `pending_add`, `pending_settle`); hand edits by the owner are fine.
- To create a decision: `decision_add`. To record an owner answer: `pending_settle`.
<!-- TEMPLATE-END -->

## 3. LOG

### D-001 | 2026-09-21 | Rebase strategy

**Decision:** Rebase, never merge. The fork's value is a small diff against upstream; merge commits hide it.

**Source:** T1.1 setup.

**Rationale:** `git merge upstream/v8` would create a merge commit that obscures the fork's minimal diff. `git rebase upstream/v8` keeps a linear history and makes `git diff v8...HEAD -- graphify/` a clean artefact for upstream consumption.

### D-002 | 2026-09-21 | Upstream proposal route

**Decision:** Open an ISSUE on Graphify-Labs/graphify, not a pull request, for the registry proposal.

**Source:** T10.2.

**Rationale:** The fork's intent is to propose a generic extension layer, not to ship AutoLISP. An issue lets upstream decide whether to accept the design before work begins; a PR implies a complete implementation.

### D-003 | 2026-09-21 | Commit grouping

**Decision:** Keep generic registry work in commits separate from AutoLISP-specific work.

**Source:** T10.5 note.

**Rationale:** Upstream may accept the registry portion while rejecting the AutoLISP-specific details. Separating them allows upstream to cherry-pick the generic portion if desired.

## 4. OPEN DECISIONS

*None.*
