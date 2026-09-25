# T14-RunTests - Task Completion Report

## Task: Execute T14 - Test graphify-lang against autolisp-pvcase

**Assigned**: T14-RunTests  
**Date**: 2026-09-23  
**Status**: ✅ COMPLETE

## Execution Summary

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files, ~300 functions, ~60 globals).

## Results: 2/20 Passing (10%)

### Working ✅
- Command detection: 7 commands found
- Function detection: ~300 functions found
- File extraction: All 18 .lsp files processed

### Needs Fix ⚠️
- Global variable detection: 0 detected (query issue)
- Package literal joining: Not working
- Source locations: All show "None"
- Module population: All show "N/A"

### Not Working ❌
- String/number literal extraction: Not implemented
- Structural nodes (list/conditional/loop): Not extracted

## Files Updated

1. `docs/testing/case_001_autolisp-pvcase.md` - Test cases with actual results
2. `docs/testing/T14-RESULTS.md` - Final test results report

## Key Findings

### Root Cause Analysis

**Global Variable Detection Failure**
- Query rule only matches single-pair setq: `(setq a 1)`
- Real code uses multi-pair setq: `(setq a 1 b 2 c 3)`
- Result: 0 globals detected vs ~60 expected

**Package Literal Joining**
- `err : trap` should become `err:trap`
- Not working in post_file hook

**Source Locations**
- All nodes show `None` instead of line numbers

**Module Population**
- All nodes show `N/A` instead of module names

## Recommendations

1. Update global variable query to handle multi-pair setq
2. Fix join_package_lits in extract.py
3. Add source location capture to AST extraction
4. Add string/number literal extraction rules
5. Add list/conditional/loop structural node kinds
6. Verify builtins.txt coverage for Visual LISP

## Next Steps

1. Fix the identified issues in the AutoLISP extractor
2. Re-run extraction with fixes
3. Compare output against expected results
4. Update test cases with passing results

---

**Status**: ✅ COMPLETE  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
