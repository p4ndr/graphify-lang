# T14-RunTests - Test Results

## Test Execution: graphify-lang AutoLISP against autolisp-pvcase

**Test ID**: T14-RunTests  
**Date**: 2026-09-23  
**Status**: ✅ COMPLETE

## Executive Summary

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files) with 20 test cases.

### Results: 2/20 Passing (10%)

| Metric | Value |
|:-------|------:|
| Passing | 2 |
| Partial | 6 |
| Failing | 12 |
| Pass Rate | 10% |

## What Works

### ✅ Commands Detected
All 7 commands correctly identified:
- C:PVCVER
- C:PVCRECONCILE
- C:PVCEXTRACT
- C:PVCIMPORT
- C:PVCEXPORT
- C:PVCGROUPS
- C:PVCRESTORE

### ✅ Functions Detected
~300 functions detected with AST capture.

### ✅ File Extraction
All 18 .lsp files successfully processed.

## Issues Found

### ⚠️ Function Labels Include Full Syntax
- Expected: `pvc-app:_start`
- Actual: `defun pvc-app:_start (cmd / why)`

### ⚠️ Package Literal Joining Not Working
- `err : trap` not joined to `err:trap`
- Detected as call nodes instead

### ⚠️ Source Locations Not Captured
- All show `None` instead of `L###` line numbers

### ⚠️ Module Population Not Working
- All show `N/A` instead of module names

### ❌ Global Variable Detection Not Working
- Query only matches single-pair setq
- Real code uses multi-pair setq
- Result: 0 globals detected vs ~60 expected

### ❌ Literal Extraction Not Implemented
- String/number literals not extracted as nodes

### ❌ Structural Nodes Not Extracted
- List, conditional, loop nodes not produced

## Test Case Results

| TC | Feature | Status | Details |
|:---|:--------|:-------|:--------|
| TC001 | Command C:PVCVER | ✅ PASS | Detected correctly |
| TC002 | Command C:PVCEXTRACT | ✅ PASS | Detected correctly |
| TC003 | Function pvc-app:_start | ⚠️ PARTIAL | Full defun label |
| TC004 | Function pvc-app:extract-run | ⚠️ PARTIAL | Full defun label |
| TC005 | Global *pvc-app:version* | ❌ FAIL | Not detected |
| TC006 | Global *pvc-app:undo-open* | ❌ FAIL | Not detected |
| TC007 | Global *pvc-asg:registry* | ❌ FAIL | Not detected |
| TC008 | Global *pvc-blk:def-cache* | ❌ FAIL | Not detected |
| TC009 | Package ref err:trap | ⚠️ PARTIAL | Not joined |
| TC010 | Package ref pvc-err:safe-call | ⚠️ PARTIAL | Not joined |
| TC011 | Package ref pvc-cfg:model | ⚠️ PARTIAL | Not joined |
| TC012 | Package ref pvc-log:add | ⚠️ PARTIAL | Not joined |
| TC013 | String literal | ❌ FAIL | Not extracted |
| TC014 | String literal | ❌ FAIL | Not extracted |
| TC015 | Number literal | ❌ FAIL | Not extracted |
| TC016 | List structure | ❌ FAIL | Not extracted |
| TC017 | Conditional cond | ❌ FAIL | Not extracted |
| TC018 | Loop foreach | ❌ FAIL | Not extracted |
| TC019 | Loop repeat | ❌ FAIL | File not found |
| TC020 | Built-in reference | ⚠️ PARTIAL | Not classified |

## Files Updated

The test file `docs/testing/case_001_autolisp-pvcase.md` has been updated with actual graphify-lang output for all 20 test cases.

## Documentation Created

- `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
- `docs/testing/case_001_autolisp-pvcase_test_results.md` - Summary
- `docs/testing/case_001_autolisp-pvcase_test_cases.md` - Per-case details
- `docs/testing/case_001_autolisp-pvcase_SUMMARY.md` - Final report
- `docs/testing/T14-COMPLETE.md` - Completion report
- `docs/testing/T14-RESULTS.json` - JSON summary
- `docs/testing/T14-SESSION-LOG.md` - Session log
- `docs/testing/T14-FINAL-REPORT.md` - Final report
- `docs/testing/T14-FINAL-RESULTS.json` - Final JSON
- `docs/testing/T14-OUTPUT.md` - Executive summary
- `docs/testing/T14-OUTPUT.json` - Output JSON
- `docs/testing/T14-TEST-RESULTS-JSON.json` - Test results JSON

## Recommendations

1. Update global variable query to handle multi-pair setq
2. Fix join_package_lits in extract.py
3. Add source location capture to AST extraction
4. Add string/number literal extraction rules
5. Add list/conditional/loop structural node kinds
6. Verify builtins.txt coverage for Visual LISP

## Conclusion

graphify-lang AutoLISP extractor successfully detects commands and functions but has several issues preventing complete test coverage. The test file has been updated with actual graphify-lang output for all 20 test cases, documenting real-world behavior.

---

**Status**: ✅ COMPLETE  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
