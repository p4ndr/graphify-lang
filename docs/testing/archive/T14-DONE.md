# T14-RunTests - Task Complete

**Status**: ✅ COMPLETE  
**Date**: 2026-09-23  
**Test ID**: T14-RunTests

## Summary

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files, 20 test cases).

## Results

| Metric | Value |
|:-------|------:|
| Passing | 2/20 (10%) |
| Partial | 6/20 (30%) |
| Failing | 12/20 (60%) |

## Working ✅
- Command detection
- Function detection
- File extraction

## Needs Fix ⚠️
- Global variable detection
- Package literal joining
- Source locations
- Module population

## Not Working ❌
- Literal extraction
- Structural nodes

## Files Updated
- `docs/testing/case_001_autolisp-pvcase.md` - Test cases with actual results

---

**Test ID**: T14-RunTests  
**Status**: COMPLETE  
**Date**: 2026-09-23
