# T14-RunTests - Final Summary

## Task Complete: Test graphify-lang against autolisp-pvcase

**Test ID**: T14-RunTests  
**Date**: 2026-09-23  
**Status**: ✅ COMPLETE

## Results

| Metric | Value |
|:-------|------:|
| Test Cases | 20 |
| Passing | 2 (10%) |
| Partial | 6 (30%) |
| Failing | 12 (60%) |

## What Works

✅ Command detection (7 commands)  
✅ Function detection (~300 functions)  
✅ File extraction (18 .lsp files)

## What Needs Fix

⚠️ Global variable detection (query issue)  
⚠️ Package literal joining (not working)  
⚠️ Source locations (all None)  
⚠️ Module population (all N/A)

## Not Working

❌ String/number literal extraction  
❌ Structural nodes (list/conditional/loop)  
❌ Built-in reference classification  

## Files Updated

- `docs/testing/case_001_autolisp-pvcase.md` - Test cases with actual results
- `docs/testing/T14-RESULTS.md` - Test results report
- `docs/testing/T14-REPORT.md` - Completion report
- `docs/testing/T14-FINAL.json` - Final JSON
- `docs/testing/T14-COMPLETED.md` - Completion note
- `docs/testing/T14-FINAL-RESULT.json` - Final result JSON

## Key Finding

The global variable query only matches single-pair setq forms `(setq a 1)` but real code uses multi-pair setq `(setq a 1 b 2 c 3)`, causing 0 globals to be detected vs ~60 expected.

---

**Status**: ✅ COMPLETE  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
