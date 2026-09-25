# Test Case 001: autolisp-pvcase - Execution Log

## Session: T14-RunTests

## Goal
Execute T14 - Test graphify-lang against autolisp-pvcase codebase

## Steps Performed

1. **Read Test Cases** - Loaded test file `docs/testing/case_001_autolisp-pvcase.md` with 20 test cases

2. **Check graphify Availability** - Confirmed graphify 0.9.55 available at `/home/p4ndr/.local/bin/graphify`

3. **Test AutoLISP Plugin Loading** - Verified plugin loads correctly:
   - Manifest: autolisp
   - Suffixes: .lsp, .mnl
   - Registered: autolisp, autolisp-dcl

4. **Run Extraction** - Tested extraction with deep mode
   - Output: 306,767 nodes for pvc_app_main.lsp
   - Commands found: 7
   - Functions found: 44
   - Globals found: 0 ❌

5. **Analyze Extraction** - Discovered issues:
   - Commands: Working ✅
   - Functions: Working but labels include "defun" prefix ⚠️
   - Globals: Not working - query only matches single-pair setq ❌
   - Package literals: Not joined properly ⚠️
   - Literals: Not extracted ❌
   - Source locations: All None ❌
   - Modules: All N/A ❌

6. **Generate Results** - Created detailed test results documenting actual behavior

7. **Update Test File** - Updated `case_001_autolisp-pvcase.md` with actual graphify-lang output for all 20 test cases

8. **Create Documentation** - Created summary files documenting findings

## Test Results Summary

| Test Case | Feature Tested | Expected | Actual | Status |
|:----------|:---------------|:---------|:-------|:-------|
| TC001 | Command C:PVCVER | command | command | ✅ |
| TC002 | Command C:PVCEXTRACT | command | command | ✅ |
| TC003 | Function pvc-app:_start | function | function (full label) | ⚠️ |
| TC004 | Function pvc-app:extract-run | function | function (full label) | ⚠️ |
| TC005-TC008 | Global variables | global | Not found | ❌ |
| TC009-TC012 | Package refs | reference.call | call | ⚠️ |
| TC013-TC015 | Literals | string/number | Not found | ❌ |
| TC016-TC020 | Structures | list/conditional/loop | Not found | ❌ |

## Key Findings

### Root Cause Analysis

1. **Global Variable Detection Failure**
   - Query: `(setq a 1)` matches
   - Real code: `(setq a 1 b 2 c 3)` does NOT match
   - Result: 0 globals detected vs ~60 expected

2. **Package Literal Joining**
   - `err : trap` should become `err:trap`
   - Not working in post_file hook

3. **Source Location**
   - All nodes show `source_location: None`
   - AST capture not populating line numbers

4. **Module Population**
   - All nodes show `module: N/A`
   - Not populated from header comments or file naming

## Output Files

- `docs/testing/case_001_autolisp-pvcase.md` - Updated with actual results
- `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
- `docs/testing/case_001_autolisp-pvcase_test_results.md` - Summary
- `docs/testing/case_001_autolisp-pvcase_test_cases.md` - Per-case details
- `docs/testing/case_001_autolisp-pvcase_SUMMARY.md` - Final report
- `docs/testing/T14-COMPLETE.md` - Completion report
- `docs/testing/T14-RESULTS.json` - JSON summary

## Recommendations

1. Update global variable query to handle multi-pair setq
2. Fix package literal joining in post_file hook
3. Add source location capture to AST extraction
4. Add string/number literal extraction rules
5. Add list/conditional/loop structural node kinds
6. Verify builtins.txt coverage for Visual LISP

## Session Status

✅ **COMPLETE** - Test documentation complete. Test file updated with actual graphify-lang behavior.
