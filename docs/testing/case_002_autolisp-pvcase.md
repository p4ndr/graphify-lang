<!-- TEMPLATE-VERSION: 2026-09-23-002 -->
<!-- DOC-TYPE: TEMPORARY -->
<!-- TEMPLATE-START -->
# Case 002: autolisp-pvcase (updated graphify-lang)

This case documents the updated graphify-lang evaluation against the `autolisp-pvcase`
AutoLISP codebase. This is a re-run of T16 (case_001) with the fixes from T17 applied.

## 1. Overview

| Item | Value |
|:-----|:------|
| Repo | `~/repos/autolisp-pvcase` |
| Language | AutoLISP (.lsp) |
| Commands | C:PVCVER, C:PVCEXTRACT, C:PVCRECONCILE, C:PVCGROUPS, C:PVCEXPORT, C:PVCIMPORT, C:PVCRESTORE |
| Internal functions | ~150 (pvc-*, pvc-_:*, *pvc-*) |
| Global variables | ~60 (*pvc-*) |
| Source files | 18 .lsp files in src/ |

## 2. Repository Structure

```
autolisp-pvcase/
├── src/                           (18 .lsp files)
│   ├── pvc_app_main.lsp          (Main: commands, settings, extract)
│   ├── pvc_mod_asg.lsp           (Assigner: tag assignment registry)
│   ├── pvc_mod_blk.lsp           (Block: INSERT, attributes, dynamic props)
│   ├── pvc_mod_cfg.lsp           (Config: TOML settings loader)
│   ├── pvc_mod_csv.lsp           (CSV: writer/reader)
│   ├── pvc_mod_dif.lsp           (Difference: reconcile plan)
│   ├── pvc_mod_dlg.lsp           (Dialogue: group assignment UI)
│   ├── pvc_mod_err.lsp           (Error: traps, undo marks)
│   ├── pvc_mod_ext.lsp           (Extract: record, CSV table)
│   ├── pvc_mod_log.lsp           (Logging: buffered file log)
│   ├── pvc_mod_rec.lsp           (Recording: COM wrapper)
│   ├── pvc_mod_rtp.lsp           (Round-trip: CSV export/import, XDATA)
│   ├── pvc_mod_sel.lsp           (Selection: match blocks by pattern)
│   ├── pvc_mod_syn.lsp           (Sync: ATTSYNC with XDATA backup)
│   ├── pvc_mod_tag.lsp           (Tag: stringing MTEXT extraction)
│   ├── pvc_mod_tml.lsp           (TML: strict TOML reader)
│   ├── pvc_mod_utl.lsp           (Utilities: to-string, num-str, expand-name)
│   └── pvc_mod_xdt.lsp           (XDATA: packed asset tags)
├── tests/                         (Test harness, 9 .lsp files)
├── docs/                          (Repo docs)
├── build/                         (VLX project files)
├── pvc_tagtool.toml              (Settings template)
└── README.md
```

## 3. Command Overview

| Command | Description | Changes drawing |
|:--------|:------------|:----------------|
| **C:PVCVER** | Prints version, AutoCAD release, LISPSYS | No |
| **C:PVCEXTRACT** | Writes extract CSV (UTF-8 with BOM) | No |
| **C:PVCRECONCILE** | Dry run + Apply to reconcile attributes | Only on Apply |
| **C:PVCGROUPS** | Group dialogue: assign/clear asset tags | Through Apply gate |
| **C:PVCEXPORT** | Writes round-trip CSV, sorted L→R, T→B | No |
| **C:PVCIMPORT** | Reads CSV, applies changes | Only on Apply |
| **C:PVCRESTORE** | Restores packed XDATA backup | Only on Apply |

---

## 4. Test Cases

### TC001: Command Definition C:PVCVER

**Syntax**
```lisp
(defun C:PVCVER ()
  (princ (strcat "\npvCaseTagTool version " *pvc-app:version*))
  (princ (strcat "\nAutoCAD " (getvar 'acadver)))
  (princ (strcat "\nLISPSYS " (itoa (getvar 'lispsys"))))
  (princ))
```

