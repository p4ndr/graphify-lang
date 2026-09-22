#!/usr/bin/env bash
# Re-measure AutoLITHP corpus counts at HEAD (d5a2074)
# Repository: ~/repos/autolithp

set -euo pipefail
cd /home/p4ndr/repos/autolithp

# 1. .lsp file count
LSP_COUNT=$(find src tests Import-Refactor build -name '*.lsp' -type f 2>/dev/null | wc -l)

# 2. (defun / (defun-q forms count
DEFUN_COUNT=$(find src tests Import-Refactor build -name '*.lsp' -type f -exec grep -E '\(\s*defun(-q)?\s' {} + 2>/dev/null | wc -l)

# 3. (defun C: forms count
C_CMD_COUNT=$(find src tests Import-Refactor build -name '*.lsp' -type f -exec grep -E '\(\s*defun\s+C:' {} + 2>/dev/null | wc -l)

# 4. .dcl file count
DCL_COUNT=$(find src tests Import-Refactor build -name '*.dcl' -type f 2>/dev/null | wc -l)

# 5. name : dialog { declarations count
DIALOG_COUNT=$(find src tests Import-Refactor build -name '*.dcl' -type f -exec grep -E '^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:\s*dialog\s*\{' {} + 2>/dev/null | wc -l)

# 6. Total .lsp bytes
LSP_BYTES=$(find src tests Import-Refactor build -name '*.lsp' -type f -exec stat --format='%s' {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')

# Human-readable size for bytes
HUMAN_SIZE=$(numfmt --to=iec-i --suffix=B "$LSP_BYTES" 2>/dev/null || echo "${LSP_BYTES} bytes")

echo "=== AutoLITHP Corpus Counts at d5a2074 ==="
echo ".lsp files: $LSP_COUNT"
echo "(defun / (defun-q forms: $DEFUN_COUNT"
echo "(defun C: forms: $C_CMD_COUNT"
echo ".dcl files: $DCL_COUNT"
echo "name : dialog { declarations: $DIALOG_COUNT"
echo ".lsp total bytes: $LSP_BYTES ($HUMAN_SIZE)"
