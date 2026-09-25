# graphify-lang AutoLISP Test - Complete

## Summary

Test execution completed. graphify-lang AutoLISP extractor was tested against the `autolisp-pvcase` codebase (18 .lsp files).

## Test Results

| Category | Passing | Partial | Failing |
|:---------|:-------:|:-------:|:-------:|
| Commands | 2 | 0 | 0 |
| Functions | 0 | 2 | 0 |
| Globals | 0 | 0 | 4 |
| References | 0 | 4 | 0 |
| Literals | 0 | 0 | 3 |
| Structures | 0 | 0 | 6 |
| **Total** | **2/20 (10%)** | **6/20** | **12/20** |

## Key Findings

### ✅ Working
- Command detection correctly identifies C:PVCVER, C:PVCEXTRACT, and 5 other commands
- Function definitions are detected with AST capture

### ⚠️ Needs Fix
- Function labels include full defun syntax instead of just names
- Module population not working (shows "N/A")
- Source locations not populated (shows "None")
- Global variables not detected (query only matches single-pair setq)
- Package literals not properly joined
- String/number literals not extracted
- List/conditional/loop structural nodes not extracted
- Built-in Visual LISP functions not classified

### ❌ Failing
- Global variable detection: 0 detected vs expected ~60
- String/number literal extraction: 0 detected
- List/conditional/loop structure extraction: 0 detected
- Package literal joining: Not working
- Built-in reference classification: Not working

## Files Modified

1. `docs/testing/case_001_autolisp-pvcase.md` - Test cases updated with actual results
2. `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
3. `docs/testing/case_001_autolisp-pvcase_test_results.md` - Summary
4. `docs/testing/case_001_autolisp-pvcase_test_cases.md` - Per-case details
5. `docs/testing/case_001_autolisp-pvcase_SUMMARY.md` - Final report

## Raw Output Location

All extraction results available at:
- `~/repos/autolisp-pvcase/src/graphify-out/graph.json`

## Next Steps

To improve test coverage:
1. Fix global variable query to handle multi-pair setq
2. Fix package literal joining in post_file hook
3. Add literal extraction rules
4. Add structural node kinds (list, conditional, loop)
5. Verify source location capture
6. Verify module population

---

**Status**: Documentation complete. Test file updated with actual graphify-lang output.  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
