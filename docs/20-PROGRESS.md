<!-- TEMPLATE-VERSION: 2026-09-20-006 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# 20-PROGRESS.md:

This document is a LIVE running changelog for all work in the repo.

- `§3` is the current session, `§4` the last one, `§5` the rest of the last 7 days; older sessions are in `25-HISTORY.md`.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`progress_add`; `todo_set` and `pending_settle` add their own lines); hand edits by the owner are fine.
- IF the owner says "prepare for exit" or similar: `progress_add` the session's outcome, and record any valid learnings/gotchas in the knowledge layer.
<!-- TEMPLATE-END -->

## 3. CURRENT SESSION

### 2026-09-26 19:48 (UTC+10)

- T37.4 done: ddefbc7 release 0.9.68+lang.4 on rr-fix; tag v0.9.68+lang.4 pushed to origin, CI green (tag + rr-fix); pipx venv on the lang.4 wheel ([mcp,commonlisp]); lang list --check 9 ok; MCP initialize 0.9.68+lang.4; yaml 6.0.3; skill refreshed; .venv lang.4. Release cut from rr-fix; autolisp untouched.
- T37.5 done: 12 graphs rebuilt (graph.pre-plan05.json, cache/ast cleared, graphify update), exit 0 each, 2nd update identical; diffs vs plan 04 S16 explained in case_008 §5 (VBA self-loops, M4 PyGeomTest split, ~/.claude tree changes). Incremental: bim-chk equal; BentleyHelp loses 1 bmake edge (duplicate-basename label residual, new TODO).
- T37.6 done: Plan 05 hub and six spokes DONE; manifest run; learnings 1477 (index-ref), 1491 (context-field hook), 1498 (purity) already recorded; new 1501 (disambiguated file labels on incremental context nodes); residual tracked as T38.
- T37 done (all steps): P05-S006 (rr-s6) Tests, docs, release lang.4 — M12 M11 N1 N2 PR drafts
- Plan 05 DONE (S6.4-S6.6): v0.9.68+lang.4 released from rr-fix ddefbc7 (tag on origin, CI green), installed in the pipx venv; 12 graphs rebuilt (case_008 §5); autolisp untouched pending owner decision.
- Open: T38, the bmake/cc-kb duplicate-basename label residual on incremental builds (learning 1501). Rollback: per repo cp graphify-out/graph.pre-plan05.json graphify-out/graph.json; global pipx install --force the lang.3 wheel (README form).

### 2026-09-26 17:11 (UTC+10)

- T37.1 done: S6.0: rr-s6 rebased onto upstream/v8 4000de1 (0.9.68), 1 conflict (lang.1 commit: README/pyproject/uv.lock version); S6.1 M12 corpus marker + samples 842a67d; 6238 passed / 14 skipped
- T37.2 done: M11 README, N1, N2 in acdac5f; S6.2 git grep check clean on README.md and .claude/CLAUDE.md
- T37.3 done: 4 drafts in docs/upstream/ (31db078), each verified on an upstream/v8 scratch worktree; E3 closed
- Plan 05 S6.0-S6.3 on rr-s6 (T37.1-T37.3 done; T37.4-T37.6 deferred by owner until after a review-fix pass): rebased onto upstream/v8 4000de1 (0.9.68), one conflict in the lang.1 commit (README kept, version lines kept); M12 corpus marker + samples; M11 README, N1, N2; four upstream PR drafts in docs/upstream/, each verified on upstream/v8.
- pytest 6238 passed / 14 skipped; extractor three-dot diff empty; no upstream test edited; M11, M12, N1, N2, E3 moved to cc-CR000.002 (cc-CR000.001 has no open finding). rr-s6 pushed to origin, CI run 36225724044 green (3.10/3.12/3.13, security).

### 2026-09-26 16:27 (UTC+10)

- T36.1 done: 14 tests, 12 strict xfail red, L10/L13 pinned (ef2012a)
- T36.2 done: M1, L7, M5 (4071b40), E4 (a05bc8b, cb21e7e); lang list --check 9 ok rows
- T36.3 done: M3 watch hooks (32d4618, 227c194); upstream test_watch.py unchanged, 181 passed
- T36.4 done: L6 7d9fbf8, L8 34510f8, N5 b80a115, L10 accepted (0.1 ms measured), L13 pinned; test leak fix 728c6a3
- T36.5 done: 6209 passed / 14 skipped; extractors diff empty; findings moved (87eb37a); CI 36223498678 green
- T36 done (all steps): P05-S005 (rr-s5) Registry robustness — M1 E4 M5 M3 L6 L7 L8 L10 L13 N5
- T36 (plan 05 S5, rr-s5 ef2012a..87eb37a): M1, E4, M5 (GRAPHIFY_LANG_PATH implemented, in E1 fingerprint), M3 (watch hooks), L6, L7, L8, N5 fixed; L10 accepted (measured), L13 pinned. pytest 6209 passed / 14 skipped; CI 36223498678 green.

