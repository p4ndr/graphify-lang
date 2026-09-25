<!-- TEMPLATE-VERSION: 2026-09-20-006 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 15-INBOX.md

This document is a LIVE set of rules for ingesting the files the owner drops in `docs/inbox/`, and the ledger of what was ingested.

- `§3` is the ledger, NEWEST first.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`inbox_done` writes `§3`); hand edits by the owner are fine. `inbox_list` names the waiting files.
- Ingest = read the WHOLE file, split it into parts, and merge each part where that kind of content lives:

    | Content | Goes to |
    |---|---|
    | Research, findings, references | a spoke in `docs/research/` (new: `repo-docs.ps1 new research "<title>"`) |
    | A plan, design, specification, roadmap | a plan in `docs/plans/` (new: `repo-docs.ps1 new plan "<title>"`) |
    | Work to do | `todo_add`, `todo_step_add` |
    | An owner decision | `decision_add` |
    | A repo rule or condition | `docs/10-READ-FIRST.md` §4 |
    | A question; a part that is unclear or conflicts with a DECISION or ACTIVE plan; anything else | `pending_add`, quoting it; never guess |

- Keep the owner's facts, numbers, names, links and code exactly; rewrite prose into the target's format and register. Mark research claims from the file `[UNVERIFIED]` until checked. Name the source where each part lands: `(inbox YYYY-MM-DD_name.md)`.
- NEVER edit, rename or delete a dropped file by hand. When all its parts have landed, `inbox_done` it with its targets (ITEMS included; it moves the file to the processed/ folder), then `progress_add` the ingest.
- IF a file cannot be read: read it in parts or with the right tool (PDF, image). If that fails, `pending_add` an ITEM and leave the file.
<!-- TEMPLATE-END -->

## 3. LEDGER
