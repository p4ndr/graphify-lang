# graphify-lang AutoLISP Test - Final Report

## Test ID: T14-RunTests

## Execution Date: 2026-09-23

## Objective

Execute T14 - Test graphify-lang against autolisp-pvcase codebase and populate the "graphify-lang output" sections with actual results.

## Methodology

1. Loaded 20 test cases from `docs/testing/case_001_autolisp-pvcase.md`
2. Tested graphify-lang AutoLISP extractor against `~/repos/autolisp-pvcase/src/` (18 .lsp files)
3. Analyzed extraction output to identify working features and issues
4. Updated test file with actual results for all 20 test cases

## Results Summary

| Metric | Value |
|:-------|------:|
| Test Cases | 20 |
| Passing | 2 (10%) |
| Partial | 6 (30%) |
| Failing | 12 (60%) |
| Files Tested | 18 .lsp files |
| Commands Detected | 7 |
| Functions Detected | ~300 |
| Globals Detected | 0 |

## Working Features

1. **Command Detection** - All 7 commands correctly identified:
   - C:PVCVER, C:PVCRECONCILE, C:PVCEXTRACT, C:PVCIMPORT, C:PVCEXPORT, C:PVCGROUPS, C:PVCRESTORE

2. **Function Detection** - ~300 functions detected

3. **File Extraction** - All 18 .lsp files successfully processed

## Issues Identified

### Critical Issues

1. **Global Variable Detection** - 0 detected vs expected ~60
   - Root cause: Query only matches single-pair setq `(setq a 1)`
   - Real code uses multi-pair setq `(setq a 1 b 2 c 3)`

2. **String/Number Literal Extraction** - 0 detected
   - No rules for string/number literal node kinds

3. **Package Literal Joining** - Not working
   - `err : trap` should become `err:trap`
   - Package literals not merged

### Moderate Issues

4. **Function Labels** - Include full "defun ..." syntax
   - Expected: `pvc-app:_start`
   - Actual: `defun pvc-app:_start (cmd / why)`

5. **Module Population** - Not populated
   - All show `module: N/A`

6. **Source Locations** - All show `None`
   - Expected: `L###` line numbers

### Minor Issues

7. **Built-in References** - Not classified as references
   - Visual LISP functions detected as call nodes

## Test Case Details

| Test Case | Feature | Status | Notes |
|:----------|:--------|:-------|:------|
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

1. `docs/testing/case_001_autolisp-pvcase.md` - Test cases with actual results
2. `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
3. `docs/testing/case_001_autolisp-pvcase_test_results.md` - Summary
4. `docs/testing/case_001_autolisp-pvcase_test_cases.md` - Per-case details
5. `docs/testing/case_001_autolisp-pvcase_SUMMARY.md` - Final report
6. `docs/testing/T14-COMPLETE.md` - Completion report
7. `docs/testing/T14-RESULTS.json` - JSON summary
8. `docs/testing/T14-SESSION-LOG.md` - Session log

## Raw Output

All extraction results available at:
- `~/repos/autolisp-pvcase/src/graphify-out/graph.json`

## Recommendations

1. **Global Variables**: Update query to handle multi-pair setq
2. **Package Literals**: Fix `join_package_lits` in `extract.py`
3. **Source Locations**: Add AST capture for line numbers
4. **Module Population**: Extract from header comments or file naming
5. **Literal Extraction**: Add string/number literal rules
6. **Structural Nodes**: Add list/conditional/loop node kinds
7. **Built-ins**: Verify builtins.txt coverage for Visual LISP

## Conclusion

graphify-lang AutoLISP extractor successfully detects commands and functions but has several issues preventing complete test coverage:
- Global variable detection not working
- Literal extraction not implemented
- Package literal joining not working
- Source locations and modules not populated

The test file has been updated with actual graphify-lang output for all 20 test cases, documenting real-world behavior rather than expected behavior.

---

**Status**: ✅ COMPLETE  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
