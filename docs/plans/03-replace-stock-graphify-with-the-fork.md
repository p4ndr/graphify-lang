# Replace stock graphify with the fork

Replace the pipx `graphifyy 0.9.55` install with a pinned build of this fork, rebased on `upstream/v8`, and rebuild the graph of every graphed repo on this host.

- Status: DONE
- Created: 2026-09-25
- Tasks: <TASK numbers in docs/30-TODO.md, when ACTIVE>

## 1. Goal

`graphify` on `PATH`, the Claude Code `graphify` MCP server (`~/.claude.json:2498`) and the OMP `graphify` MCP server (`~/.omp/agent/mcp.json:28`) all run the fork. All 23 repos with a `graphify-out/` have a graph that the fork built.

## 2. Scope

Decisions (owner, 2026-09-25):

| # | Decision |
|:--|:---------|
| D1 | Rebase the fork on `upstream/v8` (`0.9.67`, 246 commits ahead of the fork base) before the swap. |
| D2 | Install pinned from a tag, not editable. Same pipx venv name `graphifyy`, so no MCP config changes. |
| D3 | Rebuild all 23 graphed repos, with a forced AST re-extract. |

In scope: this host (Linux, aarch64) only.

Out of scope: the Windows host (it has no graphify install); an upstream PR (plan 01 T10); any change to `upstream`.

Graphed repos (2026-09-25): `~/.claude` and, under `~/repos/`: autolisp-pvcase, autolithp, autolithp02, BentleyHelp, bentley-model-management, bentley-pyplace, BentleyTools, bim-chk, brcm-pEquip, caffiene-ext, claude-config, comment-sidecar, COMOS_CODE, COMOS_DOCS, g-eng, graphify-lang, llm-linter-tool, moxide, oag-dev, oa-graph, tmllm, vscode. No repo has a graphify git hook installed.

## 3. Design

- **Upstream stays read-only.** You have no write access to `Graphify-Labs/graphify`. S1 also sets the `upstream` push URL to `DISABLE`, so a push to it fails locally, before any network call.
- **One venv, same name.** `pipx install --force <wheel>` replaces the `graphifyy` venv in place. The Python path that the two MCP configs name stays valid. The fork keeps the package name `graphifyy` (`pyproject.toml:6`).
- **Pinned build.** Build a wheel from tag `v0.9.67+lang.1` and install that wheel. A later checkout or broken commit in the fork cannot change the installed tool.
- **Forced AST re-extract only.** Delete `graphify-out/cache/ast/` and keep the semantic (LLM) cache subdirectories (`graphify/cache.py:932`). Rebuild cost is then CPU only, with no LLM tokens.
- **Rollback.** `pipx install --force graphifyy==0.9.55` puts back the stock tool. Each repo's old `graph.json` is copied to `graphify-out/graph.pre-fork.json` before the rebuild.

## 4. Steps

| Step | Action | Check |
|:-----|:-------|:------|
| S1 | `git remote set-url --push upstream DISABLE`. Tag the current `autolisp` HEAD `pre-rebase-0.9.55` and push the tag to `origin`. | `git push upstream` fails with a local error. |
| S2 | Rebase `lang-registry` on `upstream/v8`, then `autolisp` on `lang-registry`. Resolve conflicts only in fork-owned code and the registry lookup lines (`.claude/CLAUDE.md` 'Tracking upstream'). | `pytest tests/ -q` exits 0, with no upstream test file edited. |
| S3 | Set `version = "0.9.67+lang.1"`. Rerun the case 003 corpus script on `~/repos/autolithp`, compare to `docs/testing/case_004_plan02-autolisp-fixes.md`. | Node and edge counts match case 004, or the difference has a written cause. |
| S4 | Commit, tag `v0.9.67+lang.1`, push the branches (`--force-with-lease`, because the rebase changes history) and the tag to `origin`. | `git ls-remote origin` shows the tag. |
| S5 | `python -m build --wheel` in the fork venv; `pipx install --force dist/graphifyy-0.9.67+lang.1-py3-none-any.whl`. | `graphify --version` gives `0.9.67+lang.1`; `graphify lang list` shows `autolisp`; both MCP servers start (`/mcp` in Claude Code, OMP tool list). |
| S6 | Refresh `~/.claude/skills/graphify/` (`SKILL.md`, `references/`, `.graphify_version`) by a copy from the installed package. Do NOT run `graphify claude install` from `$HOME`, because it rewrites the shared `settings.json`. | `.graphify_version` reads `0.9.67+lang.1`. |
| S7 | Pilot rebuild on 3 repos: `autolithp` (AutoLISP), `tmllm` (Python), `~/.claude` (docs, semantic cache). For each: back up `graph.json`, delete `cache/ast/`, run `graphify update <path>`. | Semantic nodes in `~/.claude` stay; AutoLISP defun nodes appear in `autolithp`; `mcp__graphify__graph_stats` works on each. |
| S8 | Same rebuild on the other 20 repos, one at a time, by a script that logs each result. | Every repo exits 0; a failed repo stops the script. |
| S9 | Update docs: `$CLAUDE_HOME/CLAUDE.md` graphify paragraph (remove 'Known limit: `.lsp` files yield file nodes only'; say the tool is the fork), `CROSS-HOST.md` if it names the pipx package, fork `README.md` 'Development setup' and `.claude/CLAUDE.md` 'Verification' (install is no longer stock `0.9.55`). Add a learning. | `grep -rn "0.9.55" ~/.claude/CLAUDE.md` gives nothing. |
| S10 | After one week with no fault: delete the `graph.pre-fork.json` backups. | Owner approves. |

Update procedure for later fork releases: S2 to S5, then `graphify update` per repo (no forced rebuild unless the extractor output changed).

## 5. Acceptance criteria

- `graphify --version` and both MCP servers report `0.9.67+lang.1`.
- `pytest tests/ -q` exits 0 on the tagged commit.
- All 23 repos have a `graph.json` built by the fork; `autolithp` graph has defun nodes.
- `git push upstream` fails locally.
- Rollback command is written in this plan and was not needed, or was used and worked.

## 6. Risks and open questions

| # | Risk | Action |
|:--|:-----|:-------|
| R1 | Rebase conflicts in `graphify/extract.py`, `detect.py`, `cli.py` (246 upstream commits touch the same tables). | Stop at the first conflict you cannot solve in fork-owned lines; ask the owner. |
| R2 | Upstream changed extraction between 0.9.55 and 0.9.67, so non-AutoLISP graphs change too. | Expected; this is why D3 rebuilds all repos. S7 pilot shows the size of the change. |
| R3 | `graphify update` after deleting `cache/ast/` may not keep semantic nodes for repos first built with the `/graphify` skill. | S7 pilot on `~/.claude` checks this before S8. If nodes drop, stop and re-plan S8. |
| R4 | Plan 01 tasks T5-T8 are still `[~]`. The swap ships that state to every repo. | Owner confirms the current AutoLISP output is good enough (case 004), or finishes T5-T8 first. |
| R5 | A running Claude Code or OMP session keeps the old MCP server process. | Restart open sessions after S5. |
| R6 | The SessionStart hook `ensure-graphify-graph.ps1` can start a background build during S8. | Run S8 with no other session open. |