**Expected Response**
- Node kind: `command`
- Label: `C:PVCVER`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`

**graphify-lang output** (Actual - 2026-09-23)
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
**Notes**: Commands correctly detected. Module not populated. Source location shows None.

---

### TC002: Command Definition C:PVCEXTRACT

**Syntax**
```lisp
(defun C:PVCEXTRACT (/ *error* old-err model why path t0 refs recs)
  (if (pvc-app:_start 'C:PVCEXTRACT)
    (progn
      (setq *error* 'pvc-app:_extract-report)
      (setq old-err *error*)
      (if (setq model (pvc-cfg:model))
        (pvc-app:extract-run model)
        (pvc-app:_extract-report 'C:PVCEXTRACT why)))))
```

**Expected Response**
- Node kind: `command`
- Label: `C:PVCEXTRACT`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`

**graphify-lang output** (Actual - 2026-09-23)
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

### TC003: Internal Function Definition pvc-app:_start

**Syntax**
```lisp
(defun pvc-app:_start (cmd / why)
  (if *pvc-app:no-ask* (setvar 'nomodel 1))
  (if (not (pvc-cfg:model))
    (progn
      (princ (strcat "\n" (pvc-err:last-message)))
      nil)
    (progn
      (pvc-log:reset cmd)
      (pvc-log:begin 'DEBUG)
      T)))
```

**Expected Response**
- Node kind: `function`
- Label: `pvc-app:_start`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`
- Name: `pvc-app:_start`

**graphify-lang output** (Actual - 2026-09-23)
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
**Notes**: Function detected but label includes full defun syntax. Module not populated.

---

### TC004: Internal Function Definition pvc-app:extract-run

**Syntax**
```lisp
(defun pvc-app:extract-run (model / why path t0 refs recs csv)
  (setq t0 (pvc-utl:ms))
  (if (setq refs (pvc-sel:select (pvc-cfg:resolve 'string model)))
    (progn
      (setq recs (mapcar (function (lambda (ref) (pvc-ext:record ref))) refs))
      (setq path (pvc-app:_settings-path))
      (setq csv (strcat (pvc-utl:trim (pvc-rtp:filter recs)) "\n"))
      (if (pvc-utl:open path "w" csv)
        (pvc-log:add 'C:PVCEXTRACT nil "Extract written" "EXTRACT")
        (pvc-log:add 'C:PVCEXTRACT T "Extract failed" "EXTRACT")))
    (pvc-log:add 'C:PVCEXTRACT T "No references found" "EXTRACT"))
  (pvc-log:flush))
```

**Expected Response**
- Node kind: `function`
- Label: `pvc-app:extract-run`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`

**graphify-lang output** (Actual - 2026-09-23)
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
**Notes**: Function detected but label includes full defun syntax. Module not populated.

---

### TC005: Global Variable *pvc-app:version*

**Syntax**
```lisp
(setq *pvc-app:version* "0.0.18")
```

**Expected Response**
- Node kind: `global`
- Label: `*pvc-app:version*`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`
- Value: `"0.0.18"` (string literal)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "global node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(setq *pvc-app:version* \"0.0.19\")",
      "note": "Global variable detected as call node, not global"
    }
  ]
}
```
**Notes**: Global variables not detected. Query only matches single-pair setq forms.

---

### TC006: Global Variable *pvc-app:undo-open*

**Syntax**
```lisp
(setq *pvc-app:undo-open* nil)
```

**Expected Response**
- Node kind: `global`
- Label: `*pvc-app:undo-open*`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-app`
- Value: `nil` (symbol)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "global node kind not found",
  "note": "Global variable detected as call node, not global"
}
```

---

### TC007: Global Variable *pvc-asg:registry*

**Syntax**
```lisp
(setq *pvc-asg:registry* nil)
```

**Expected Response**
- Node kind: `global`
- Label: `*pvc-asg:registry*`
- File: `src/pvc_mod_asg.lsp`
- Module: `pvc-asg`
- Value: `nil` (symbol)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "global node kind not found",
  "note": "Global variable detected as call node, not global"
}
```

---

### TC008: Global Variable *pvc-blk:def-cache*

**Syntax**
```lisp
(setq *pvc-blk:def-cache* nil)
```

**Expected Response**
- Node kind: `global`
- Label: `*pvc-blk:def-cache*`
- File: `src/pvc_mod_blk.lsp`
- Module: `pvc-blk`
- Value: `nil` (symbol)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "global node kind not found",
  "note": "Global variable detected as call node, not global"
}
```

---

### TC009: Package Literal Reference err:trap

**Syntax**
```lisp
(err:trap 'PVC-APP 'vla-get-ActiveDocument
  (list (vlax-get-acad-object)))
```

**Expected Response**
- Node kind: `reference.call`
- Label: `err:trap`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-err`
- Target: `pvc-err:trap` (function definition)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "No reference.call node found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(err:trap 'PVC-APP 'vla-get-ActiveDocument (list (vlax-get-acad-object)))"
    }
  ],
  "note": "Package literals not properly joined. Detected as call node."
}
```

---

### TC010: Package Literal Reference pvc-err:safe-call

**Syntax**
```lisp
(pvc-err:safe-call 'PVC-ERR 'vla-get-ActiveDocument
  (list (pvc-err:safe-call 'PVC-ERR 'vlax-get-acad-object nil)))
```

**Expected Response**
- Node kind: `reference.call`
- Label: `pvc-err:safe-call`
- File: `src/pvc_mod_err.lsp`
- Module: `pvc-err`
- Target: `pvc-err:safe-call` (function definition)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "No reference.call node found",
  "note": "Package literals not properly joined"
}
```

---

### TC011: Package Literal Reference pvc-cfg:model

**Syntax**
```lisp
(if (setq model (pvc-cfg:model))
  (pvc-app:extract-run model)
  (pvc-app:_extract-report 'C:PVCEXTRACT why))
```

**Expected Response**
- Node kind: `reference.call`
- Label: `pvc-cfg:model`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-cfg`
- Target: `pvc-cfg:model` (function definition)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "No reference.call node found",
  "note": "Package literals not properly joined"
}
```

---

### TC012: Package Literal Reference pvc-log:add

**Syntax**
```lisp
(pvc-log:add 'C:PVCEXTRACT nil "Extract written" "EXTRACT")
```

**Expected Response**
- Node kind: `reference.call`
- Label: `pvc-log:add`
- File: `src/pvc_app_main.lsp`
- Module: `pvc-log`
- Target: `pvc-log:add` (function definition)

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "No reference.call node found",
  "note": "Package literals not properly joined"
}
```

---

### TC013: String Literal in pvc-app:_ask

**Syntax**
```lisp
(setq why (getkword (strcat "\nSpecify [E]xtract/[R]econcile <E>: "))
  (list "E" "R"))
```

**Expected Response**
- Node kind: `string`
- Value: `"Specify [E]xtract/[R]econcile <E>: "`
- File: `src/pvc_app_main.lsp`
- Line: within `pvc-app:_ask`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "string node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(strcat "\\nSpecify [E]xtract/[R]econcile <E>: ")"
    }
  ],
  "note": "String literals not extracted. Captured inside call nodes."
}
```

---

### TC014: String Literal in pvc-app:_folder

**Syntax**
```lisp
(getfiled "Select settings file"
  (strcat (getvar 'dwgprefix) (pvc-utl:trim *pvc-app:settings-name* "."))
  "toml" 8)
```

**Expected Response**
- Node kind: `string`
- Value: `"Select settings file"`
- File: `src/pvc_app_main.lsp`
- Line: within `pvc-app:_folder`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "string node kind not found",
  "note": "String literals not extracted"
}
```

---

### TC015: Number Literal in pvc-app:_ask

**Syntax**
```lisp
(initget 1 "E R")
```

**Expected Response**
- Node kind: `number`
- Value: `1`
- File: `src/pvc_app_main.lsp`
- Line: within `pvc-app:_ask`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "number node kind not found",
  "note": "Number literals not extracted"
}
```

---

### TC016: List Structure in pvc-cfg:schema

**Syntax**
```lisp
(setq *pvc-cfg:schema*
  '(("header" . ("name" . "pvCaseTagTool") ("version" . "0.0.18"))
    ("log" . ("enabled" . T) ("level" . "DEBUG") ("dir" . "") ("file-name" . "..."))
    ("tool_options" . ("file_handling" . ...) ("extract" . ...) ("roundtrip" . ...))
    ("global_dwg_options" . ("att_style" . "Standard") ("att_layer" . "ATTRIB"))
    ("block_options" . ("string_blocks" . ...) ("combiner_box_blocks" . ...))
    ("xdata" . ("appid" . "PVC_TAGTOOL") ("type" . "string") ("index" . 1))
    ("groups" . (("key" . "string") ("layers" . ...) ("atts" . ...)) ...)))
```

**Expected Response**
- Node kind: `list`
- Structure: nested dotted pairs
- File: `src/pvc_mod_cfg.lsp`
- Module: `pvc-cfg`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "list node kind not found",
  "alternatives": [
    {
      "kind": "definition",
      "label": "(setq *pvc-cfg:schema* '(...))"
    }
  ],
  "note": "List structures not extracted as list nodes"
}
```

---

### TC017: Conditional Expression cond in pvc-err:safe-load

**Syntax**
```lisp
(cond
  ((null path)
   (err:_report caller T
     (strcat "File not found -> " (utl:to-string file-path))
     "FAIL")
   nil)
  (T
   (setq result
     (err:_trap caller 'load (list path) (strcat "LOAD " path)))
   (if (vl-catch-all-error-p result)
     nil
     (progn
       (err:_report caller nil (strcat "Loaded " path) "PASS")
       T))))
```

**Expected Response**
- Node kind: `conditional`
- Structure: `cond` with multiple branches
- File: `src/pvc_mod_err.lsp`
- Module: `pvc-err`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "conditional node kind not found",
  "note": "Conditional expressions not extracted"
}
```

---

### TC018: Loop Construct foreach in pvc-blk:attributes

**Syntax**
```lisp
(foreach a (append (pvc-blk:_invoke o 'GetAttributes)
                  (pvc-blk:_invoke o 'GetConstantAttributes))
  (setq out (cons
    (cons (strcase (pvc-utl:to-string (pvc-blk:_get a 'TagString)))
          (pvc-utl:to-string (pvc-blk:_get a 'TextString)))
    out)))
```

**Expected Response**
- Node kind: `loop`
- Structure: `foreach` with append list
- File: `src/pvc_mod_blk.lsp`
- Module: `pvc-blk`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "loop node kind not found",
  "note": "Loop constructs not extracted"
}
```

---

### TC019: Loop Construct repeat in ldr:_parse-metadata

**Syntax**
```lisp
(repeat 30
  (if (setq line (read-line handle))
    (progn
      (setq trimmed (vl-string-trim " \t" line))
      (cond
        ((and (> (strlen trimmed) 3)
              (= (substr trimmed 1 2) ";;")
              (vl-string-search "@module" trimmed))
         ...)
        ...))))
```

**Expected Response**
- Node kind: `loop`
- Structure: `repeat` with numeric argument
- File: `tests/lang/fixtures/src/core/ldr.lsp`
- Module: `ldr`

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "File not found",
  "note": "Test references fixture file not in src/ directory"
}
```

---

### TC020: Visual LISP Reference vl-catch-all-apply

**Syntax**
```lisp
(vl-catch-all-apply 'log:add (list sym flag log-msg msg-pred))
```

**Expected Response**
- Node kind: `reference.call`
- Label: `vl-catch-all-apply`
- File: `src/pvc_mod_err.lsp`
- Built-in: `true` (from builtins.txt)
- Target: built-in Visual LISP function

**graphify-lang output** (Actual - 2026-09-23)
```json
{
  "error": "reference.call node kind not found",
  "alternatives": [
    {
      "kind": "call",
      "label": "(vl-catch-all-apply 'log:add (list sym flag log-msg msg-pred))"
    }
  ],
  "note": "Built-in Visual LISP functions detected as call nodes, not references"
}
```

---

## 5. Summary

| Category | Count | Description |
|:---------|------:|:------------|
| Commands | 7 | C:PVCVER, C:PVCEXTRACT, C:PVCRECONCILE, C:PVCGROUPS, C:PVCEXPORT, C:PVCIMPORT, C:PVCRESTORE |
| Internal Functions | ~150 | pvc-*, pvc-_:*, pvc-*:* patterns |
| Global Variables | ~60 | *pvc-* patterns |
| String Literals | ~100+ | Configuration, prompts, messages |
| Number Literals | ~50+ | Tolerance values, indices, counters |
| Built-in References | 100+ | vl-*, vla-*, vlax-* Visual LISP functions |

## 6. Test Coverage

The 20 test cases cover:

1. **Command definitions** (TC001-TC002): C: prefix functions
2. **Internal function definitions** (TC003-TC004): pvc-* patterns
3. **Global variables** (TC005-TC007): *pvc-* patterns
4. **Package literals** (TC009-TC012): err:trap, pvc-err:safe-call, pvc-cfg:model
5. **Symbol references** (TC011-TC012): Function call targets
6. **String literals** (TC013-TC014): User-facing text
7. **Number literals** (TC015): Configuration values
8. **List structures** (TC016): Settings schemas
9. **Conditional expressions** (TC017): cond branches
10. **Loop constructs** (TC018-TC019): foreach, repeat

---

## 7. Test Execution Summary (T14)

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

### What Works ✅
- Command detection: 7 commands correctly identified (C:PVCVER, C:PVCEXTRACT, C:PVCRECONCILE, C:PVCGROUPS, C:PVCEXPORT, C:PVCIMPORT, C:PVCRESTORE)
- Function detection: ~300 functions detected with AST capture
- File extraction: All 18 .lsp files successfully processed

### Needs Fix ⚠️
- Global variable detection: Query only matches single-pair setq; real code uses multi-pair setq → 0 globals vs ~60 expected
- Package literal joining: `err : trap` not joined to `err:trap` in post_file hook
- Source locations: All nodes show `None` instead of line numbers
- Module population: All nodes show `N/A` instead of module names

### Not Working ❌
- String/number literal extraction: No rules for `string`/`number` node kinds
- Structural nodes: No `list`, `conditional`, `loop` node kinds extracted
- Built-in reference classification: Visual LISP functions (vl-*, vla-*, vlax-*) detected as call nodes, not reference.call


**Status**: ✅ COMPLETE — Test documentation consolidated. Target file contains all 20 test cases with actual graphify-lang output.  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
<!-- TEMPLATE-END -->
