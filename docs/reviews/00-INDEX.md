<!-- TEMPLATE-VERSION: 2026-09-27-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# Reviews hub

This document is the LIVE hub for the reviews of this repo: code, diffs, plans and documents.

- `§1` is the instructions. These apply to every document in `docs/reviews/`.
- `§2` is a list of CONDITIONS. Each sub-section is one CONDITION.
- `§3` is the list of reviews. A script writes it. Do not edit it by hand.

## 1. INSTRUCTIONS

- Put every review report for this repo in `docs/reviews/`. NEVER put one in .claude/docs/ or the repo root.
- Create each report with `repo-docs new review "<title>"`, or the MCP tool `new` with `kind: "review"`. Not by hand.
- The first line under the H1 of a report is one sentence that says what was reviewed, and the verdict. `§3` shows it.
- Each report has one status line: `- Status: OPEN` (unresolved findings), `DONE` (every finding fixed, rejected, or moved to a TASK), or `SUPERSEDED` (name the report that replaces it). `§3` shows it.
- A finding that is still open when its report is closed becomes a TASK (`todo_add`).
- NEVER delete a report.

## 2. CONDITIONS

When a CONDITION is TRUE, execute the tasks listed under that CONDITION.

### IF you add or rename a report, change its first line, or change its status:

-   Update `§3`: run the script with the verb `manifest`.

### IF you review the same target again:

-   Mark the old report SUPERSEDED, and name the new one in it.
<!-- TEMPLATE-END -->

## 3. REVIEWS

<!-- MANIFEST-START -->
| File | Title | Purpose | Type / Status |
|---|---|---|---|
| `01-code-review-cc-cr000-001.md` | Code review (was .claude/docs/cc-CR000.001.md) | Review moved here from .claude/docs/cc-CR000.001.md by repo-docs migrate-reviews (plan 03, T2); the body below is unchanged. | OPEN |
| `02-code-review-cc-cr000-002.md` | Code review (was .claude/docs/cc-CR000.002.md) | Review moved here from .claude/docs/cc-CR000.002.md by repo-docs migrate-reviews (plan 03, T2); the body below is unchanged. | DONE |
| `03-code-review-cc-cr000-003.md` | Code review (was .claude/docs/cc-CR000.003.md) | Review moved here from .claude/docs/cc-CR000.003.md by repo-docs migrate-reviews (plan 03, T2); the body below is unchanged. | OPEN |
<!-- MANIFEST-END -->
