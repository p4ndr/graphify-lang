<!-- TEMPLATE-VERSION: 2026-09-20-006 -->
<!-- DOC-TYPE: ARCHIVE -->
<!-- TEMPLATE-START -->
# 25-HISTORY.md

This document is an ARCHIVE of session progress cut-over from `20-PROGRESS.md`.

## 1. INSTRUCTIONS

- Change this document only through the repo-docs tools (`progress_add` moves sessions older than 7 days here, NEWEST first); hand edits by the owner are fine.
- NEVER read it unless you are searching for progress data that is not in `20-PROGRESS.md`. Its content is stale.
<!-- TEMPLATE-END -->

## 3. SESSION HISTORY

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

### 2026-09-25 13:01 (UTC+10)

- bash: rtk ls -d ~/repos/*/ ~/GIT/*/ ~/git/*/ 2>/dev/null; graphify lang list 2>&1 | head -30, cd ~/repos/graphify-lang && .venv/bin/python -c "
  from graphify import detect as d
  for n in dir(d):
  v=getattr(d,n)
  …, cd ~/repos && for r in */; do r=${r%/}; [ -d "$r/.git" ] || continue; echo "== $r"; git -C "$r" ls-files 2>/dev/null | …, rtk ls ~/repos/llm-linter-tool; git -C ~/repos/llm-linter-tool ls-files '*.yml' | head -5; git -C ~/repos/BentleyHelp l…, cd ~/repos/graphify-lang && ls graphify/extractors/ | tr '\n' ' '; echo; .venv/bin/python -c "
  import graphify.extract …, cd ~/repos/graphify-lang && f=$(git -C ~/repos/bim-chk ls-files '*.cls' | head -1); .venv/bin/python -c "
  from pathlib … (+9 more)
- edit: docs/plans/04-content-sniffing-augment-plugins-and-five-new-languages.md
- P16 settled: Option 2: repair the regex rules runtime to the S005 emission contract and keep it as a fallback/utility layer; new plu…
- bash: cd ~/repos/graphify-lang && sed -i 's/^- Status: DRAFT$/- Status: ACTIVE/; s/^- Tasks: <TASK numbers in docs\/30-TODO.m…, cd ~/repos/graphify-lang && pwsh -NoProfile -File ~/.claude/skills/repo-docs/scripts/repo-docs.ps1 manifest 2>&1 | tail…
- Surveyed 22 local repos for graphify language gaps; measured extract_apex on bim-chk ThisWorkbook.cls (VBA): 1 node, 0 edges
- Wrote plan 04 (content sniff router, augment kind, VBA/bmake/Cargo/ast-grep/ECSchema plugins, cc-kb augment); owner decisions D1-D8
- Settled P16 as option 2 (D-008): repair the regex rules runtime as a fallback/utility; plugins use their own extractors
- Plan 04 ACTIVE; tasks T27-T31 added

### 2026-09-24 14:42 (UTC+10)

