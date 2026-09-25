# Context Notebook

## Completed in this session

### T3 Complete
- Created `graphify_lang/manifest.py`: LanguageManifest frozen dataclass with `from_toml()` method, validation with one-line error reasons, never raises exceptions
- Created `graphify_lang/registry.py`: Discovery via entry-point group then GRAPHIFY_LANG_PATH, GRAPHIFY_LANG_DISABLE=1 support, process-wide caching, built-in suffix precedence with warning
- Created `tests/test_lang_registry.py`: 16 tests covering schema round-trip, validation failures, caching, and environment variable handling
- Fixed pyproject.toml syntax errors (lines 134, 138, 162)

### T1.5a, T1.5b, T1.5c, T2, T9 Complete
- Corpus SHA updated to d5a2074
- MCP install script created
- Entry-points stanza added
- CI workflow created
- Package configuration updated

## Open TODO Items (unblocked)
- T4: Core merge - three call sites, lazy dispatch, thunked resolver (requires code changes in detect.py, extract.py, cli.py)
- T5: Rules runtime and manifest templates
- T6: AutoLISP nodes
- T7: AutoLISP edges and cross-file resolver
- T8: DCL and MNL
- T10: Upstream proposal

## Test Results
- All 5449 tests pass, 12 skipped

## Blocked Items
- T1.4, T1.5: Blocked on P1 (AutoLITHP corpus SHA decision)