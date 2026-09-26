# Plan 05 S005: registry robustness

Stage 5 of plan 05: one bad plugin cannot take down the others, plugin files trigger every rebuild path, and the registry has one clear loading path.

- Status: DONE (2026-09-26, `rr-s5` `ef2012a`..HEAD)
- Task: T36
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s5` from `rr-s4`
- Findings: M1, E4, M5, M3, L6, L7, L8, L10, L13, N5

## 1. Design

- **M1.** In `graphify_lang/registry.py`, the call `result = result()` and `_process_loader_result` run inside the per-entry-point `try`. A failure logs `failed to load entry point <name>: <error>`, and the other plugins still register.
- **E4.** `graphify lang list --check` loads every entry point and every `GRAPHIFY_LANG_PATH` folder, and prints one row per plugin: `ok`, or the load error. It exits 1 when any plugin fails. The `cli.py` change is inside the existing `lang` branch, which is fork code.
- **M5 (hub D4): implement `GRAPHIFY_LANG_PATH`.**
  - For each folder in the variable (`os.pathsep`-separated), load each `*.toml` manifest with `LanguageManifest.from_toml`.
  - `[extract] runtime = "<module>"` is imported with that folder first on `sys.path`, for that import only. The module must expose the same `extract` or `augment` callable that entry-point plugins expose.
  - Order: entry points first, then path folders. A later claimant of an owned suffix follows the existing rules (router, `overrides`, the warning).
  - A folder that does not exist, or a manifest that fails, logs one warning and is skipped (M1 rule).
  - Also: delete the unread `_RegistryState.enabled` (the disable check stays in `_init_state`); fix the docstring at `registry.py:1`; make `docs/55-SETTLED.md:125` and `docs/35-DONE.md:289` true, with a test that loads a plugin from a tmp folder.
- **M3 (hub D2).** `graphify watch` ignores `.xml`, and it treats `.yml`, `Cargo.toml` and `.md` edits as docs.
  - Fork fix: a try-wrapped registry lookup in `watch.py` at the `_WATCHED_EXTENSIONS` filter (`watch.py:282`) and in `_batch_triggers_rebuild` (`watch.py:2306`). A path counts as code when `lang_registry.claims_file(path)` is true, or when an augment claims it.
  - Upstream PR draft in S006.
- **L6.** Delete the `upper()` suffix variants in `graphify/lang_registry.py:36-42,94`, and fix the "casefolded" comment.
- **L7.** One entry-point group, `graphify_lang_plugins`, which is the one `pyproject.toml` ships. One loop. Delete the Python 3.9 `entry_points().get` fallback and the `importlib_metadata` import.
- **L8.** Each `except Exception: pass` at the core hook sites (`detect.py:49-50,535-536`, `extract.py:6719-6720,6758-6759,6883-6884,6920-6921`, `cli.py:82-83`) logs at debug level to `graphify.lang_registry`. Each hook still changes only one line of upstream code.
- **L10.** `dispatch_table` leaves out the suffixes that only `[match]` plugins claim (`.yml`, `.yaml`, `.xml`, `.toml`). They reach extraction through `claims_file` alone. Check first that `_get_extractor` still finds the plugin for a claimed file; if it does not, keep the router and close L10 as accepted, with the measured cost.
- **L13 (hub D2).** Keep the fork's case-fold in `graphify/resolver_registry.py:78-80`, and add a test that pins the reason (a `.LSP` file activates the AutoLISP resolver). Upstream PR draft in S006, marked T10.4. Remove the fork edit once upstream merges it.
- **N5.** `[match] filenames` compare with `casefold()` (`registry.py:240`).

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S5.1 | Tests first: `test_m1_bad_entry_point_isolated`, `test_e4_lang_list_check`, `test_m5_lang_path_loads_plugin`, `test_m5_missing_dir_warns`, `test_m3_watch_triggers_on_claimed_xml_yml_toml_md`, `test_l6_no_upper_variants`, `test_l7_single_group`, `test_l8_hook_error_logged`, `test_l10_claimed_yml_still_extracted`, `test_l13_upper_suffix_activates_resolver`, `test_n5_cargo_toml_casefold`. | Each fails for the reason the review names (L13 passes today: it pins behaviour). |
| S5.2 | M1, L7, M5, E4 (engine commits, then the `cli.py` `lang` branch). | Their tests pass; `graphify lang list --check` prints 9 `ok` rows. |
| S5.3 | M3 watch hooks (core registry-lookup commit). | `test_m3_*` passes; upstream `tests/test_watch.py` passes unchanged. |
| S5.4 | L6, L8, L10, N5. | Their tests pass; `tests/upstream_tables.json` changes only by the removed upper-case variants (L6), with the cause written here. |
| S5.5 | Stage close (hub §3); move the findings to `cc-CR000.002.md`. | Hub §3 checks pass. |

## 3. Result

| Step | Result | Commits |
|:-----|:-------|:--------|
| S5.1 | 14 tests in `tests/lang/test_s5_registry_robustness.py`: 12 red, strict xfail with `raises=` pinned (M1 `ValueError` escapes `registered_names()`; the others `AssertionError`: L7 two groups scanned, M5 x4 nothing loaded or logged, E4 no `--check`, M3 x2 `.xml` / `.yml` / `Cargo.toml` / cc-kb `.md` do not rebuild, L6 upper variants, L8 no log record, N5 `cargo.toml` not claimed). L10 and L13 pass: they pin behaviour. | `ef2012a` |
| S5.2 | M1, L7, M5 (engine): per-plugin `try`, `load_errors()`, one group, `GRAPHIFY_LANG_PATH` folders loaded after the entry points, loaded folders in the E1 fingerprint (a toml or code edit in a path plugin moves the namespace: 3 distinct values in the test). E4: `check_languages` (engine), then the `cli.py` `lang` branch. `graphify lang list --check`: 9 `ok` rows, exit 0. | `4071b40`, `a05bc8b`, `cb21e7e` |
| S5.3 | M3: engine `watch_claims`, then one try-wrapped lookup (`_lang_claims`) at three `watch.py` sites (the filter, `_batch_triggers_rebuild`, `_has_non_code`). Upstream `tests/test_watch.py` unchanged, 181 passed. | `32d4618`, `227c194` |
| S5.4 | L6 upper variants dropped; L8 nine hook sites log at debug level; N5 case-folded `[match] filenames`; L10 closed as accepted (measured below); L13 pinned. `tests/upstream_tables.json` unchanged (cause below). Also a fork test fix: `test_graphify_lang_disable` now resets the registry it emptied. | `7d9fbf8`, `34510f8`, `b80a115`, `728c6a3` |
| S5.5 | `pytest tests/ -q`: 6209 passed, 14 skipped (baseline 6195 / 14; +14 in `test_s5_registry_robustness.py`). `git diff upstream/v8...HEAD -- graphify/extractors/` empty; `tests/lang_baseline.txt`, `tests/upstream_tables.json`, `tests/test_watch.py` unchanged. M1, M3, M5, L6, L7, L8, L10, L13, N5, E4 moved to `cc-CR000.002.md`. | this commit |

Deviations from §1:

- **L6 and `tests/upstream_tables.json`.** The file did not change at all: `test_sc2_no_plugin_tables_match_upstream_snapshot` takes the snapshot with `GRAPHIFY_LANG_DISABLE=1`, so the upper-case variants were never in it.
- **M3 augment claim.** cc-kb's `[match]` claims every `.md`, so "an augment claims it" means the augment adds something to the built-in's result for that file (`watch_claims` runs the wrapped and the plain extractor and compares). A plain `.md` still takes the doc path, so upstream `test_batch_modified_doc_only_does_not_rebuild` passes unchanged. Known limit: an edit that removes a doc's last cc mention does not rebuild until the next code event (the `needs_update` flag is still written). A deleted file counts by suffix (`[match]` or augment suffix), so the rebuild's reconcile drops it.
- **M3 third site.** `_has_non_code` also asks the registry (language claims only): an `.xml` or `.yml` a plugin claims no longer writes the `needs_update` flag with the "semantic re-extraction requires LLM" message.
- **M5 contract.** The runtime module exposes `extract` (or `augment` for an augment) and an optional `RESOLVER`, the names entry-point packages already use internally. A path manifest whose name is already registered is rejected (logged, skipped); a manifest registered directly (tests) keeps the old overwrite behaviour. `LanguageManifest` gained a `runtime` field (the `[extract] runtime` value). The unread `warned_builtins` went with `enabled`.
- **L8 scope.** The two S4 `context_fields` fallbacks in `cli.py` and `watch.py` log too (nine sites, not seven).
- **L10 measured.** No built-in claims `.yml`, `.yaml` or `.xml`, and `_get_extractor` finds extractors only in `_DISPATCH`, so dropping the routers would stop claimed files being extracted: kept. Cost on this repo: `collect_files` returns 27 `.yml` / `.xml` files, 16 unclaimed, 0.1 ms of router time in total (the glob fails before any read).
- **Order-dependent fork test.** Run before `tests/lang/test_astgrep.py`, `test_graphify_lang_disable` left an empty cached registry and 6 astgrep tests failed (reproduced at `ef2012a`, before any S5 fix); `728c6a3` adds the missing `registry.reset()`.
