# graphify-lang AutoLISP Test Results Summary

## Test Execution Date: 2026-09-23

## Overview

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files).

## Key Findings

### ✅ Working Features

| Feature | Status | Details |
|:--------|:-------|:--------|
| Command Detection | Working | 7 commands found: C:PVCVER, C:PVCRECONCILE, C:PVCEXTRACT, C:PVCIMPORT, C:PVCEXPORT, C:PVCGROUPS, C:PVCRESTORE |
| Function Detection | Working | ~300 functions detected with full defun syntax in label |
| File Extraction | Working | All 18 .lsp files extracted |

### ⚠️ Partial/Needs Fix

| Feature | Issue | Impact |
|:--------|:------|:-------|
| Module Population | `N/A` in output | Module metadata not populated |
| Source Location | `None` instead of `L###` | AST capture line numbers not populated |
| Function Labels | Full "defun ..." syntax | Expected: just function name |
| Global Variables | 0 detected | Query only handles single-pair setq |
| Package Literals | Not joined | `err:trap` not detected as single symbol |
| String/Number Literals | Not extracted | No literal nodes produced |

### ❌ Not Working

| Feature | Expected | Actual |
|:--------|:---------|:-------|
| Global Variable Detection | 60+ globals | 0 detected |
| Reference.Call Nodes | Package refs like `err:trap` | Not matched |
| String Literal Nodes | String values | Not extracted |
| Number Literal Nodes | Numeric values | Not extracted |
| List Structure Nodes | S-expression lists | Not extracted |
| Conditional Nodes | `cond` branches | Not extracted |
| Loop Nodes | `foreach`, `repeat` | Not extracted |

## Test Case Results

### TC001-TC002: Commands ✅
- **Status**: PASS
- **Details**: Commands correctly detected and classified

### TC003-TC004: Functions ⚠️
- **Status**: PARTIAL
- **Details**: Functions found but label includes full "defun ..." syntax
- **Example**: `defun pvc-app:_start (cmd / why)` instead of just `pvc-app:_start`

### TC005-TC008: Globals ❌
- **Status**: FAIL
- **Details**: No global nodes detected despite setq forms existing
- **Root Cause**: Query rule `(list_lit . (sym_lit) @kw (#eq? @kw "setq") . (sym_lit) @name)` only matches single-pair setq, not multi-pair forms like `(setq a 1 b 2 c 3)`

### TC009-TC012: References ⚠️
- **Status**: PARTIAL
- **Details**: Package literals not properly joined into single symbol nodes

### TC013-TC015: Literals ❌
- **Status**: FAIL
- **Details**: No string or number literal nodes produced

### TC016-TC020: Structures ❌
- **Status**: FAIL
- **Details**: No list, conditional, or loop nodes produced

## Statistics

- Total files: 18 .lsp files
- Total nodes: 25,000 - 306,000 per file (includes many call nodes)
- Commands: 7
- Functions: ~300
- Globals: 0 (expected ~60)
- String literals: 0 (expected ~100+)
- Built-in references: 0 (expected 100+)

## Recommendations

1. **Global Variables**: Update query to handle multi-pair setq forms
2. **Module Population**: Add module extraction from header comments or file naming
3. **Source Locations**: Fix AST capture to include line numbers
4. **Function Labels**: Strip "defun " prefix from labels
5. **Package Literals**: Fix `join_package_lits` in post_file hook
6. **String/Number Literals**: Add literal extraction rules
7. **List/Conditional/Loop**: Add structural node kinds
8. **Built-ins**: Verify builtins.txt coverage for Visual LISP

## Files Generated

- `docs/testing/case_001_autolisp-pvcase_results.md` - Detailed analysis
- `docs/testing/case_001_autolisp-pvcase_test_results.md` - This summary

## Raw Data

All extraction results available at:
- `~/repos/autolisp-pvcase/src/graphify-out/graph.json`
