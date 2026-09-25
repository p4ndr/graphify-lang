# Test Case Updates for docs/testing/case_001_autolisp-pvcase.md

## TC001: Command Definition C:PVCVER ✅

**graphify-lang output** (Actual)
```json
{
  "id": "home_p4ndr_repos_autolisp_pvcase_src_pvc_app_main_c_pvcver",
  "label": "C:PVCVER",
  "name": "C:PVCVER",
  "node_kind": "command",
  "module": "N/A",
  "source_file": "src/pvc_app_main.lsp",
  "source_location": "None"
}
```

**Notes**: Commands correctly detected. 7 commands total found.

---

## TC002: Command Definition C:PVCEXTRACT ✅

**graphify-lang output** (Actual)
```json
{
  "id": "home_p4ndr_repos_autolisp_pvcase_src_pvc_app_main_c_pvextract",
  "label": "C:PVCEXTRACT",
  "name": "C:PVCEXTRACT",
  "node_kind": "command",
  "module": "N/A",
  "source_file": "src/pvc_app_main.lsp",
  "source_location": "None"
}
```

**Notes**: Commands correctly detected.

---

## TC003: Internal Function Definition pvc-app:_start ⚠️

**graphify-lang output** (Actual)
```json
{
  "id": "home_p4ndr_repos_autolisp_pvcase_src_pvc_app_main_defun_pvc_app__start_cmd__why",
  "label": "defun pvc-app:_start (cmd / why)",
  "name": "pvc-app:_start",
  "node_kind": "function",
  "module": "N/A",
  "source_file": "src/pvc_app_main.lsp",
  "source_location": "None"
}
```

**Notes**: Function detected but label includes full defun syntax. Expected just function name.

---

## TC004: Internal Function Definition pvc-app:extract-run ⚠️

**graphify-lang output** (Actual)
```json
{
  "id": "home_p4ndr_repos_autolisp_pvcase_src_pvc_app_main_defun_pvc_app_extract_run_model_",
  "label": "defun pvc-app:extract-run (model / why path t0 refs recs csv)",
  "name": "pvc-app:extract-run",
  "node_kind": "function",
  "module": "N/A",
  "source_file": "src/pvc_app_main.lsp",
  "source_location": "None"
}
```

**Notes**: Function detected but label includes full defun syntax.

---

## TC005: Global Variable *pvc-app:version* ❌

**graphify-lang output** (Actual)
```json
{
  "error": "global node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(setq *pvc-app:version* \"0.0.19\")"
    }
  ]
}
```

**Notes**: Global variables not detected. The setq is captured as a call node, not a global node. Query rule only matches single-pair setq forms.

---

## TC006: Global Variable *pvc-app:undo-open* ❌

**graphify-lang output** (Actual)
```json
{
  "error": "global node kind not found"
}
```

**Notes**: Same issue - globals not detected.

---

## TC007: Global Variable *pvc-asg:registry* ❌

**graphify-lang output** (Actual)
```json
{
  "error": "global node kind not found"
}
```

---

## TC008: Global Variable *pvc-blk:def-cache* ❌

**graphify-lang output** (Actual)
```json
{
  "error": "global node kind not found"
}
```

---

## TC009: Package Literal Reference err:trap ⚠️

**graphify-lang output** (Actual)
```json
{
  "error": "No reference.call node found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(err:trap 'PVC-APP 'vla-get-ActiveDocument (list (vlax-get-acad-object)))"
    }
  ]
}
```

**Notes**: Package literals not properly joined. The err:trap call is detected as a call node.

---

## TC010: Package Literal Reference pvc-err:safe-call ⚠️

**graphify-lang output** (Actual)
```json
{
  "error": "No reference.call node found"
}
```

---

## TC011: Package Literal Reference pvc-cfg:model ⚠️

**graphify-lang output** (Actual)
```json
{
  "error": "No reference.call node found"
}
```

---

## TC012: Package Literal Reference pvc-log:add ⚠️

**graphify-lang output** (Actual)
```json
{
  "error": "No reference.call node found"
}
```

---

