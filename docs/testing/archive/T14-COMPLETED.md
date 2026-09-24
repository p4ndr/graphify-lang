# T14-RunTests - Task Complete

## Summary

Tested graphify-lang AutoLISP extractor against `autolisp-pvcase` codebase (18 .lsp files, 20 test cases).

**Results**: 2/20 Passing (10%)

### Working ✅
- Command detection: 7 commands
- Function detection: ~300 functions
- File extraction: All files

### Needs Fix ⚠️
- Global variable detection: Query issue (single-pair vs multi-pair setq)
- Package literal joining: Not working
- Source locations: All None
- Module population: All N/A

### Not Working ❌
- String/number literal extraction
- Structural nodes (list/conditional/loop)
- Built-in reference classification

## Files Updated

- `docs/testing/case_001_autolisp-pvcase.md` - Updated with actual results
- `docs/testing/T14-RESULTS.md` - Test results report
- `docs/testing/T14-REPORT.md` - Completion report
- `docs/testing/T14-FINAL.json` - Final JSON

## Next Steps

Fix identified issues to improve test coverage.

---

**Status**: ✅ COMPLETE  
**Test ID**: T14-RunTests  
**Date**: 2026-09-23
