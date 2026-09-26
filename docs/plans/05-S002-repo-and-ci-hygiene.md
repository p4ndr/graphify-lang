# Plan 05 S002: repo and CI hygiene

Stage 2 of plan 05: the workflows parse, CI runs on the fork's release branches and tags, and the repo holds no junk.

- Status: ACTIVE
- Task: T33
- Hub: `05-review-remediation-cc-cr000-001.md`
- Branch: `rr-s2` from `rr-s1`
- Findings: M7, M8, E9, M9, M10, N6

## 1. Design

| Finding | Fix |
|:--------|:----|
| M7 | `git checkout upstream/v8 -- .github/workflows/publish.yml .github/workflows/release-graph.yml`, then add back only the one-line `if: github.repository == 'Graphify-Labs/graphify'` guard in each. |
| M8, E9 | `.github/workflows/graphify-lang-ci.yml`: trigger on `autolisp`, `lang-*`, `rr-*`, `v8` and `v*` tags. Change the security job to `bandit -r graphify graphify_lang`. |
| M9 | Hub D3: `git rm -r .sidecar-cache/ src_core_test.lsp test_dcl.toml test_pattern.toml docs/testing/archive/ .claude/docs/cc-T10-COMPLETE.md`; add `.sidecar-cache/` to `.gitignore`. `git-sp.ps1` stays. First search the docs for references to `docs/testing/archive/` and `cc-T10-COMPLETE.md`, and repoint each one to the kept summary (`docs/testing/case_*`) or to git history. |
| M10, N6 | `git rm scripts/install-mcp.sh`. Fix the T9.5 line in `docs/30-TODO.md` and `docs/35-DONE.md`: remove "(TODO: run manually)" and cite M10. |

## 2. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S2.1 | M7 restore and guards. | `python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]"` on every file in `.github/workflows/` exits 0; `git diff upstream/v8 -- .github/workflows/publish.yml` shows only the guard line. |
| S2.2 | M8 and E9 trigger and bandit change. | `actionlint` if installed, else the YAML parse above. Bandit over `graphify_lang` runs with no High finding, or each High finding is listed in this spoke with a fix. |
| S2.3 | M9 deletions and reference repoint. | `git grep -n "sidecar-cache\|testing/archive\|cc-T10-COMPLETE\|install-mcp"` finds nothing outside git history notes. |
| S2.4 | M10 and N6. | The T9.5 text has no open TODO. |
| S2.5 | Ask the owner, then push `rr-s2` to `origin` and read the CI result. | The fork CI run on `rr-s2` is green. |
| S2.6 | Stage close (hub §3); move the findings to `cc-CR000.002.md`. | Hub §3 checks pass. |