### 2026-09-26 15:57 (UTC+10)

- T35.6 done: pytest 6195 passed / 14 skipped; extractors diff empty; H1 H3 M2 L9 L11 E1 E5 moved to cc-CR000.002 (E3 open for S006)
- T35 done (all steps): P05-S004 (rr-s4) Build coherence — H1 E3 E5 H3 L9 L11 M2 E1
- T35 plan 05 S4 build coherence on rr-s4 (a5961fe..HEAD): incremental parity (E5) passes on all 8 plugin fixture trees via [resolve] context_fields registry hooks in watch.py and cli.py (H1)
- H3/L9: cargo and cc-kb augments pure, new cargo resolver; case_007 cargo 16/5/5 and claude-config cc-kb counts unchanged (case_008 §3)
- L11 normpath; M2/E1 AST cache namespace -lang<fingerprint>; ltm 1484 superseded by 1490
- pytest 6195 passed, 14 skipped; findings H1 H3 M2 L9 L11 E1 E5 moved to cc-CR000.002; E3 open until the S006 PR draft

### 2026-09-26 15:53 (UTC+10)

- T35.5 done: 2e2cba1: -lang<fp> AST namespace per plugin set; M2 and E1 tests pass; ltm 1484 superseded by learning 1490 (no update path for learnings)

### 2026-09-26 15:51 (UTC+10)

- T35.3 done: 22855e9: pure cargo/cc-kb augments + cargo resolver; case_007 cargo 16/5/5 and claude-config cc-kb counts unchanged
- T35.4 done: dc8a8ec: astgrep ruleDirs normpath; test_l11_dotdot_ruledirs passes

### 2026-09-26 15:47 (UTC+10)

- T35.2 done: 2adf7bc engine hook (watch.py + cli.py context_fields lookup), cd55efb plugins; E5 parity passes on 8 fixture trees

### 2026-09-26 15:43 (UTC+10)

- T35.1 done: a5961fe: 13 strict xfail red tests (E5 x7, H3 x2, L9, L11, M2, E1), cargo parity + M2 shared-cache pass

### 2026-09-26 15:31 (UTC+10)

- T34 done (plan 05 S3, rr-s3 542f417..70fc7fe): graphify_lang/_common.py shared plugin core; H2, M4, M6 (D1), L3, L5, L12, N3, E2, E8 fixed, E7 closed per D-008; pytest 6178 passed / 14 skipped; CI 36220807200 green (3.10/3.12/3.13, security); corpus counts in docs/testing/case_008 (only change: autolithp .lsp/.md sidecar pairs split, sidecar_doc 1 -> 63).

### 2026-09-26 15:30 (UTC+10)

- T34.1 done: 542f417: 8 strict-xfail red tests (H2 x2, M4 x5, M6)
- T34.2 done: 2c3e6e9: _common.py (Sink, refs_of, pick_by_prefix, load_manifest, load_builtins); bmake counts unchanged
- T34.3 done: 05ddbef..b244901: ecschema, astgrep, vba, autolisp, cc-kb, cargo moved one commit each
- T34.4 done: afa4015: case_008 id form and corpus counts; H2/M4 tests pass
- T34.5 done: 3fa02c2..e837ed2: M6 prefix rule, N3 keys, L3/E8, L12; lang list 9
- T34.6 done: 70fc7fe: pytest 6178 passed/14 skipped; extractors diff empty; CI 36220807200 green; findings moved, E7 closed per D1
- T34 done (all steps): P05-S003 (rr-s3) Shared plugin core — E2 L5 H2 M4 M6 E7 L3 E8 N3 L12

### 2026-09-26 15:04 (UTC+10)

- T33 (plan 05 S2, branch rr-s2) done: M7, M8, E9, M9, M10, N6 fixed in 711dfc6..57efe47 and moved to cc-CR000.002
- Fork CI now runs on rr-*; first run failed on 3.10 (tests/lang/test_rules.py bare tomllib), fixed 3d3b99f; run 36219115105 green on 3.10/3.12/3.13
- pytest 6154 passed, 14 skipped; three-dot extractor diff empty; baseline files unchanged

### 2026-09-26 15:03 (UTC+10)

- T33.1 done: 711dfc6: workflows restored from upstream/v8 plus guard line; all 4 parse
- T33.2 done: 23735ce: triggers autolisp, lang-*, rr-*, v8, v* tags; bandit graphify_lang 0 issues
- T33.3 done: 1f8a2e4: 38 junk files removed, .sidecar-cache/ ignored; git-sp.ps1 kept
- T33.4 done: 1e2e430: install-mcp.sh and 16-MCP-SETUP.md deleted; T9.5 text fixed
- T33.5 done: pushed rr-s1, rr-s2; CI 36219014956 failed (3.10 tomllib), fixed 3d3b99f; 36219115105 green
- T33.6 done: 57efe47: pytest 6154 passed/14 skipped; extractor diff empty; findings moved to cc-CR000.002
- T33 done (all steps): P05-S002 (rr-s2) Repo and CI hygiene — M7 M8 E9 M9 M10 N6

