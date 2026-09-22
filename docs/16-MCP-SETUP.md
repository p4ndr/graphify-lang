# MCP Setup for AutoLISP Support

This document describes how to register AutoLISP hook suffixes (`.lsp`, `.dcl`, `.mnl`) in Claude MCP configuration.

## Quick Start

Run the install script:

```bash
./scripts/install-mcp.sh
```

This adds the required suffixes to `~/.claude/mcp.json` and creates a backup.

## Flags

| Flag | Description |
|---|---|
| `--dry-run` | Show what would be written without making changes |
| `--check` | Report current registration status (exit 0 if registered) |
| `--help` | Show this help |

## Verification

After running `install-mcp.sh`, verify registration:

```bash
./scripts/install-mcp.sh --check
```

Expected output:

```
✓ AutoLISP hook suffixes are registered in ~/.claude/mcp.json
```

## Manual Configuration

If the script fails or you prefer to edit manually, add to `~/.claude/mcp.json`:

```json
{
  "watch": {
    "_HOOK_SOURCE_EXTS": [".lsp", ".dcl", ".mnl"]
  }
}
```

Or merge into an existing `watch` entry:

```json
{
  "watch": {
    "_HOOK_SOURCE_EXTS": [".lsp", ".dcl", ".mnl"]
  }
}
```

## What This Does

The hook suffix registration enables graphify to:

1. **Nudge** — Trigger graph regeneration when editing AutoLISP/DCL files
2. **Watch** — Monitor files for changes under projects using graphify

## Rollback

If needed, restore the backup file:

```bash
cp ~/.claude/mcp.json.backup.YYYYMMDDHHMMSS ~/.claude/mcp.json
```

Or manually edit `~/.claude/mcp.json` to remove the `.lsp`, `.dcl`, `.mnl` entries.