## TC013: String Literal in pvc-app:_ask ❌

**graphify-lang output** (Actual)
```json
{
  "error": "string node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(strcat \"\\nSpecify [E]xtract/[R]econcile <E>: \")"
    }
  ]
}
```

**Notes**: String literals not extracted. String is captured inside call node.

---

## TC014: String Literal in pvc-app:_folder ❌

**graphify-lang output** (Actual)
```json
{
  "error": "string node kind not found"
}
```

---

## TC015: Number Literal in pvc-app:_ask ❌

**graphify-lang output** (Actual)
```json
{
  "error": "number node kind not found"
}
```

---

## TC016: List Structure in pvc-cfg:schema ❌

**graphify-lang output** (Actual)
```json
{
  "error": "list node kind not found"
}
```

---

## TC017: Conditional Expression cond ❌

**graphify-lang output** (Actual)
```json
{
  "error": "conditional node kind not found"
}
```

---

## TC018: Loop Construct foreach ❌

**graphify-lang output** (Actual)
```json
{
  "error": "loop node kind not found"
}
```

---

## TC019: Loop Construct repeat ❌

**graphify-lang output** (Actual)
```json
{
  "error": "File not found: tests/lang/fixtures/src/core/ldr.lsp"
}
```

**Notes**: Test references fixture file not in src/ directory.

---

## TC020: Visual LISP Reference vl-catch-all-apply ❌

**graphify-lang output** (Actual)
```json
{
  "error": "reference.call node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(vl-catch-all-apply 'log:add (list sym flag log-msg msg-pred))"
    }
  ]
}
```

**Notes**: Built-in Visual LISP functions not detected as references. Detected as call nodes.

---

## Summary Table

| Test Case | Expected | Actual | Status |
|:----------|:---------|:-------|:-------|
| TC001 | command C:PVCVER | command C:PVCVER | ✅ PASS |
| TC002 | command C:PVCEXTRACT | command C:PVCEXTRACT | ✅ PASS |
| TC003 | function pvc-app:_start | function (full defun label) | ⚠️ PARTIAL |
| TC004 | function pvc-app:extract-run | function (full defun label) | ⚠️ PARTIAL |
| TC005 | global *pvc-app:version* | No global nodes | ❌ FAIL |
| TC006 | global *pvc-app:undo-open* | No global nodes | ❌ FAIL |
| TC007 | global *pvc-asg:registry* | No global nodes | ❌ FAIL |
| TC008 | global *pvc-blk:def-cache* | No global nodes | ❌ FAIL |
| TC009 | reference.err:trap | call node | ⚠️ PARTIAL |
| TC010 | reference.pvc-err:safe-call | call node | ⚠️ PARTIAL |
| TC011 | reference.pvc-cfg:model | call node | ⚠️ PARTIAL |
| TC012 | reference.pvc-log:add | call node | ⚠️ PARTIAL |
| TC013 | string literal | No string nodes | ❌ FAIL |
| TC014 | string literal | No string nodes | ❌ FAIL |
| TC015 | number literal | No number nodes | ❌ FAIL |
| TC016 | list structure | No list nodes | ❌ FAIL |
| TC017 | conditional | No conditional nodes | ❌ FAIL |
| TC018 | loop (foreach) | No loop nodes | ❌ FAIL |
| TC019 | loop (repeat) | File not found | ❌ FAIL |
| TC020 | reference (built-in) | call node | ⚠️ PARTIAL |

## Pass Rate: 2/20 (10%) - Commands only

## Critical Issues

1. **Global Variable Detection**: Query only handles single-pair setq
2. **String/Number Literals**: No literal extraction rules active
3. **Package Literal Joining**: `err:trap` etc. not merged into single symbols
4. **Source Locations**: All show `None` instead of line numbers
5. **Module Population**: All show `N/A` instead of module names

## Next Steps

1. Fix global variable query to handle multi-pair setq
2. Add literal extraction rules for strings and numbers
3. Fix package literal joining in post_file hook
4. Investigate why source locations and modules not populated
5. Add conditional, loop, list node kinds
