<!-- TEMPLATE-VERSION: 2026-09-21-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 50-PENDING.md

This document is a LIVE list of ITEMS that need owner input or a decision.

- `§3` is the list of open ITEMS.

## 1. INSTRUCTIONS:

:- Change this document only with the repo-docs tools (`pending_add`, `pending_settle`, `todo_set`);
  hand edits by the owner are fine.
:- To settle an ITEM: `pending_settle`. To block a TASK: `todo_set` with the ITEM.
<!-- TEMPLATE-END -->

## 3. OPEN ITEMS:

### P2 | 2026-09-21 | Graphify MCP server registration

**Source:** T9.5.

**Status:** OPEN — owner decision needed.

**Description:**

The MCP server registration for the hook nudge requires manual intervention after the package is installed. The owner needs to decide:

- Should the fork's MCP server register automatically on install (requires writing to the user's MCP config)?
- Or should the owner manually add the hook suffixes to `~/.claude/mcp.json`?

**Note:** The `scripts/install-mcp.sh` script has been created with `--dry-run`, `--check`, and `--help` flags to help the owner manage this.

### P3 | 2026-09-21 | Entry-point stanza for upstream compatibility

**Source:** T9.4.

**Status:** OPEN — owner decision needed.

**Description:**

The shipped `[project.entry-points."graphify_lang.plugins"]` stanza is needed for the registry to discover language packages via `importlib.metadata.entry_points`. The owner needs to decide:

- What group name to use (current suggestion: `graphify_lang.plugins`)?
- Should the stanza be present in the fork's `pyproject.toml` even though it's not yet used?

**Note:** The stanza has been added to `pyproject.toml` as an empty section.

## 4. SETTLED ITEMS:

### S1 | 2026-09-21 | AutoLITHP corpus SHA updated to d5a2074

**Source:** P1.

**Status:** SETTLED.

**Decision:** Update the SRS §1.3 to use `d5a2074` and re-measure the six counts.

**Applied:**
- SRS §1.3 SHA updated to `d5a20743b007431521c4f9a0507560d5feb94b27`
- Counts re-measured: 81 `.lsp`, 4,027 defuns, 52 `C:`, 3 `.dcl`, 8 dialogs, 3.1 MiB
- Plan `cc-IP000.001.md` SHA and counts reference updated