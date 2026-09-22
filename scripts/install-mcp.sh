#!/usr/bin/env bash
# install-mcp.sh — Register AutoLISP hook suffixes in Claude MCP config
#
# Usage:
#   ./install-mcp.sh           Install the suffixes (writes ~/.claude/mcp.json)
#   ./install-mcp.sh --dry-run Show what would be written without writing
#   ./install-mcp.sh --check   Report current registration status (exit 0 if registered)
#
# This script adds `.lsp`, `.dcl`, and `.mnl` to the `watch._HOOK_SOURCE_EXTS` array
# in ~/.claude/mcp.json, creating the entry if missing.

set -euo pipefail

MCP_FILE="${HOME}/.claude/mcp.json"

# Default action
ACTION="install"

# Parse arguments
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      ACTION="dry-run"
      ;;
    --check)
      ACTION="check"
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run|--check|--help]"
      echo ""
      echo "Options:"
      echo "  --dry-run  Show what would be written without writing"
      echo "  --check    Report current registration status (exit 0 if registered)"
      echo "  --help     Show this help"
      echo ""
      echo "Default: install (write to ${MCP_FILE})"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

# Check if MCP file exists
if [[ ! -f "$MCP_FILE" ]]; then
  echo "Error: ${MCP_FILE} not found" >&2
  exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
  echo "Error: jq is required but not installed" >&2
  exit 1
fi

# Extract current watch._HOOK_SOURCE_EXTS array or default to empty
CURRENT_EXTS=$(jq -r '.watch._HOOK_SOURCE_EXTS // []' "$MCP_FILE")

# Required suffixes
REQUIRED_EXTS=(".lsp" ".dcl" ".mnl")

# Check if all required suffixes are present
MISSING=()
for ext in "${REQUIRED_EXTS[@]}"; do
  if ! echo "$CURRENT_EXTS" | jq -e "index(\"$ext\")" > /dev/null 2>&1; then
    MISSING+=("$ext")
  fi
done

case "$ACTION" in
  check)
    if [[ ${#MISSING[@]} -eq 0 ]]; then
      echo "✓ AutoLISP hook suffixes are registered in ${MCP_FILE}"
      echo "  Current: ${CURRENT_EXTS}"
      exit 0
    else
      echo "✗ AutoLISP hook suffixes are NOT registered in ${MCP_FILE}"
      echo "  Missing: ${MISSING[*]}"
      echo "  Current: ${CURRENT_EXTS}"
      exit 1
    fi
    ;;
  dry-run)
    if [[ ${#MISSING[@]} -eq 0 ]]; then
      echo "✓ No changes needed — suffixes already registered"
      exit 0
    else
      echo "Would add to ${MCP_FILE}:"
      echo "  watch._HOOK_SOURCE_EXTS: ${MISSING[*]}"
      exit 0
    fi
    ;;
  install)
    if [[ ${#MISSING[@]} -eq 0 ]]; then
      echo "✓ AutoLISP hook suffixes are already registered in ${MCP_FILE}"
      exit 0
    fi

    # Create backup
    BACKUP="${MCP_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$MCP_FILE" "$BACKUP"
    echo "Created backup: ${BACKUP}"

    # Add missing suffixes
    for ext in "${MISSING[@]}"; do
      jq --arg ext "$ext" '.watch._HOOK_SOURCE_EXTS += [$ext]' "$MCP_FILE" > "${MCP_FILE}.tmp" && \
        mv "${MCP_FILE}.tmp" "$MCP_FILE"
      echo "Added ${ext} to watch._HOOK_SOURCE_EXTS"
    done

    echo "✓ AutoLISP hook suffixes registered in ${MCP_FILE}"
    ;;
esac
