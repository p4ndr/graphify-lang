# T14-RunTests - Final Output

## Test Execution Summary

**Test ID**: T14-RunTests  
**Date**: 2026-09-23  
**Status**: ✅ COMPLETE

## What Was Done

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (`~/repos/autolisp-pvcase/src/`) - 18 .lsp files with 20 test cases.

## Test Results

| Category | Count |
|:---------|------:|
| Passing | 2 (10%) |
| Partial | 6 (30%) |
| Failing | 12 (60%) |
| **Total** | **20** |

### Working Features ✅
- Command detection: 7 commands found
- Function detection: ~300 functions found
- File extraction: All 18 .lsp files processed

### Issues Found ⚠️
- Global variable detection: 0 detected (query issue)
- Package literal joining: Not working
- String/number literal extraction: Not implemented
- Source locations: All show "None"
- Module population: All show "N/A"

### Not Working ❌
- List/conditional/loop structural nodes: Not extracted
- Built-in reference classification: Not working

## Files Updated

The test file `docs/testing/case_001_autolisp-pvcase.md` has been updated with actual graphify-lang output for all 20 test cases.

Additional documentation created:
- `docs/testing/case_001_autolisp-pvcase_results.md`
- `docs/testing/case_001_autolisp-pvcase_test_results.md`
- `docs/testing/case_001_autolisp-pvcase_test_cases.md`
- `docs/testing/case_001_autolisp-pvcase_SUMMARY.md`
- `docs/testing/T14-COMPLETE.md`
- `docs/testing/T14-RESULTS.json`
- `docs/testing/T14-SESSION-LOG.md`
- `docs/testing/T14-FINAL-REPORT.md`
- `docs/testing/T14-FINAL-RESULTS.json`

## Key Findings

The graphify-lang AutoLISP extractor successfully detects commands and functions but has several issues:
1. Global variable query only matches single-pair setq, not multi-pair forms
2. Package literals not properly joined into single symbols
3. Source locations and module metadata not populated
4. String/number literals not extracted
5. Structural nodes (list, conditional, loop) not extracted

## Recommendation

Fix the identified issues to improve test coverage from 10% to full coverage.

---

**Test Status**: Documentation complete with actual results populated.  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
