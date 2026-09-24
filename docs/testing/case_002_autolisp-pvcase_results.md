# graphify-lang Test Results for autolisp-pvcase (Case 002)

**Date:** 2026-09-24  
**Status:** T17 fixes applied  
**Comparison:** Case 002 vs Case 001  
**Test Run:** 5468 passed, 12 skipped, 6 warnings in 65.55s

## Summary

Tested updated graphify-lang AutoLISP extractor against autolisp-pvcase codebase (18 .lsp files).

### T17 Fixes Applied
- `graphify_lang/regex_rules.py`: Added `kind == "regex"` filter to avoid processing query rules with empty patterns
- `graphify_lang/autolisp/extract.py`: Added `fix_function_labels()` to extract just function name from labels
- `graphify_lang/autolisp/extract.py`: Added `fix_global_labels()` to extract just variable name from global nodes

## Results

### Passing Test Cases

| Test Case | Node Type | Status | Details |
|:----------|:----------|:-------|:--------|
| TC001 | command (C:PVCVER) | ✅ PASS | Command detected with correct label `C:PVCVER` |
| TC002 | command (C:PVCEXTRACT) | ✅ PASS | Command detected with correct label `C:PVCEXTRACT` |
| TC003 | function (pvc-app:_start) | ✅ PASS | Label now shows just `pvc-app:_start` (was `defun pvc-app:_start (...)`) |
| TC004 | function (pvc-app:extract-run) | ✅ PASS | Label now shows just `pvc-app:extract-run` (was `defun pvc-app:extract-run (...)`) |
| TC005-TC008 | global (*pvc-*) | ✅ PASS | Global variables detected with correct variable names |
| TC009-TC012 | reference.call | ✅ PASS | Package literals properly joined (err:trap, pvc-err:safe-call, etc.) |
| All tests | Full suite | ✅ PASS | 5468 passed, 12 skipped |

### Issues Fixed (vs Case 001)

| Issue | Case 001 | Case 002 | Fix |
|:------|:---------|:---------|:----|
| Function labels | Full `defun ...` syntax | Just function name | `fix_function_labels()` |
| Global variable labels | Full `(setq ...)` form | Just variable name | `fix_global_labels()` |
| Global detection | 0 global nodes | ~60 globals detected | Already working, labels fixed |

### Remaining Issues

| Test Case | Expected | Actual | Issue |
|:----------|:---------|:-------|:------|
| TC013-TC015 | string/number literals | Not detected | No string/number literal extraction rules |
| TC016 | list structure | Not detected | No list node kind being extracted |
| TC017 | conditional (cond) | Not detected | No conditional node kind being extracted |
| TC018 | loop (foreach) | Not detected | No loop node kind being extracted |
| TC019 | reference.call (vl-catch-all-apply) | Built-in not detected | builtins.txt coverage needs update |

## Extraction Statistics

| Metric | Count |
|:-------|:------|
| Files | 18 .lsp files |
| Nodes per file range | 25,000 - 306,000 |
| Commands | 7 total (all in pvc_app_main.lsp) |
| Functions | ~300 total |
| Globals | ~60 detected |

## Before/After Comparison

### Function Labels
- **Before (T17.4 issue):** `defun pvc-app:_start (cmd / why)`  
- **After:** `pvc-app:_start` ✅

### Global Variable Labels  
- **Before:** `(setq *pvc-app:version* "0.0.18")`  
- **After:** `*pvc-app:version*` ✅

### Global Detection
- **Before:** 0 global nodes  
- **After:** ~60 global nodes detected ✅

## Recommendations

1. Add string/number literal extraction rules (T17.2 partial)
2. Add list/conditional/loop node kinds
3. Verify builtins.txt coverage for Visual LISP functions

---

**Next:** T18.6 - Compare case_001 and case_002 results to verify T17 fixes are working
