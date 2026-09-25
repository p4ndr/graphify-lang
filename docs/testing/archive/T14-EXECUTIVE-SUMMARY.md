# T14-RunTests - Executive Summary

## Test Execution: graphify-lang AutoLISP against autolisp-pvcase

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

## What Works ✅
- Command detection (7 commands)
- Function detection (~300 functions)
- File extraction (18 .lsp files)

## What Needs Fix ⚠️
- Global variable detection (query issue)
- Package literal joining
- String/number literal extraction
- Source location capture
- Module population

## Files Updated

The test file `docs/testing/case_001_autolisp-pvcase.md` has been updated with actual graphify-lang output for all 20 test cases.

## Output Files

- `docs/testing/case_001_autolisp-pvcase.md` - Updated test file
- `docs/testing/T14-OUTPUT.md` - Executive summary
- `docs/testing/T14-OUTPUT.json` - JSON results

---

**Status**: Documentation complete. Test file populated with actual results.  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
