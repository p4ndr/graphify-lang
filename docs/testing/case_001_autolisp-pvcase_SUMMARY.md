# graphify-lang AutoLISP Test Summary

## Execution Date: 2026-09-23

## Test Execution

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files).

## Results Overview

| Category | Count |
|:---------|------:|
| Test Cases | 20 |
| Passing | 2 (TC001-TC002 - Commands) |
| Partial | 6 (TC003-TC004, TC009-TC012) |
| Failing | 12 (TC005-TC008, TC013-TC020) |
| **Pass Rate** | **10%** |

## Key Findings

### ✅ Working Features

1. **Command Detection** - 7 commands correctly identified
   - C:PVCVER, C:PVCRECONCILE, C:PVCEXTRACT, C:PVCIMPORT, C:PVCEXPORT, C:PVCGROUPS, C:PVCRESTORE

2. **Function Detection** - ~300 functions detected with AST capture

3. **File Extraction** - All 18 .lsp files successfully processed

### ⚠️ Partial/Needs Fix

1. **Function Labels** - Include full "defun ..." syntax instead of just function name
2. **Module Population** - Not populated (shows "N/A")
3. **Source Locations** - All show "None" instead of line numbers
4. **Package Literal Joining** - `err:trap` etc. not merged into single symbols
5. **Global Variables** - Query only matches single-pair setq, not multi-pair forms
6. **String/Number Literals** - No literal nodes produced
7. **List/Conditional/Loop Nodes** - Structural node kinds not extracted

### ❌ Not Working

1. **Global Variable Detection** - 0 globals detected vs expected ~60
2. **Literal Extraction** - String/number literals not captured as nodes
3. **Built-in References** - Visual LISP functions not classified as references

## Test Case Status

| TC | Feature | Status | Notes |
|:---|:--------|:-------|:------|
| TC001 | Command C:PVCVER | ✅ PASS | Detected correctly |
| TC002 | Command C:PVCEXTRACT | ✅ PASS | Detected correctly |
| TC003 | Function pvc-app:_start | ⚠️ PARTIAL | Full defun label |
| TC004 | Function pvc-app:extract-run | ⚠️ PARTIAL | Full defun label |
| TC005 | Global *pvc-app:version* | ❌ FAIL | Not detected |
| TC006 | Global *pvc-app:undo-open* | ❌ FAIL | Not detected |
| TC007 | Global *pvc-asg:registry* | ❌ FAIL | Not detected |
| TC008 | Global *pvc-blk:def-cache* | ❌ FAIL | Not detected |
| TC009-TC012 | Package refs | ⚠️ PARTIAL | Not joined |
| TC013-TC015 | Literals | ❌ FAIL | Not extracted |
| TC016-TC020 | Structures | ❌ FAIL | Not extracted |

## Files Updated

1. `docs/testing/case_001_autolisp-pvcase.md` - Test cases updated with actual results
2. `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
3. `docs/testing/case_001_autolisp-pvcase_test_results.md` - Summary
4. `docs/testing/case_001_autolisp-pvcase_test_cases.md` - Per-case details

## Extraction Statistics

- Total files: 18 .lsp files
- Total nodes: 25,000 - 306,000 per file (many call nodes)
- Commands: 7
- Functions: ~300
- Globals: 0 (expected ~60)
- Built-in refs: 0 (expected 100+)

## Root Causes Identified

1. **Global Variables**: Query rule only matches single-pair setq
   ```toml
   (setq a 1 b 2)  # Not matched
   (setq a 1)       # Matched but not in codebase
   ```

2. **Package Literals**: Not properly joined in post_file hook

3. **Source Locations**: AST capture not populating line numbers

4. **Literal Extraction**: No rules for string/number nodes

## Recommendations

1. Update global variable query to handle multi-pair setq
2. Fix `join_package_lits` in `extract.py` for package literal merging
3. Add source location capture in AST extraction
4. Add string/number literal extraction rules
5. Add list/conditional/loop structural node kinds
6. Verify builtins.txt coverage for Visual LISP functions

## Next Steps

To complete the test suite:
1. Fix identified issues in the AutoLISP extractor
2. Re-run extraction with fixes
3. Compare output against expected results
4. Update test cases with passing results

---

**Report Generated**: 2026-09-23  
**Tested By**: T14-RunTests  
**Status**: Documentation Complete