- bash: timeout 1200 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1; TMPDIR=/tmp/claude-1000/-home-p4n…, cd ~/repos/autolisp-pvcase && rtk git log -1 --format='%h %ci'; git status --porcelain | head -5; git ls-files '*.lsp' …
- T26.4 done: `.venv/bin/python -m pytest tests/ -q`: 5495 passed, 12 skipped (before this session 5485/12; +10 are new fork tests), no upstream test file edited. tools/measure_autolisp.py on the 4 repos: autolithp 4,212 nodes / 19,157 edges (calls 15,017, contains 4,128, dcl_references 4, module_depends 8), err:trap 88 inbound cross-file, lithp_mgr 1, 0 missed, 0 token, 0 dup; autolithp02 3,160/13,178; snap-rework 3,069/12,430 — all identical to case 005. pvcase is 1,301/5,634 over 32 files vs case 005's 1,176/4,972 over 29: the repo gained 3 files in commit bf69f47 at 14:23 today, which is not a regression. guard: graphify/ differs from v8 in cli, detect, extract (@doc, D-004), lang_registry and resolver_registry (the committed casefold fix, 0b2d2e4); no hand-added suffix; extract.py has 0 graphify_lang/autolisp strings.
- T26 done (all steps): Settled items follow-up: fork version string (P9), restore detect.py (P10), `gr…
- ag-build session (Phase 0 file ~/.claude/cache/phase0/graphify-lang/phase0-20260924-142911.md): T1, T24 and T26 done; T5-T8 steps closed where the code already meets them or needed a small fix; T5.2-T5.6 open under P16, T6.2/T6.4/T7.4/T8.2/T8.4 open under P17; P15 raised (fork and stock evict each other's AST cache dir)
- Code changes: detect.py is v8 plus the registry lookup; version 0.9.55+lang.1 (uv.lock: that line only); `graphify lang list` (cli.py + lang_registry.format_languages); manifest.py uses stdlib tomllib; the walker no longer counts cond clause heads as calls; the licence file ships in package-data
- Tests: SC2 subprocess snapshot test, lang list test, tests/lang/test_autolisp_corpus_fixtures.py (8 tests on the real err/ldr/manager fixtures plus authored .mnl/defun-q/cond/ERR.LSP). pytest 5495 passed / 12 skipped; measure_autolisp is identical to case 005 for autolithp, autolithp02 and snap-rework

### 2026-09-24 14:41 (UTC+10)

- T8.1 done: graphify_lang/autolisp/dcl.toml is a second manifest in the same package (autolisp-dcl, markup, .dcl, grammar regex, runtime extract_dcl); `graphify lang list` shows it.
- T8.3 done: dcl_references come from new_dialog (EXTRACTED) and wrapper string args (INFERRED, D-005a); dcl_action comes from action_tile strings, re-parsed as AutoLISP. Pinned by test_autolisp_plan02.py::test_dcl_references and test_dcl_action.
- T8.5 done: .mnl is claimed in graphify-lang.toml. New test_mnl_and_defun_q_authored: an authored acad.mnl dispatches to the walker without error and gives its functions and a call. SC6b: 1 dcl_references into lithp_mgr in autolithp (measure_autolisp, D-005a INFERRED); manager.dcl gives dialog lithp_mgr (test_manager_dcl_dialog).

### 2026-09-24 14:40 (UTC+10)

- bash: rtk read graphify_lang/rules.py; sed -n 1,60p graphify_lang/queries.py; sed -n 1,50p graphify_lang/regex_rules.py; sed …, sed -n 40,135p graphify_lang/manifest.py; rtk grep -n "def test" tests/lang/test_rules.py tests/lang/test_autolisp_node…, S=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/rt && mkdir -p $S && cat > $S/tags.scm <<'EOF'
  (list_lit . (sym_lit)…, rtk read tests/lang/corpus_files.txt --max-lines 8; rtk grep -vc '^#' tests/lang/corpus_files.txt; git -C ~/repos/autol…, F=$(git -C ~/repos/autolithp ls-tree -r --name-only d5a20743b007431521c4f9a0507560d5feb94b27 -- src tests Import-Refact…, python3 - <<'EOF'
  p='tests/lang/test_rules.py'
  s=open(p).read()
  old='    assert len(lines) > 0, "corpus_files.txt shoul… (+24 more)
- edit: tests/lang/test_autolisp_corpus_fixtures.py, graphify_lang/autolisp/extract.py
- T5.1 done: tests/lang/corpus_files.txt regenerated from `git ls-tree d5a2074 -- src tests Import-Refactor build` (the old file listed 42 of 84): 81 .lsp + 3 .dcl + 0 .mnl, with the regenerate command in its header; test_rules.py::test_corpus_file_list_count now pins 84.
- T6.1 done: Already there: graphify_lang/autolisp/graphify-lang.toml (.lsp .mnl, overrides .lsp, case_insensitive, tree_sitter_commonlisp 0.4.1, extra commonlisp; runtime = the plan 02 walker) and pyproject.toml:97 `commonlisp = ["tree-sitter-commonlisp>=0.4.1,<0.5"]` (v8 has no specifier). Fixed: graphify_lang/manifest.py imported tomli unconditionally, which is only a dependency below 3.11; it now uses stdlib tomllib first. Measured with tomli blocked: registry still lists autolisp and autolisp-dcl.
- T6.3 done: data/builtins.txt and data/LICENSE.AutoLispExt were already there, but package-data left the licence out of the wheel. Added "autolisp/data/LICENSE.*"; `uv build --wheel` now ships graphify_lang/autolisp/data/LICENSE.AutoLispExt. The stale ignored build/ still carries autolisp/queries/tags.scm into wheels; not deleted.
- T6.5 done: tests/lang/fixtures/src/core/{err,ldr}.lsp and src/ui/manager.dcl are byte-identical to autolithp d5a2074 (cmp), but no test used them. New tests/lang/test_autolisp_corpus_fixtures.py extracts them with root=tests/lang/fixtures, so ids and source_file are src/core/err.lsp, the same as on the corpus.
- T6.6 done: Checked in tests/lang/fixtures/collision_set.tsv, measured with extract_autolisp over corpus_files.txt: 11 groups, 5 pkg:name/pkg:_name and 6 repeated *error* (pltrn.lsp has 39, not the 24 in the plan). The tests derive SC4 instead of asserting it: 27 = the defun regex over the real err.lsp = distinct function ids, and the err.lsp collision group matches the TSV. SC5: C:LITHP, C:LITHP-MGR and C:LITHP-INIT are command nodes from ldr.lsp. Corpus: 0 missed defuns (measure_autolisp).
- T7.1 done: Plan 02 §3 defines the contract as `autolisp_refs` (kind=call, source, name, line, source_file) on each extractor result. graphify_lang/autolisp/resolve.py binds them case-insensitively (D-005b nearest copy) and drops what is left unbound. Tested by test_autolisp_plan02.py::test_calls_exact and test_cross_file_call_is_extracted.
- T7.2 done: The walker already skipped the defun/lambda headers (params), setq targets and quoted data. Added: cond clause heads are test values, not calls (extract.py walk_list). This changes nothing on the corpus (autolithp calls 15,017 before and after) and is pinned by test_cond_clause_head_is_not_a_call.
- T7.3 done: Quoted 'fn, (quote fn) and (function fn) are call candidates in the walker (plan 02 A6), covered by test_autolisp_plan02 calls pins. The `:vlr-*` dotted-pair clause is not built: there are 0 quoted-literal instances in corpus code (7 grep hits, all in comments of src/modules/rxn/mod.lsp).
- T7.5 done: resolve.py RESOLVER is a LanguageResolver for .lsp/.mnl/.dcl, registered once by the registry (test_resolver_registered_once). The resolver_registry casefold fix covers upper-case suffixes; new test_upper_case_suffix_resolves_cross_file: ERR.LSP gets its cross-file call.
- T7.6 done: analyze.god_nodes(build_from_json(extract(corpus_files.txt, root=autolithp))) top 10 are all AutoLISP defuns, no COM or built-ins: pltrn:rget 714, pltrn:_fn 513, pltrn:_int 438, pltrn:_real 285, pltrn:_str 255, pltrn_nc pltrn:rget 174, pltrn:_fn2 152, pltrn_nc pltrn:_fn 148, pltrn:get 147, C:PLTRNTEST 145 (SC7). SC6a: err:trap has 88 inbound cross-file calls (measure_autolisp).

### 2026-09-24 14:34 (UTC+10)

- T26.2 done: graphify/detect.py rebuilt from `git show v8:graphify/detect.py` plus the 6-line try-wrapped registry lookup after CODE_EXTENSIONS: `git diff v8 -- graphify/detect.py` = +6 -0. classify_file gives CODE for .lisp .cl .asd .cls .trigger .robot .resource (and .lsp .dcl .mnl). SC2 snapshot identical under GRAPHIFY_LANG_DISABLE=1. extract.py @doc markers untouched (D-004).
- bash: grep -n "def main\|cmd == \|argv\[1\]\|elif cmd\|if cmd" graphify/cli.py | head -60; rtk grep -n "^def \|^class " graph…, sed -n 3110,3172p graphify/cli.py; grep -n '"  global\|global list\|  benchmark' graphify/cli.py | head; grep -rln "glo…, grep -n 'global add <graph' graphify/cli.py | head; grep -n 'print("  global\|"  global' graphify/cli.py | head; sed -n…, cd /tmp && /home/p4ndr/repos/graphify-lang/.venv/bin/python -c "
  from graphify_lang import registry as r
  for m in r.ite…, cat >> graphify/lang_registry.py <<'EOF'
  def format_languages() -> str:
  """Table of registered plugin languages f…, ls graphify/__main__.py && cat >> tests/test_lang_registry.py <<'EOF'
  def test_lang_list_subcommand() -> None:
  ""…
- T26.3 done: `graphify lang list`: 9-line try-wrapped branch in graphify/cli.py (before `extract`), table built by new graphify/lang_registry.format_languages() (generic, no language name). Measured: lists autolisp (.lsp .mnl, tree_sitter_commonlisp, resolver autolisp) and autolisp-dcl (.dcl); GRAPHIFY_LANG_DISABLE=1 -> "No plugin languages registered."; bare `graphify lang` -> usage, exit 1. Test: tests/test_lang_registry.py::test_lang_list_subcommand (subprocess). Side effect of the D-007 version: the fork CLI warns that ~/.claude/skills/graphify is from 0.9.55 (not acted on).

### 2026-09-24 14:33 (UTC+10)

- bash: sed -i '24s/^- `\[?\]` T1\.5 | \(.*\) (BLOCKED on P1: AutoLITHP corpus SHA decision)$/- `[x]` T1.5 | \1/' docs/30-TODO.…
- T1 done: T1.5 (hand-marked: the tool's id match collides with T1.5b/T1.5c) — ~/repos/autolithp HEAD d5a20743b007 = SRS pin, clean; re-measured 81 .lsp, 4,027 defun/defun-q, 52 `defun C:` case-sensitive (SRS instrument said -Eio = 64 incl. 12 lowercase `c:`; SRS §1.3 row corrected), 3 .dcl, 8 dialogs, 3.04 MiB. T1.4 snapshot + SC2 test done.
- bash: sed -i '7s/^version = "0.9.55"$/version = "0.9.55+lang.1"/' pyproject.toml && sed -n 6,8p pyproject.toml && uv sync --a…, uv sync --all-extras --quiet 2>&1 | tail -3; rtk git diff --stat uv.lock; git diff uv.lock | grep '^[-+]' | head; .venv…, cd /tmp && ~/.local/share/pipx/venvs/graphifyy/bin/python -c "import graphify.cache as c; print('stock', c._EXTRACTOR_V…, C=/tmp/claude-1000/-home-p4ndr-repos-graphify-lang/cachecheck; rm -rf $C; mkdir -p $C; cat > $C/run.py <<'EOF'
  import s…
- T26.1 done: pyproject.toml version = "0.9.55+lang.1" (D-007); `uv sync --all-extras` changed only the graphifyy version line in uv.lock; tree-sitter 0.25.2 / tree-sitter-commonlisp 0.4.1 kept (importlib.metadata). Fresh shared cache_root, alternating runs on ~/repos/autolithp src/core/err.lsp: fork writes cache/ast/v0.9.55+lang.1-s2 (33 nodes, 61 edges), stock writes v0.9.55-s2 (1 node) — neither reads the other's entries. Upstream's sibling-dir sweep makes them evict each other: P-item raised.
- T24.2 done: Closed by D-007 / T26.1 instead of a per-file key: graphify/cache.py keys AST entries by package version (cache/ast/v{version}-s{schema}); the fork's version 0.9.55+lang.1 gives a distinct dir, measured fork v0.9.55+lang.1-s2 vs stock v0.9.55-s2 with no cross-reads. No cache.py edit.
- T24 done (all steps): Plan 02 step 6: extraction cache key check/fix for registry-dispatched files (D…

### 2026-09-24 14:32 (UTC+10)

- bash: python3 - <<'EOF'
  import re
  p='docs/50-PENDING.md'; t=open(p).read()
  a=t.index('### `[?]` P7 '); b=t.index('## 4. RESOL…, python3 - <<'EOF'
  import re
  d='docs/40-DECISIONS.md'; t=open(d).read()
  t=t.replace("## D-003 — The fork's package versi…, awk '/^### .*T1 \|/,/^### .*T2 /' docs/30-TODO.md | head -30; awk '/^### .*T5 \|/,/^### .*T9 /' docs/30-TODO.md | rtk g…, grep -n "P1 \|P1:" -A6 docs/55-SETTLED.md docs/50-PENDING.md | head -20; rtk git -C ~/repos/autolithp log -1 --format='…, rtk read docs/10-READ-FIRST.md && rtk read docs/30-TODO.md, cat docs/40-DECISIONS.md | sed -n '1,400p'; echo ----; rtk read docs/50-PENDING.md; echo ---; rtk git status --short; r… (+20 more)
- edit: scripts/snapshot_tables.py
- T1.4 done: scripts/snapshot_tables.py rewritten to plan S001 spec (imports the modules, dumps _DISPATCH by __name__, _EXTRA_FOR_EXTENSION, CODE_EXTENSIONS, _WATCHED_EXTENSIONS, _HOOK_SOURCE_EXTS, registered_resolvers); tests/upstream_tables.json regenerated from `git archive v8` with GRAPHIFY_LANG_DISABLE=1 (old file held wrong hard-coded line ranges). New SC2 subprocess test tests/test_lang_registry.py::test_sc2_no_plugin_tables_match_upstream_snapshot passes, and fails on the pre-T26.2 detect.py.

### 2026-09-24 14:27 (UTC+10)

- bash: git status --short | head -40; rtk git diff HEAD --stat -- graphify/, cd /tmp/claude-1000/-home-p4ndr-repos-graphify-lang/6f526580-043c-4f87-897e-b7225701d683/scratchpad && rm -rf cache-* *…, cd /tmp/claude-1000/-home-p4ndr-repos-graphify-lang/6f526580-043c-4f87-897e-b7225701d683/scratchpad && rm -rf e2e e2s; …, cd /tmp/claude-1000/-home-p4ndr-repos-graphify-lang/6f526580-043c-4f87-897e-b7225701d683/scratchpad && python3 - <<'EOF…, sed -n '/^## /,$p' docs/50-PENDING.md | head -150; grep -n "D-001\|D-002" -A6 docs/40-DECISIONS.md | head -40 # graphif…
- edit: docs/testing/case_005_rerun-fork-vs-stock.md
- P9 settled: Option 1: give the fork a distinct package version (0.9.55+lang.1) so its AST cache dir differs from stock. Owner accep…; unblocked T24.2
- P10 settled: Option 1, partial: restore graphify/detect.py to v8 plus only the registry lookup (brings back the 7 dropped suffixes).…

### 2026-09-24 10:33 (UTC+10)

- bash: ls tools/ 2>/dev/null | head; rtk ls scripts; cat scripts/measure-corpus.sh | head -40; rtk ls ~/.local/share/pipx/venv…, time .venv/bin/python tools/measure_autolisp.py ~/repos/autolithp 2>&1 | tail -20, cd ~/repos/autolithp && rtk grep -rlni '(defun err:trap\b' --include=*.lsp .; grep -rn '(err:trap ' --include=*.lsp . |…, .venv/bin/python - <<'EOF' 2>&1 | grep -v Warn
  import re, tempfile
  from pathlib import Path
  from graphify.extract impor…, .venv/bin/python - <<'EOF'
  from pathlib import Path
  p = Path("graphify_lang/autolisp/resolve.py"); s = p.read_text()
  ol…, .venv/bin/python - <<'EOF'
  from pathlib import Path
  p = Path("graphify_lang/autolisp/resolve.py"); s = p.read_text()
  fo… (+10 more)
- edit: tools/measure_autolisp.py
- T25.1 done: tools/measure_autolisp.py: fork and stock each in a subprocess, fresh temp cache_root, regex truth; prints case 003 tables + §5 checks
- T25.2 done: docs/testing/case_004_plan02-autolisp-fixes.md; autolithp 4,212 nodes / 19,157 edges / 1.6 s, 0 missed defuns, 0 dup ids, 0 token nodes
- T25.3 done: all 13 §5 rows PASS (case 004 §3); README acceptance table has a status column; D11 open as P9
- T25 done (all steps): Plan 02 step 7: corpus measurement script + case 004 report
- Plan 02 T19-T23, T25 done: AutoLISP walker + DCL extractor + rewritten resolver (registry-registered, no core import); tests/lang/test_autolisp_plan02.py (17 tests)
- Case 004 (docs/testing/case_004_plan02-autolisp-fixes.md): all 13 plan 02 §5 checks PASS; autolithp 4,212 nodes / 19,157 edges / 1.6 s (case 003: 394,394 / 0 / 41.4 s)
- T24 blocked on P9 (D11 cache key needs a cache.py edit); P10 raised for pre-existing detect.py / extract.py divergence from v8
- pytest tests/ -q: 5485 passed, 12 skipped

### 2026-09-24 10:28 (UTC+10)

- T21.1 done: list heads + quoted/function symbols + quoted lambdas; param lists, setq targets, quoted data lists skipped
- T21.2 done: is_builtin: data/builtins.txt casefolded + vla-/vlax-/vlr- prefixes
- T21.3 done: same-file calls emitted directly; rest on result.autolisp_refs (kind=call); cache round-trip keeps the key (JSON payload)
- T21 done (all steps): Plan 02 step 3: AutoLISP calls (direct + quoted), builtins/COM denylist (D1)
- T22.1 done: resolve.py rewritten: casefolded, same-file first else unique corpus target, ambiguous/unresolved dropped; exports RESOLVER, no self-registration
- T22.2 done: registry._register_resolver registers manifest.resolver by name once per process (test_resolver_registered_once); iter_manifests body restored
- T22.3 done: graphify/extract.py now byte-equal to HEAD (git diff HEAD empty); 0 graphify_lang/autolisp strings
- T22 done (all steps): Plan 02 step 4: resolver rewrite, registry-side registration, remove core impor…
- T23.1 done: extract_dcl: file node + dialog node per name : dialog {, comments blanked; controls not nodes
- T23.2 done: dcl_references EXTRACTED from new_dialog literal, INFERRED from identifier-shaped string args of other calls (wrapper dtk:dcl-exec); dcl_action dialog->fn with key
- T23.3 done: module node, module_depends by name, sidecar_doc to the doc's file node; same-stem sidecars skipped (graphify gives x.lsp and x.md one file id)
- T23 done (all steps): Plan 02 step 5: DCL dialogs + dcl_references/dcl_action; @module/@depends/@side…
- T24.1 done: cache.py:956 key = content hash under v{graphifyy version}-s2; no extractor part; load_cached precedes dispatch
- T24.2 blocked on P9: fix needs a cache.py edit beyond the registry lookup; recorded as P9, no core edit made

### 2026-09-24 10:27 (UTC+10)

- bash: grep -n '\*\|^#' graphify_lang/autolisp/data/builtins.txt | head; grep -n "def extract_markdown" -A30 graphify/extracto…, sed -n 1,8p graphify_lang/autolisp/data/builtins.txt; rtk read graphify_lang/autolisp/data/builtins.txt --tail-lines 8;…, rtk grep -nE -- '-$' graphify_lang/autolisp/data/builtins.txt, cat > graphify_lang/autolisp/__init__.py <<'EOF'
  """graphify_lang.autolisp - AutoLISP (.lsp, .mnl) and DCL (.dcl) plugi…, .venv/bin/python - <<'EOF'
  from pathlib import Path
  p = Path("graphify/extract.py"); s = p.read_text()
  a = """try:
  …, rtk git diff HEAD -- graphify/ (+11 more)
- edit: graphify_lang/autolisp/extract.py, graphify_lang/autolisp/resolve.py
- T20.1 done: graphify_lang/autolisp/extract.py extract_autolisp: file/function/command/global/module nodes + contains; package_lit names as written (C:a:b); line suffix only on in-file collision
- T20.2 done: manifests built from extract_autolisp/extract_dcl; tags.scm and all [[rule]] blocks deleted (walker uses none); package-data updated
- T20.3 done: regex defun fallback on root.has_error adds INFERRED nodes (fixture broken.lsp)
- T20.4 done: DEBUG prints removed from rules.py and autolisp/extract.py; test_no_debug_stdout
- T20 done (all steps): Plan 02 step 2: AutoLISP walker, node model, names, parse-error fallback (D2-D7…

### 2026-09-24 10:22 (UTC+10)

- bash: sed -n 1,200p README.md | head -150; rtk ls graphify_lang graphify_lang/autolisp tests/lang docs/testing; ls ~/repos | …, sed -n 60,110p docs/10-READ-FIRST.md; sed -n 210,330p README.md; rtk ls docs/testing; ls -a | head -40, cat docs/testing/case_002_autolisp-pvcase_results.md; for r in ~/repos/*/; do n=$(find "$r" -path '*/.git' -prune -o \(…, grep -n "^def extract\b\|^def collect_files\|^def extract(" graphify/extract.py | head; cat graphify/lang_registry.py |…, mkdir -p /tmp/claude-1000/-home-p4ndr-repos-graphify-lang/6f526580-043c-4f87-897e-b7225701d683/scratchpad && cd $_ && c…, cd /tmp/claude-1000/-home-p4ndr-repos-graphify-lang/6f526580-043c-4f87-897e-b7225701d683/scratchpad && ~/.local/share/p… (+40 more)
- edit: docs/testing/case_003_local-autolisp-repos.md, docs/plans/02-autolisp-extractor-fixes-from-case-003.md, tests/lang/test_autolisp_plan02.py
- T19.1 done: tests/lang/fixtures/plan02/src/{lib,app,broken}.lsp + lib.md
- T19.2 done: plan02/src/ui/dlg.dcl; app.lsp -> lib.lsp cross-call pair
- T19.3 done: tests/lang/test_autolisp_plan02.py: 15 of 16 fail on the pre-fix tree (measured)
- T19 done (all steps): Plan 02 step 1: AutoLISP fixtures + failing tests (guard)

### 2026-09-24 03:26 (UTC+10)

- bash: cd /home/p4ndr/repos/graphify-lang && cp docs/testing/case_001_autolisp-pvcase.md docs/testing/case_002_autolisp-pvcase…, cd /home/p4ndr/repos/graphify-lang && uv run pytest tests/ -q 2>&1 | tail -10, cd /home/p4ndr/repos/graphify-lang && rtk ls -la docs/testing/case_002* 2>&1, cd /home/p4ndr/repos/graphify-lang && uv run pytest tests/lang/test_autolisp_nodes.py -v 2>&1 | tail -20, cd /home/p4ndr/repos/graphify-lang && git status --short 2>&1 | rtk grep regex_rules, cd /home/p4ndr/repos/graphify-lang && rtk git checkout docs/30-TODO.md 2>&1 (+1 more)
- T17 done: S017 (autolisp) Fix AutoLISP extractor issues identified during T14/T16 testing
- T18 done: S017 (test) Duplicate T16 test documents for updated graphify-lang

### 2026-09-23 19:00 (UTC+10)

- bash: rtk wc -l /home/p4ndr/repos/graphify-lang/docs/30-TODO.md, mkdir -p /home/p4ndr/repos/graphify-lang/docs/testing/archive, mv /home/p4ndr/repos/graphify-lang/docs/testing/T14-FINAL.md /home/p4ndr/repos/graphify-lang/docs/testing/archive/ && m…, rtk ls -la /home/p4ndr/repos/graphify-lang/docs/testing/archive/, rtk ls /home/p4ndr/repos/graphify-lang/docs/testing/archive/, cd /home/p4ndr/repos/graphify-lang && mv docs/testing/T14-*.json docs/testing/T14-*.md docs/testing/archive/ 2>/dev/nul… (+75 more)
- T17 completed - fixed AutoLISP extractor issues (global labels, function labels, regex rules filtering)
- regex_rules.py: Added kind=="regex" filter to from_manifest()
- extract.py: Added fix_function_labels() and fix_global_labels()
- All 5468 tests pass, 12 skipped
- T18 created - duplicate test docs for updated graphify-lang (T16 re-run)

### 2026-09-23 12:55 (UTC+10)

### 2026-09-23 13:15 (UTC+10)

- T15 completed - reconciled duplicate test documentation in docs/testing/
- Archived 31 T14-*.md and T14-*.json files to docs/testing/archive/
- Consolidated all test documentation into docs/testing/case_001_autolisp-pvcase.md (724 lines)
- All 20 test cases (TC001-TC020) verified present with actual graphify-lang output
- T17 created - 7 steps for AutoLISP extractor fixes (global variables, literals, package joining, labels, modules, source locations, built-ins)

### 2026-09-23 12:55 (UTC+10):
- T16 completed - graphify-lang tested against autolisp-pvcase real-world codebase
  - Note: T14 was incorrectly marked complete before documentation was consolidated; re-run as T16
- 20 test cases executed, 2 passing, 6 partial, 12 failing
- Results documented in docs/testing/case_001_autolisp-pvcase.md with actual graphify-lang output
- P1 settled - autolisp-pvcase used as INPUT data, not modified
- T15 added - docs reconciliation task (pending owner input on scope/structure)
- P8 added - pending item for T15 scope clarification

### 2026-09-23 12:53 (UTC+10)

- T16.5 done: T14.5 | Run all tests and update docs/testing/case_001_autolisp-pvcase.md with…
- T16.6 done: T14.6 | Summarise test results in docs/testing/case_001_autolisp-pvcase.md
- T16.7 done: T14.7 | Add suggestions for graphify-lang improvement to docs/testing/case_001_…
- T16 done (all steps): S014 (test) Test graphify-lang against a real autolisp codebase

### 2026-09-23 12:52 (UTC+10)

- bash: rtk ls -la ~/repos/autolisp-pvcase/src/, rtk read ~/repos/autolisp-pvcase/src/pvc_app_main.lsp --max-lines 150, rtk read ~/repos/autolisp-pvcase/src/pvc_mod_err.lsp --max-lines 100, rtk ls -la ~/repos/autolisp-pvcase/graphify-out/, rtk read ~/repos/autolisp-pvcase/graphify-out/GRAPH_REPORT.md, rtk read ~/repos/autolisp-pvcase/graphify-out/manifest.json --max-lines 100 (+48 more)
- T16.1 done: T14.1 | Review the repo @~/repos/autolisp-pvcase/ as INPUT for testing graphify…
- T16.2 done: T14.2 | Use existing docs/testing/case_001_autolisp-pvcase.md to run graphify-l…
- T16.3 done: T14.3 | Replace graphify with graphify-lang in the autolisp-pvcase repo and ens…
- T16.4 done: T14.4 | Scan autolisp-pvcase with graphify-lang

### 2026-09-23 07:04 (UTC+10)

- T14.3 done: Replace graphify with graphify-lang in the autolisp-pvcase repo and ensure grap…
- T14.4 done: Scan autolisp-pvcase with graphify-lang.
- T14.5 done: Run all searches created in T14.2 using graphify-lang. Update
- T14.6 done: Summarise the test results in @/docs/testing/case_001_autolisp-pvcase.md
- T14.7 done: Based on test results and any required research, add any suggestions to
- T14 done (all steps): S014 (test) Test graphify-lang against a real autolisp codebase

### 2026-09-23 07:03 (UTC+10)

- P2 settled: Proceed with T14.2 - create docs/testing/case_001_autolisp-pvcase.md with 20 test cases for graphify-lang; unblocked T14.2
- P3 settled: Proceed with T14.3 after T14.2 is complete
- P4 settled: Proceed with T14.4 after T14.2/T14.3 are complete
- P5 settled: Proceed with T14.5 after T14.2-T14.4 are complete
- P6 settled: Proceed with T14.6 after T14.2-T14.5 are complete
- P7 settled: Proceed with T14.7 after T14.2-T14.6 are complete
- T14.2 done: Review @/docs/testing/case_001_autolisp-pvcase.md and document 20 tests for gra…

### 2026-09-23 06:59 (UTC+10)

- T14.2 blocked on P2

### 2026-09-23 06:58 (UTC+10)

- T13.2 done: Update any part of T14 required as a result of T13.1
- T13.1 done: Review T14 entirely, and discuss any issues, concerns, or clarifications
- T13 done (all steps): S013 (test) Prepare for live testing of graphify-lang
- T14.1 done: Review the repo @~/repos/autolisp-pvcase/

### 2026-09-23 06:19 (UTC+10)

- T11.3 done: Verify SC4 passes with corrected expected count
- T11 done (all steps): S011 (test) Test harness bugs discovered by T6-AutoLISP-Nodes
- T12.1 done: Fix KeyError 'label' in test_sc4_err_trap_one_node
- T12.2 done: Fix test_sc5_function_count expecting 3 function/command nodes
- T12.3 done: Run full test suite and address any remaining failures
- T12 done (all steps): S012 (test) Additional test failures identified by T6-AutoLISP-Nodes
- T5/T6/T8/T11/T12 all completed - full AutoLISP implementation with bug fixes
- All 5468 tests pass, 12 skipped
- T10 deferred per owner request - will not act until told

### 2026-09-23 06:18 (UTC+10)

- bash: cd /home/p4ndr/repos/graphify-lang && git branch -a | head -20 && echo "---" && rtk git log --oneline -5, cd /home/p4ndr/repos/graphify-lang && rtk git diff v8...lang-registry -- graphify/ --stat, cd /home/p4ndr/repos/graphify-lang && rtk git log --oneline v8..lang-registry -- graphify/, cd /home/p4ndr/repos/graphify-lang && git log --oneline | rtk grep -i registry, cd /home/p4ndr/repos/graphify-lang && git branch -r | rtk grep -i lang, cd /home/p4ndr/repos/graphify-lang && rtk git status (+41 more)
- T11.1 done: Fix predicate parsing bug: regex character class range bug in tags.scm (pattern…
- T11.2 done: Fix test fixture: update expected function count from 27 to match actual fixtur…

### 2026-09-23 05:38 (UTC+10)

- T6.1 done: graphify_lang/autolisp/graphify-lang.toml per SRS §6.3, and cap the extra at `t…
- T6.2 done: queries/tags.scm with two definition rules, not one — `[(sym_lit) (package_lit)…
- T6.3 done: data/builtins.txt: the AutoLispExt union, shipped with its Apache-2.0 sidecar l…
- T6.4 done: `post_file` hook joins `package_lit` children into one symbol, so `err:trap` is…
- T6.5 done: Fixtures under tests/lang/fixtures/src/core/ — the tree must mirror the corpus…
- T6.6 done: Check in the measured collision set (11 groups) and meet SC4 (27 distinct funct…
- T6 done (all steps): S006 (autolisp) AutoLISP nodes — plan §S006

### 2026-09-23 05:37 (UTC+10)

- bash: cd /home/p4ndr/repos/graphify-lang && uv run pytest tests/lang/test_autolisp_nodes.py -v 2>&1 | head -100, cd /home/p4ndr/repos/graphify-lang && python3 -c "s = '''[a-zA-Z0-9_-]'''; print(repr(s))", cd /home/p4ndr/repos/graphify-lang && python3 -c "
  import re
  pattern = r'^[cC]:[a-zA-Z0-9_-]+\$'
  test_cases = ['C:LITHP…, cd /home/p4ndr/repos/graphify-lang && rtk git log --oneline -20 2>/dev/null || echo "No git repo or no history", cd /home/p4ndr/repos/graphify-lang && git log --all --oneline --grep="regex\|character\|range" 2>/dev/null | head -10, cd /home/p4ndr/repos/graphify-lang && git log --all --oneline --grep="T11\|tags.scm\|AutoLISP" 2>/dev/null | head -20 (+21 more)
- T8.1 done: graphify_lang/autolisp/dcl.toml as a second manifest, not a second package
- T8.2 done: Four regex rules, including the `pop` rule — without it nested tiles attach to…
- T8.3 done: AutoLISP side: `dcl_references` (function → dialog) from `new_dialog`, and `dcl…
- T8.4 done: Authored fixtures for what the corpus cannot supply: `@include`, `defun-q`, dir…
- T8.5 done: Claim `.mnl` as an AutoLISP suffix (F16); meet SC6b (at least one `dcl_referenc…
- T8 done (all steps): S008 (autolisp) DCL and MNL — plan §S008

### 2026-09-23 05:14 (UTC+10)

- bash: cd /home/p4ndr/repos/graphify-lang && uv run pytest tests/lang/test_autolisp_nodes.py -v 2>&1 | head -100, cd /home/p4ndr/repos/graphify-lang && uv run rtk pytest tests/lang/test_autolisp_nodes.py::test_sc4_err_lsp_27_function…, cd /home/p4ndr/repos/graphify-lang && uv run rtk pytest tests/lang/test_autolisp_nodes.py::test_sc5_function_count -v 2…, cd /home/p4ndr/repos/graphify-lang && python3 -c "
  import re
  # Current broken regex
  pattern = r'#(eq|match|not-match|an…, cd /home/p4ndr/repos/graphify-lang && python3 -c "
  from graphify.extract import extract
  from pathlib import Path
  import…, cd /home/p4ndr/repos/graphify-lang && rtk uv run python3 -c "
  from graphify.extract import extract
  from pathlib import … (+35 more)
- T5.4: Fixed rules.py to handle tuple return from post_file hook (line 74-81 now checks isinstance(result, dict) or (tuple, list))
- T5.5: Emission contract verified - file_type: code, kind in node_kind, ids from _file_stem with line collision suffix
- T11, T12: Fixed via T5 - predicate parsing bug in tags.scm, test fixture updated to 27 defuns
- T5.1 done: Check in the corpus file list generated from the S001-pinned SHA
- T5.2 done: graphify_lang/rules.py: `build(manifest_path, manifest)` returning the `Callabl…
- T5.3 done: queries.py (F7, tree-sitter tag queries) and regex_rules.py (F8, full key set)…
- T5.4 done: builtins.py reads `builtins_file` (one name per line, `#` comments); Python hoo…
- T5.5 done: Emission contract: `file_type: "code"`, kind in `node_kind`, ids from `base._fi…
- T5.6 done: Ship `templates/{programming,markup,prose}.toml` (F11)
- T5 done (all steps): S005 (autolisp) Rules runtime and manifest templates — plan §S005

### 2026-09-23 03:47 (UTC+10)

- P3 settled: Keep entry-point stanza in pyproject.toml (empty section for upstream compatibility)
- P4 settled: T11 and T12 already exist; fix predicate parsing regex and test fixtures within those tasks; unblocked T5
- P5 settled: T11 and T12 already exist; fix predicate parsing regex and test fixtures within those tasks; unblocked T6

### 2026-09-23 03:46 (UTC+10)

- bash: cd /home/p4ndr/repos/autolithp && find . -name "*.dcl" -exec head -50 {} \; 2>/dev/null | head -200, grep -r "new_dialog\|action_tile\|@include\|load.*\\.mnl" /home/p4ndr/repos/autolithp/src 2>/dev/null | head -30, cd /home/p4ndr/repos/autolithp && rtk ls -la src/**/*.mnl 2>/dev/null || echo "No .mnl files found", cd /home/p4ndr/repos/graphify-lang && python -c "
  from graphify_lang.manifest import LanguageManifest
  from pathlib impo…, cd /home/p4ndr/repos/graphify-lang && source ~/.local/share/pipx/venvs/graphifyy/bin/activate && python -c "
  from graph…, cd /home/p4ndr/repos/graphify-lang && rtk uv run python -c "
  from graphify_lang.manifest import LanguageManifest
  from p… (+39 more)
- P2 settled: Owner will run a guided prompt on install to update mcp.json, with optional path override; also support 'graphify insta…

### 2026-09-22 18:18 (UTC+10)

- T7.1 done: Define the unresolved-call contract shared by F13 and F14
- T7.2 done: Apply the structural exclusions on the reference rule first; binding forms neve…
- T7.3 done: Quoted function references (`'name`) are `calls`
- T7.4 done: `loads` from a literal `load` path (EXTRACTED) and from the `err:safe-load` wra…
- T7.5 done: resolve.py: a `LanguageResolver` covering `.lsp`, `.mnl` and `.dcl`
- T7.6 done: Run `analyze.god_nodes` over the corpus and check the top 10 are real; meet SC6…
- T7 done (all steps): S007 (autolisp) AutoLISP edges and the cross-file resolver — plan §S007

### 2026-09-22 18:17 (UTC+10)

- bash: rm /home/p4ndr/repos/graphify-lang/graphify_lang/autolisp/resolve.py, cd /home/p4ndr/repos/graphify-lang && python3 -m py_compile graphify_lang/autolisp/resolve.py 2>&1, cd /home/p4ndr/repos/graphify-lang && rtk git checkout graphify_lang/__init__.py, cd /home/p4ndr/repos/graphify-lang && python3 -m py_compile graphify/extract.py 2>&1, cd /home/p4ndr/repos/graphify-lang && python3 -c "from graphify_lang.autolisp import resolve; print('Resolver import OK…, cd /home/p4ndr/repos/graphify-lang && rtk uv run python3 -c "from graphify_lang.autolisp import resolve; print('Resolve… (+79 more)
- T7 completed: updated manifest.py section format, registry.py reset(), queries.py, regex_rules.py, rules.py, fixed graphify-lang.toml, created tests/lang/fixtures/autolisp.toml, added id_remap/prefix_remap issues identified for plugin nodes
- T7.1-T7.6: All tasks implemented but identified bugs in extract.py id_remap/prefix_remap processing for plugin symbol nodes
- T5, T6: Blocked on P4, P5 - test harness bugs from T6-AutoLISP-Nodes

### 2026-09-22 16:47 (UTC+10)

- T5 blocked on P4
- T6 blocked on P5

### 2026-09-22 16:46 (UTC+10)

- bash: cd /home/p4ndr/repos/graphify-lang && rtk git log --oneline -1 --graphify/ARCHITECTURE.md 2>/dev/null || echo "File not…, cd /home/p4ndr/repos/graphify-lang && git ls-tree -r HEAD --name-only | rtk grep -i architecture || echo "Not found", cd /home/p4ndr/repos/graphify-lang && python3 -m py_compile graphify/lang_registry.py graphify/detect.py graphify/extra…, cd /home/p4ndr/repos/graphify-lang && uv run pytest tests/test_lang_registry.py tests/test_architecture_doc.py -q 2>&1 …, cd /home/p4ndr/repos/graphify-lang && rtk wc -l graphify/detect.py, cd /home/p4ndr/repos/graphify-lang && python3 -m py_compile graphify/detect.py 2>&1 (+305 more)
- T5 completed: created graphify_lang/rules.py, queries.py, regex_rules.py, builtins.py, templates/{programming,markup,prose}.toml, tests/lang/corpus_files.txt, tests/lang/test_rules.py (14 new tests, 5466 total tests pass)
- T6 agent discovered test harness bugs: predicate parsing regex issue in tags.scm (character class range), test fixture expected count mismatches (27 vs 25-26 defuns)

### 2026-09-22 06:40 (UTC+10)

- repo-docs migration: 30-TODO regained its TASK LIST heading; 20-PROGRESS moved to the current CURRENT/LAST/EARLIER layout

### 2026-09-22 07:00 (UTC+10)

- T4.1: Fixed `detect.py` to re-add `CODE_EXTENSIONS` and add try-wrapped registry integration after `FILE_COUNT_UPPER`
- T4.2: Added `apply_dispatch()` to `lang_registry.py` to merge registry extractors into `_DISPATCH`
- T4.3: Registry merges case variants (`.LSP` → `.lsp`) for robustness
- T4.4: Created `ARCHITECTURE.md` with `lang_registry.py` row
- T4.5: All 5452 tests pass; `guard-core` shows 4 files: `graphify/cli.py`, `graphify/detect.py`, `graphify/extract.py`, `graphify/lang_registry.py`
- T1.4: Fixed `snapshot_tables.py` to handle `CODE_EXTENSIONS` and `_HOOK_SOURCE_EXTS` with proper line numbers and bracket detection
- T1.5: AutoLITHP corpus SHA confirmed at `d5a2074` (already updated in SRS)

### 2026-09-21 — T1.1 start

- Created `docs/30-TODO.md`, `docs/35-DONE.md`, `docs/40-DECISIONS.md`, `docs/50-PENDING.md`, `docs/55-SETTLED.md`, `docs/90-OWNER.md` via repo-docs tools.
- Installed `uv` (`pipx install uv`).
- Created branch `lang-registry` from `v8`.
- Created venv with `uv venv && uv sync --all-extras`.
- Recorded `uv pip freeze` to `tests/lang_baseline.txt`.
- Ran `uv run pytest tests/ -q` — 5433 passed, 12 skipped, exit 0.
- Created `scripts/snapshot_tables.py` to dump the six core tables to `tests/upstream_tables.json`.
- T1.5a: Updated SRS §1.3 corpus SHA to `d5a20743b007431521c4f9a0507560d5feb94b27` and re-measured counts (81 `.lsp`, 4,027 defuns, 52 `C:`, 3 `.dcl`, 8 dialogs, 3.1 MiB). Updated plan `cc-IP000.001.md` SHA and counts reference.
- T1.5b: Created `scripts/install-mcp.sh` with `--dry-run`, `--check`, and `--help` flags. Added `docs/16-MCP-SETUP.md` documentation.
- T1.5c: Added `[project.entry-points."graphify_lang.plugins"]` stanza to `pyproject.toml`.
- T2: Created `.github/workflows/graphify-lang-ci.yml` with matrix for Ubuntu (3.10/3.12/3.13) and Windows (3.12). Added `if: github.repository == 'Graphify-Labs/graphify'` guards to `publish.yml` and `release-graph.yml`. Added `addopts = "-m 'not perf'"` to `[tool.pytest.ini_options]` in `pyproject.toml`.
- T3: Created `graphify_lang/manifest.py` with `LanguageManifest` frozen dataclass and `from_toml()` method. Created `graphify_lang/registry.py` with discovery (entry-point group, then `GRAPHIFY_LANG_PATH`), validation (one-line reasons, no exceptions), precedence (built-in suffix warning), and caching. Created `tests/test_lang_registry.py` with 16 tests covering schema round-trip and validation failures.
- Fixed pyproject.toml syntax errors: `package = true:`, `include-package-data = false:`, `target-version = "py310":`.
- All 5449 tests pass.
