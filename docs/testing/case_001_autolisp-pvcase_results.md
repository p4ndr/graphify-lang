# graphify-lang Test Results for autolisp-pvcase

## Summary

Tested graphify-lang AutoLISP extractor against autolisp-pvcase codebase (18 .lsp files).

## Results

### Passing Test Cases

| Test Case | Node Type | Status | Details |
|:----------|:----------|:-------|:--------|
| TC001 | command (C:PVCVER) | ✅ PASS | Found 7 commands total in pvc_app_main.lsp |
| TC002 | command (C:PVCEXTRACT) | ✅ PASS | Found 7 commands total in pvc_app_main.lsp |
| TC003 | function (pvc-app:_start) | ⚠️ PARTIAL | Label includes full defun syntax: "defun pvc-app:_start..." |
| TC004 | function (pvc-app:extract-run) | ⚠️ PARTIAL | Label includes full defun syntax: "defun pvc-app:extract-run..." |

### Issues Found

| Test Case | Expected | Actual | Issue |
|:----------|:---------|:-------|:------|
| TC005-TC008 | global nodes | No global nodes detected | Query rule for `setq` only captures simple single-pair forms, not multi-pair or complex setq |
| TC009-TC012 | reference.call nodes | Call nodes detected but not properly classified | Package literals (err:trap, pvc-err:safe-call, etc.) not joined correctly |
| TC013-TC015 | string/number literals | Not detected | No string/number literal extraction rules active |
| TC016 | list structure | Not detected | No list node kind being extracted |
| TC017 | conditional (cond) | Not detected | No conditional node kind being extracted |
| TC018 | loop (foreach) | Not detected | No loop node kind being extracted |
| TC019 | loop (repeat) | File not found | Test references fixture in tests/lang/fixtures/ not src/ |
| TC020 | reference.call (vl-catch-all-apply) | Built-in not detected | Built-in Visual LISP functions not in builtins.txt or not matched |

## Detailed Findings

### Command Detection (Working ✅)
- Query rule correctly identifies `C:` prefixed functions as commands
- 7 commands found: C:PVCVER, C:PVCRECONCILE, C:PVCEXTRACT, C:PVCIMPORT, C:PVCEXPORT, C:PVCGROUPS, C:PVCRESTORE

### Function Detection (Partial ⚠️)
- Function definitions are detected but labels include full defun syntax
- Query captures: `defun pvc-app:_start (cmd / why)` not just `pvc-app:_start`
- Expected behavior per TC003-TC004: label should be function name only

### Global Variable Detection (Not Working ❌)
- Query rule expects: `(list_lit . (sym_lit) @kw (#eq? @kw "setq") . (sym_lit) @name)`
- Actual AutoLISP uses multi-pair setq: `(setq a 1 b 2 c 3)`
- Result: 0 global nodes detected, only `call` or `definition` nodes

### Package Literal Detection (Partial ⚠️)
- `err:trap`, `pvc-err:safe-call`, `pvc-cfg:model` etc. not properly joined
- Some `package_lit` nodes exist but not correctly merged into single symbol

### String/Number Literals (Not Working ❌)
- No literal node kinds being extracted
- String literals like "Specify [E]xtract/[R]econcile <E>: " not captured

### List/Conditional/Loop (Not Working ❌)
- No list, conditional, or loop node kinds in output
- Only `call`, `function`, `command` node kinds detected

### Built-in Functions (Not Working ❌)
- `vl-catch-all-apply` and other Visual LISP builtins not matched
- builtins.txt may need update or regex rules missing

## Extraction Statistics

Total files: 18 .lsp files  
Total nodes per file range: 25,000 - 306,000 (includes many `call` nodes)  
Commands: 7 total (all in pvc_app_main.lsp)  
Functions: ~300 total  
Globals: 0 detected  

## Recommendations

1. Update global variable query to handle multi-pair setq
2. Fix package literal joining in post_file hook
3. Add string/number literal extraction rules
4. Add list/conditional/loop node kinds
5. Verify builtins.txt coverage for Visual LISP functions