### 2026-09-26 13:52 (UTC+10)

- bash: grep -n "04" docs/plans/00-INDEX.md | head; pwsh -NoProfile -File ~/.claude/skills/repo-docs/scripts/repo-docs.ps1 mani…, rtk grep -c "| DONE |" docs/plans/00-INDEX.md; grep "04-content" docs/plans/00-INDEX.md | rtk grep -o "| [A-Z]* |$"; rt…, graphify --version; graphify lang list | cut -c1-20 | tr '\n' ' '; echo; cd ~/repos/graphify-lang && git log --oneline …, cd ~/repos/graphify-lang && git remote -v | cat && git push origin autolisp lang-sniff lang-rules lang-vba lang-bmake l…, cd ~/.claude && rtk git add CLAUDE.md && git commit -q -m "docs(CLAUDE): graphify fork now graphs VBA, bmake, Cargo, as…, git fetch -q upstream 2>&1 | tail -2; git diff --stat upstream/v8...autolisp | tail -80; rtk ls .claude/docs/ (+105 more)
- edit: .claude/docs/cc-CR000.001.md, docs/plans/05-review-remediation-cc-cr000-001.md, docs/plans/05-S001-security-and-crash-safety.md, docs/plans/05-S002-repo-and-ci-hygiene.md, docs/plans/05-S003-shared-plugin-core.md, docs/plans/05-S004-build-coherence.md (+4 more)
- T32.1 done: 1e678c5 029c35e: 13 red tests, strict xfail
- T32.2 done: f3357fb: 9 alias levels >30 s -> 0.04 s
- T32.3 done: 10f235b: 20k props 25.1 s -> 0.18 s; corpora byte-identical
- T32.4 done: d498a6f (engine): 9 languages load
- T32.5 done: 141b63f: 6154 passed/14 skipped; findings in cc-CR000.002
- T32 done (all steps): P05-S001 (rr-s1) Security and crash safety — H4 E6 L1 L2 L4 N4
- T32 (plan 05 S1, branch rr-s1) done: H4, E6, L1, L2, L4, N4 fixed test-first; commits 1e678c5 029c35e f3357fb 10f235b d498a6f 141b63f; pytest 6154 passed / 14 skipped; corpus graphs byte-identical to autolisp; findings moved to .claude/docs/cc-CR000.002.md. Note: `git diff upstream/v8 -- graphify/extractors/` is non-empty from upstream drift (25 commits since merge-base); fork diff vs merge-base is empty.

## 4. LAST SESSION

### 2026-09-25 18:08 (UTC+10)

- T31 done (plan 04 S15-S17): 27c85f2 release 0.9.67+lang.3 (pyyaml runtime dep), autolisp fast-forwarded, local tag v0.9.67+lang.3 (nothing pushed), pipx venv on the lang.3 wheel with [mcp,commonlisp] extras; 12 graphs rebuilt with plugin nodes; learnings 1481-1484; CLAUDE.md graphify paragraph updated; plan 04 DONE.
- Deviation: pipx install used the README form with [mcp,commonlisp] extras and the wheels dir copy, not a bare `pipx install --force dist/...whl`, which would drop the mcp extra that both MCP servers need.
- Open: running Claude Code/OMP sessions keep the lang.1 MCP server process until restarted; upstream's zero-node warning for DOC yml (tmllm 00-POLICY.yml, fixtures/*.yml, repo-docs policy.yml) predates plan 04 (tmllm counts unchanged).

### 2026-09-25 18:07 (UTC+10)

