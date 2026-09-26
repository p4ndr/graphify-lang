# Plan 05 S006: tests, docs and release

Stage 6 of plan 05: the test suite shows what CI really covers, the docs describe the fork as it is, the upstream PR drafts exist, and `v0.9.67+lang.4` is installed and graphed.

- Status: ACTIVE
- Task: T37
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s6` from `rr-s5`; the release is a fast-forward of `autolisp`
- Findings: M12, M11, N1, N2, E3 (PR draft), and the PR drafts for M3 and L13

## 1. Design

- **M12.** The failure-class tests were added in stages 1 to 5. Here: register a `corpus` pytest marker in `pyproject.toml`, and mark the corpus tests (`test_vba.py:166-169`, `test_bmake.py:157-160`, `test_ecschema.py:31,184-185`, `test_astgrep.py:26,139`, `test_lang_sniff.py:165-168`) with it, so a skip reads "corpus" in CI. Add a small checked-in corpus sample for each plugin under `tests/lang/fixtures/`, so CI covers more than the minimal fixtures. Each sample must be small, and redistributable or synthetic.
- **M11, `README.md`.**
  - Replace '## Status' with the current state: the released version, the 9 languages, and `graphify lang list`.
  - Rewrite 'Development setup' to the repo `.venv` + `uv sync`. Delete the `graphifyy 0.9.55` / `~/.venvs/graphify-lang` / "uv is not installed" text.
  - Mark each roadmap phase done or open. Phase 6 = T10, open.
  - Replace line citations (`cli.py:881`) with symbol names.
  - Delete "Planned directories are marked".
  - Add the plugin rules from the review's architectural findings: a resolver reads ids through the node index; an extractor or augment is a pure function of the file bytes; name the upstream seams the fork depends on.
- **N1.** `.claude/CLAUDE.md`: cite `_DISPATCH`, `CODE_EXTENSIONS` and `_HOOK_SOURCE_EXTS` by symbol and file, not by line number.
- **N2.** Set plan 02 to DONE. Plan 01 stays ACTIVE for T10 only; write that in its status line. Run the `manifest` verb.
- **PR drafts (hub D2), under plan 01 T10.** Write `docs/upstream/pr-*.md`, one per seam:
  - `watch.py` context-node fields (H1/E3);
  - `watch.py` claimed-path trigger (M3);
  - `resolver_registry.py` case-fold (L13, T10.4);
  - the registry lookups in `detect.py` / `extract.py`.

  Each draft holds the problem, the minimal upstream diff, and a test. Nothing is opened on GitHub without owner approval.
- **Release.** Bump to `0.9.67+lang.4`. Fast-forward `autolisp` to `rr-s6`, then tag. `rm -rf build dist`; build the wheel; copy it to `~/.local/share/graphify-lang/wheels/`; install it with the README form, `pipx install --force "graphifyy[mcp,commonlisp] @ file://…"` (the plan 04 T31 lesson: the bare wheel path drops the `mcp` extra). Refresh the graphify skill copy (plan 03 S6). Do not run `graphify claude install`.
- **Rebuild.** For the same 11 repos plus `~/.claude` as plan 04 S16: back up to `graph.pre-plan05.json`, delete `graphify-out/cache/ast/`, run `graphify update <path>`. E1 changes the cache namespace, so old AST entries are not reused anyway.

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S6.0 | Hub D5: `git fetch upstream`; rebase the `rr-s1`..`rr-s6` chain onto `upstream/v8` (rebase, never merge; resolve conflicts only in fork-owned code and registry-lookup lines). | Full pytest exits 0 with no upstream test file edited; `git diff upstream/v8...HEAD -- graphify/extractors/` is empty. |
| S6.1 | M12 marker and corpus samples. | `pytest -m "not corpus" tests/ -q` exits 0, and the skip reasons read "corpus". |
| S6.2 | M11, N1, N2 docs. | `git grep -n "No code yet\|0.9.55\|~/.venvs/graphify-lang\|extract.py:5630"` finds nothing in the fork's docs. |
| S6.3 | PR drafts. | Each draft's test passes when its diff is applied to a scratch `upstream/v8` worktree. |
| S6.4 | Release `v0.9.67+lang.4` and install. | `graphify --version` = `0.9.67+lang.4`; `graphify lang list --check` shows 9 `ok`; the MCP server starts; `import yaml` works in the pipx venv. |
| S6.5 | Rebuild the 12 graphs; do a second, no-change update; run the E5 parity test's incremental check on scratch copies of bim-chk and BentleyHelp. | Every repo exits 0. Plugin edge counts match `case_007`, or `case_008` records the cause. Cross-file edges survive the incremental update (this closes H1 on real corpora). |
| S6.6 | Close out: every finding is in `cc-CR000.002.md`, and `cc-CR000.001.md` holds no open finding; plan 05 and all spokes set to DONE; learnings (ltm) for the purity contract, the index-ref contract and the context-field hook; ask the owner, then push `autolisp`, the `rr-*` branches and the tag to `origin`. | Hub §6 acceptance criteria are met. |

## 3. Result

Owner decision (2026-09-26): S6.4 (release), S6.5 (graph rebuild) and S6.6 (close-out) are deferred until after a review-fix pass. This run does S6.0 to S6.3; no version bump, tag, build, install or graph rebuild.

| Step | Result | Commits |
|:-----|:-------|:--------|
| S6.0 | `rr-s6` = `rr-s5` + the learnings sidecar, rebased onto `upstream/v8` `4000de15466588ec3ee32f9e10a587ca97d3b8a5` (release 0.9.68; old base `4c73561`, 0.9.67; 25 upstream commits). 104 commits replayed, one conflicting: `7b6eaf3` (the lang.1 commit) in `README.md` (kept the fork README), `pyproject.toml` and `uv.lock` (version line only; kept `0.9.67+lang.1`). No conflict in any code file. `docs/UPSTREAM-README.md` synced to the upstream README. `pytest tests/ -q`: 6233 passed, 14 skipped (6209 + 24 new upstream tests). `git diff upstream/v8...HEAD -- graphify/extractors/` empty; no upstream test file modified; `tests/lang_baseline.txt`, `tests/upstream_tables.json` unchanged. `rr-s1`..`rr-s5` keep the old base. | `9351e4c`, `5a53250` |

Deviations from §1:

- **S6.0 chain.** Only `rr-s6` is rebased; `rr-s1`..`rr-s5` stay as historical refs (owner, this run).
- **Version.** The branch still says `0.9.67+lang.3` on an upstream 0.9.68 base. The release step (S6.4) must choose between `0.9.67+lang.4` (spoke) and `0.9.68+lang.4` (the real base).
- **Upstream `8928031`** ("preserve cross-file edges during incremental updates") feeds context nodes into JS/Python symbol resolution in `resolution.py`; it does not touch `watch.py` or the fork's `context_fields` hooks, and the E5 parity tests still pass.