- bash: S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad; for i in $(seq 1 55…, S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad; n0=$(grep -c ALLDON…, S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad; python3 - <<EOF
  imp…, S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad; grep -nE "^== |zero…, PY=~/.local/share/pipx/venvs/graphifyy/bin/python; $PY - <<'EOF'  # graphify: skip classifying specific known files, no…, S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad; PY=~/.local/share/p… (+3 more)
- T31.2 done: 12 graphs rebuilt (graph.pre-plan04.json backups, cache/ast cleared, graphify update, exit 0 each; semantic nodes kept). Nodes/edges before->after: bim-chk 421->818/381->1598; bentley-model-management 290->1406/300->4282; BentleyTools 33871->36395/34108->44499; BentleyHelp 6256->22230/12245->36945; bentley-pyplace 3770->3777/7396->7475; moxide 6045->6046/15030->15075; oa-graph 2433->2434/3970->3977; oag-dev 2586->2587/4091->4096; tmllm 4623/11629 unchanged; llm-linter-tool 1580->1662/2785->2882; claude-config 47567->47568/52295->64638 (12104 cites); ~/.claude 18256->18260/22925->33774 (10594 cites). Second no-change update identical on all 12; changed_paths incremental on scratch copies (bim-chk 6 VBA files, BentleyHelp 9 mki/mke/ecschema) kept every cross-file edge. graph_stats via MCP works on all 12. Rollback in plan 04 R5.
- T31.3 done: Learnings ltm ids 1481-1482 (repo:graphify-lang: sniff router, augment kind), 1483-1484 (global: reconcile drops unbacked references edges, AST cache key excludes plugin code). $CLAUDE_HOME/CLAUDE.md graphify paragraph lists the 6 new plugins (matches graphify lang list). README layout table lists graphify_lang plugins. Plan 04 DONE.
- T31 done (all steps): P04-E Release, rebuild graphs, docs — plan 04 S15-S17

### 2026-09-25 18:05 (UTC+10)

- bash: cd ~/repos/graphify-lang && git log --oneline 09c488a..lang-cc-kb | cat; git merge-base --is-ancestor autolisp lang-cc-…, cd ~/repos/graphify-lang && rtk git add .claude/docs/cc-LR000.002.md docs/20-PROGRESS.md docs/25-HISTORY.md docs/30-TOD…, git status --short | head; rtk git log --oneline -1; rtk ls docs/plans; rtk wc -l docs/plans/04-*.md docs/plans/03-*.md…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "T31 plan 04 S15-S17…, rtk read docs/plans/04-*.md; echo ======; rtk read docs/plans/03-*.md, grep -n "lang.2\|lang\.1\|version" pyproject.toml | head; grep -n "dependencies" -A25 pyproject.toml | head -50; rtk gi… (+25 more)
- T31.1 done: 27c85f2 pyyaml>=6.0 runtime dep + 0.9.67+lang.3; pytest 6141 passed 14 skipped; extractors diff empty; autolisp ff to 27c85f2; local tag v0.9.67+lang.3 (not pushed); wheel graphifyy-0.9.67+lang.3 has 6 new plugin dirs + templates; pipx install with [mcp,commonlisp] extras (README form) - graphify 0.9.67+lang.3, lang list 9 languages, yaml 6.0.3 in venv, MCP server initialize reports 0.9.67+lang.3; skill refreshed via _copy_skill_file('claude')

### 2026-09-25 17:58 (UTC+10)

- bash: cd ~/repos/graphify-lang && git log --oneline 8a07307..lang-cc-kb | cat; .venv/bin/python -m pytest tests/lang/test_cc_…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "cc-kb augment cites…, rtk read graphify_lang/cc_kb/augment.py graphify_lang/cc_kb/resolve.py graphify_lang/cc_kb/__init__.py; sed -n 1,80p /h…, grep -n "cc_kb_refs\|resolver_registry\|def _get_extractor\|augment" graphify/extract.py graphify/resolver_registry.py …, rtk ls tests/lang; grep -rln "cc_kb" tests/ | head; git show --stat 9aa125f 09c488a | cat, cat tests/lang/test_cc_kb.py; for f in $(find tests/lang/fixtures/cc_kb tests/lang/fixtures/cc_kb_plain -type f); do ec… (+35 more)
- Plan 04 D12 (ae3d751): cc-kb cites edges (cc_ref, code_ref) are also added from the mention's heading node, one per section and target, on top of the unchanged page edges. Heading-only and first-section-only variants were measured and rejected (Q1 16 and 8).
- S14 on the ~/.claude scratch copy, all+D11 -> D12: Q1 7, Q2 18 -> 14 (17 citers), Q3 miss -> 3, Q4 2, Q5 9. Edges 22863 -> 29969. A second update kept all 10211 augment edges; tmllm has 0 extra edges; pytest 6141 passed, 14 skipped; extractor diff empty.
- 7595070: the cc-kb graph test uses its own cache_root, because the AST cache key does not cover plugin code. case_007 D12 section and S14 columns are in fed543e.

### 2026-09-25 17:42 (UTC+10)

- bash: rtk git log --oneline 3e9e9fe..HEAD, cd ~/repos/graphify-lang && git log --oneline lang-ecschema..lang-cc-kb | cat && git diff --stat upstream/v8 lang-cc-kb…, cd ~/repos/graphify-lang && python3 - <<'EOF'
  p='docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "extend cc-kb augmen…, rtk read graphify_lang/cc_kb/*.py graphify_lang/cc_kb/graphify-lang.toml; grep -n "D5\b\|D6\b\|D10\|D11\|### 3.3" docs/…, sed -n 60,90p docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md; grep -n "cc-kb\|S14\|cc_kb" doc… (+36 more)
- D11 on lang-cc-kb (9aa125f): cc-kb augment also reads root *.md, agents/**/*.md, skills/**/*.md of a harness root (docs/ holds a cc-*.md); cites edges only, attrs/hub_spoke stay on docs/cc-*.md. ~/.claude scratch: +325 edges (cc_ref 1776, code_ref 1088), base nodes identical; tmllm 0 extra edges; D10 recount 0 semantic-backed of 131.
- S14 all + D11 column in case_007 (09c488a): Q1 7, Q2 18, Q4 2, Q5 9; Q3 still missed (page-node edge is 3 hops from the Retrieval heading, default depth 2). pytest 6140 passed / 14 skipped.

### 2026-09-25 16:35 (UTC+10)

- bash: cd ~/repos/graphify-lang && git log --oneline lang-astgrep..lang-ecschema | cat && git diff --stat upstream/v8 lang-ecs…, cd ~/repos/graphify-lang && rtk git branch --show-current && rtk grep -n "hook_suffixes\|^suffixes\|^\[language\]" grap…, cd ~/repos/graphify-lang && grep -rn "hook_suffixes\|_HOOK_SOURCE_EXTS" graphify/lang_registry.py graphify/cli.py graph…, cd ~/repos/graphify-lang && .venv/bin/python -c "
  import graphify.cli as c; print([s for s in ('.yml','.xml','.mki','.b…, cd ~/repos/graphify-lang && python3 - <<'EOF'
  p='docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.…, rtk git log --oneline -1 && rtk git status --short && rtk ls graphify_lang/ && rtk wc -l docs/plans/04-*.md graphify/la… (+63 more)
- T30.1 done: cc-kb augment 9b266d3 plus engine commits 271a06c/635ea9c/01c76a2/81b7fcc. On ~/.claude: 241 hub_spoke, 1555 cc_ref, 984 code_ref edges; every mention resolves or is dangling; 0 RF000 pairs missing. Relation is cites, not references, because watch reconciliation prunes references.
- T30.2 done: S14: all four elements kept (none pushes a relevant node out of budget); results in docs/testing/case_007 (8a07307; the TODO text says case_005).
- T30 done (all steps): P04-D (lang-cc-kb) KB markdown augment and value test — plan 04 S13-S14
- T30 done on branch lang-cc-kb. Step 0: hook set now includes every manifest's hook_suffixes (.yml .yaml .xml added). D10: 0 of 1277 cc docs skip the AST pass, so no hook added. cc-kb augment plus value test; 6136 passed / 14 skipped. Details in docs/testing/case_007.

### 2026-09-25 16:11 (UTC+10)

- bash: cd ~/repos/graphify-lang && git log --oneline lang-cargo..lang-astgrep | cat && git diff --stat upstream/v8 lang-astgre…, rtk git log --oneline -1 && ls graphify_lang/ graphify_lang/astgrep tests/lang | head -80 && grep -n "ecschema\|ECSchem…, rtk git checkout -q -b lang-ecschema && rtk git status --short && rtk read graphify_lang/astgrep/graphify-lang.toml gra…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "ECSchema XML plugin…, head -c 3000 /home/p4ndr/.claude/cache/phase0/graphify-lang/phase0-20260925-160138.md; echo; rtk read graphify_lang/ast…, rtk read graphify_lang/astgrep/resolve.py && grep -n "RESOLVER\|class LanguageResolver\|def resolve" -r graphify_lang/b… (+34 more)
- edit: graphify_lang/ecschema/extract.py, graphify_lang/ecschema/resolve.py, tests/lang/test_ecschema.py
- T29.5 done: ecschema plugin on lang-ecschema (a6bdbb9 engine UTF-16 sniff, 2d07933 plugin, 2632d4f tests, 3e9e9fe case 007). Class nodes 5130/3 vs tag grep 5134/3 (4 explained); PSMaml .xsd unclaimed; pytest 6126 passed, 14 skipped.
- T29 done (all steps): P04-C Language plugins, one branch each — plan 04 S8-S12
- Plan 04 S12 (T29.5): ecschema plugin on branch lang-ecschema; .xml claimed only on a root <ECSchema (any prefix), 63 files changed class across ~/repos + ~/.claude (58 BentleyHelp, 1 bentley-pyplace, 4 fixtures); 64 other .xml and 165 .xsd unchanged vs GRAPHIFY_LANG_DISABLE=1.
- Engine commit a6bdbb9: sniff decodes a UTF-16 head with a BOM (7 BentleyHelp schemas were read as binary).
- Counts in docs/testing/case_007 ecschema section; pytest 6126 passed, 14 skipped.

### 2026-09-25 16:00 (UTC+10)

- bash: cd ~/repos/graphify-lang && rtk git branch --show-current && git log --oneline lang-bmake..lang-cargo | cat && git diff…, cd ~/repos/graphify-lang && sed -i '1s/^# Case 005/# Case 007/' docs/testing/case_007_plan04-sniff-and-plugins.md && gi…, rtk git log --oneline -1 && grep -n "^#\|astgrep\|ast-grep" docs/plans/04-content-sniffing-augment-plugins-and-five-new…, sed -n 70,100p graphify/extractors/markdown.py; sed -n 150,175p graphify/manifest_ingest.py; ls ~/.local/share/pipx/ven…, rtk read graphify_lang/bmake/graphify-lang.toml graphify_lang/cargo/graphify-lang.toml graphify_lang/bmake/__init__.py …, rtk read graphify_lang/bmake/resolve.py graphify_lang/cargo/__init__.py graphify_lang/cargo/augment.py tests/lang/test_… (+27 more)
- edit: graphify_lang/astgrep/extract.py, graphify_lang/astgrep/resolve.py, tests/lang/test_astgrep.py
- T29.4 done: astgrep plugin on lang-astgrep (680ce58, 9c6be53, f6b6cc9): llm-linter-tool 82/82 yml code, 27 rule nodes = 27 rules/**/*.yml with ^id:, 1 tested_by per rule; 18 other yml under ~/repos stay document; pytest 6113 passed / 14 skipped.
- Plan 04 S11 (T29.4): ast-grep plugin graphify_lang/astgrep on branch lang-astgrep (680ce58 plugin, 9c6be53 tests, f6b6cc9 case 007). .yml/.yaml claimed only via [match] globs + sniff (D3).
- Corpus llm-linter-tool 4123a92: 27 rule nodes = 27 rules/**/*.yml with ^id:; 27 tested_by (1 per rule), 27 has_snapshot, 27 sgconfig loads; the other 18 .yml under ~/repos (7 workflows) stay document as on upstream.
- PyYAML is used when importable but is not a graphify dependency and is absent from the pipx venv; a flat top-level parser is the fallback (tested). pytest tests/ -q: 6113 passed, 14 skipped.

### 2026-09-25 15:50 (UTC+10)

- bash: rtk git status --short; rtk git log --oneline 241d085..HEAD, cd ~/repos/graphify-lang && rtk git branch --show-current && git log --oneline lang-vba..lang-bmake | cat && git diff -…, rtk git log --oneline -1 && grep -n "^#\|D9\|cargo" docs/plans/04-content-sniffing-augment-plugins-and-five-new-languag…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "cargo augment plugi…, rtk wc -l graphify/lang_registry.py graphify_lang/registry.py && rtk read graphify/lang_registry.py, rtk read graphify_lang/registry.py; rtk ls graphify_lang graphify_lang/bmake tests/lang; rtk read graphify_lang/bmake/g… (+37 more)
- edit: tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad/m1.py, graphify_lang/cargo/augment.py, tmp/claude-1000/-home-p4ndr-repos-graphify-lang/d0e1fb12-471c-4d42-a019-0286ec26da55/scratchpad/m2.py, tests/lang/test_cargo.py
- T29.3 done: cargo augment on lang-cargo (d3d052d engine hook, 1e8244c plugin, 8e3ddca case 007): has_member edges = cargo metadata members for moxide 16, oa-graph 5, oag-dev 5; pytest 6102 passed/14 skipped
- S10/T29.3: _get_extractor registry hook (augment_extractor) wraps extract_package_manifest when an augment's [match] claims the path; cargo augment adds workspace node, has_member edges, external_deps attr, renamed path-dep edges. Member edges match cargo metadata on the 3 workspace repos; tmllm/llm-linter-tool have no [workspace] (0 vs cargo's implicit 1); comment-sidecar has no Cargo.toml; pyproject.toml 3/3 byte-identical.

### 2026-09-25 15:40 (UTC+10)

- bash: cd ~/repos/graphify-lang && rtk git branch --show-current && git log --oneline lang-rules..lang-vba | cat && git diff -…, cd ~/repos/graphify-lang && git mv docs/testing/case_005_plan04-sniff-and-plugins.md docs/testing/case_007_plan04-sniff…, rtk git checkout -q -b lang-bmake 241d085 2>&1; rtk git branch --show-current; rtk ls graphify_lang/ graphify_lang/vba …, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "bmake plugin for Be…, P=docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md; grep -n "^#\|bmake\|D[0-9]\+\b" $P | head -…, sed -n 60,112p docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md; rtk read graphify_lang/vba/__i… (+38 more)
- edit: graphify_lang/bmake/extract.py, graphify_lang/bmake/resolve.py, tests/lang/test_bmake.py
- T29.2 done: S9 lang-bmake: .mki/.mke extractor; corpus BentleyHelp
- T29.2 (plan 04 S9) bmake plugin on branch lang-bmake: 6eb7cfa feat, 6a67e36 tests, 483d6ae case_007 section.
- BentleyHelp 95b9a95: grep -c %include 206 = 199 directives + 7 comment lines; 135 resolved -> 113 imports edges, 64 kept as unresolved_includes (46 not in repo, 18 computed); 0 dangling edges.
- pytest tests/ -q: 6096 passed, 14 skipped; git diff upstream/v8 -- graphify/extractors/ empty; wheel carries graphify_lang/bmake + entry point.

### 2026-09-25 15:26 (UTC+10)

- bash: cd ~/repos/graphify-lang && .venv/bin/python -c "import graphify,graphify_lang;print(graphify.__file__, graphify_lang._…, graphify query "AutoLISP plugin registration manifest extract resolve" 2>&1 | head -40, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "VBA language plugin…, cd /home/p4ndr/repos/graphify-lang/graphify_lang/autolisp && rtk read graphify-lang.toml dcl.toml __init__.py resolve.p…, P=docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md; grep -n "^#" $P | head -60; rtk wc -l $P, rtk read docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md (+32 more)
- edit: graphify_lang/vba/extract.py, graphify_lang/vba/resolve.py, tests/lang/test_vba.py, docs/testing/case_005_plan04-sniff-and-plugins.md
- T29.1 done: VBA plugin on lang-vba (9cefa7d, 6486c9b, f0f2947): proc nodes = grep on all 3 repos (2236/995/347), ThisWorkbook.cls 8 nodes, Apex sample.cls unchanged; pytest 6086 passed / 14 skipped
- T29.1 (plan 04 S8) done on branch lang-vba: graphify_lang/vba (line-scanner extractor, cross-module resolver, builtins list) as two manifests, vba (.bas .frm) and vba-cls (.cls, sniffed against extract_apex); commits 9cefa7d, 6486c9b, f0f2947, not pushed.
- Corpus: Sub/Function/Property nodes match grep exactly on BentleyTools 2236, bentley-model-management 995, bim-chk 347; all 30 .cls routed to vba; ThisWorkbook.cls 1 -> 8 nodes; counts in docs/testing/case_005_plan04-sniff-and-plugins.md.
- pytest 6086 passed / 14 skipped; git diff upstream/v8 -- graphify/extractors/ empty; lang_baseline.txt and upstream_tables.json unchanged.

### 2026-09-25 15:11 (UTC+10)

- bash: rtk git status --short && rtk git log --oneline -2, cd ~/repos/graphify-lang && rtk git branch --show-current && git log --oneline lang-sniff..lang-rules | cat && git diff…, cd ~/repos/graphify-lang && rtk ls build && git check-ignore -q build && rm -rf build && echo removed
- P17 settled: Option 1: mark T6.2, T6.4, T7.4, T8.2, T8.4 superseded by plan 02 and A6; their outcomes are met or deliberately exclud…
- P15 settled: Moot: plan 03 replaced stock graphify with the fork on this host, so only one AST cache writer exists. Reopen if stock…
- T5.2 done: Superseded by T28 (plan 04 S7, D-008)
- T5.3 done: Superseded by T28 (plan 04 S7, D-008)
- T5.4 done: Superseded by T28 (plan 04 S7, D-008)
- T5.5 done: Superseded by T28 (plan 04 S7, D-008)
- T5.6 done: Superseded by T28 (plan 04 S7, D-008)
- T5 done (all steps): S005 (autolisp) Rules runtime and manifest templates — plan §S005
- T6.2 done: Superseded by plan 02 / A6 (P17 option 1)
- T6.4 done: Superseded by plan 02 / A6 (P17 option 1)
- T6 done (all steps): S006 (autolisp) AutoLISP nodes — plan §S006
- T7.4 done: Superseded by plan 02 / A6 (P17 option 1)
- T7 done (all steps): S007 (autolisp) AutoLISP edges and the cross-file resolver — plan §S007
- T8.2 done: Superseded by plan 02 / A6 (P17 option 1)
- T8.4 done: Superseded by plan 02 / A6 (P17 option 1)
- T8 done (all steps): S008 (autolisp) DCL and MNL — plan §S008

### 2026-09-25 13:40 (UTC+10)

- bash: cd ~/repos/graphify-lang && rtk git branch --show-current && git log --oneline autolisp..lang-sniff | cat && git diff -…, cd ~/repos/graphify-lang && git stash list | head -2; git status --short | head; python3 - <<'EOF'
  p='docs/plans/04-con…, rtk git status --short && rtk git log --oneline -1 && rtk ls graphify_lang graphify_lang/templates tests/lang && grep -…, grep -n "S7\b\|## S7\|S7 " docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md | head; grep -n "P1…, grep -n "^#\|S005\|emission\|contract" docs/plans/01-language-extension-layer-and-autolisp-plugin.md | sed -n '1,80p', rtk read docs/plans/01-language-extension-layer-and-autolisp-plugin.md; rtk ls docs/plans (+44 more)
- edit: graphify_lang/rules.py, graphify_lang/builtins.py, graphify_lang/queries.py, graphify_lang/regex_rules.py, tests/lang/test_rules.py
- T28.1 done: 91f26cd: file node, contract keys, _file_stem ids + line on clash, in-file @reference/edge= calls, builtins filter
- T28.2 done: 91f26cd query tier errors (not installed / failed to load) + Python predicates; 8fbefec templates in package-data, wheel lists graphify_lang/templates/*.toml
- T28.3 done: 91f26cd test_rules.py 25 real tests (19/22 red on a68c964); rules_dcl.toml equals extract_dcl nodes+edges on fixture .dcl files
- T28 done (all steps): P04-B (lang-rules) Repair the regex rules runtime to the S005 emission contract…
- T28 done on branch lang-rules (8fbefec, 91f26cd): the rules runtime now meets the S005 contract. Red at a68c964, measured on err.lsp: 27 nodes with no label/source_file/file_type, 0 query nodes, no file node, 0 edges. Green: both the regex tier and the tags.scm tier give 27 function nodes, 1 file node, 27 contains edges and 29 in-file calls edges, and the two tiers produce the same output.
- tests/lang/rules_dcl.toml (rules-based DCL) matches extract_dcl nodes and edges on every fixture .dcl. The query tier now errors instead of returning nothing: a missing grammar gives 'not installed'; a bad or missing query, rule or hook gives 'failed to load'. py-tree-sitter 0.23 inverts #not-match? and ignores #any-of?, so text predicates are now evaluated in Python.
- pytest tests/ -q: 6076 passed, 14 skipped (baseline 6065/14). The tree-sitter 0.23 run of test_rules passes 25/25. The wheel contains graphify_lang/templates/*.toml. Found: a stale build/lib from Sep 21 adds graphify_lang/autolisp/queries/tags.scm to in-tree wheel builds.

### 2026-09-25 13:19 (UTC+10)

- bash: rtk read docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md && rtk git log --oneline -3 && rtk gi…, rtk read graphify/lang_registry.py && rtk read graphify_lang/registry.py && rtk read graphify_lang/manifest.py && rtk r…, pwsh -NoProfile -File $HOME/.claude/scripts/phase0.ps1 -Repo /home/p4ndr/repos/graphify-lang -Task "content-sniff route…, rtk read /home/p4ndr/.claude/cache/phase0/graphify-lang/phase0-20260925-130317.md --max-lines 60; rtk read graphify_lan…, sed -n 6700,6780p graphify/extract.py; grep -n "def _get_extractor" -A60 graphify/extract.py | head -90; grep -n '"\.ls…, sed -n 1,80p tests/test_lang_registry.py; grep -n "upstream_tables\|lang_baseline" -r tests/*.py tools/ | head; grep -n… (+35 more)
- edit: tests/test_lang_sniff.py
- T27.1 done: 7181bea: 6 fixtures + tests/test_lang_sniff.py; 14 red (13 AttributeError no dispatch_table, 1 _get_extractor still extract_apex)
- T27.2 done: eda6b03: manifest [sniff]/[match]/kind/augments/overrides/priority; 8 schema tests pass
- T27.3 done: 135113d: dispatch_table + sniff_router[.cls]; S1 tests green; .lsp stays extract_autolisp; lang list sniff column + * marker
- T27.4 done: f893e65: classify_file claims_file hook; detect ~/.claude 0.716s -> 0.718s; upstream_tables.json unchanged
- T27.5 done: 355831d: augmented[.md] wrapper, prefix/no-overwrite merge, composed with router; base md nodes unchanged
- T27.6 done: 0761cf5 docs, a68c964 version 0.9.67+lang.2, local tag v0.9.67+lang.2; pytest 6065 passed 14 skipped
- T27 done (all steps): P04-A (lang-sniff) Sniff router, detect hook, augment kind — plan 04 S1-S6
- T27 done on branch lang-sniff (7 commits 7181bea..a68c964, local tag v0.9.67+lang.2, not pushed): sniff router, [match] detect hook in classify_file, augment kind; pytest 6065 passed / 14 skipped (baseline 6026); git diff upstream/v8 -- graphify/extractors/ empty; upstream_tables.json and lang_baseline.txt unchanged.
- Open for S10: Cargo.toml and pyproject.toml are already CODE upstream via is_package_manifest_path, and _get_extractor sends them to extract_package_manifest before _DISPATCH, so a [match] cargo plugin on .toml is never called by the router.
- Phase 0 file: /home/p4ndr/.claude/cache/phase0/graphify-lang/phase0-20260925-130317.md

## 5. EARLIER SESSIONS
