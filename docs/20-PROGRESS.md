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

### 2026-11-06 15:12 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 2 ops - done T45.1 (proof: plan 06 §5 table filled from tools/measure_autolisp.py --graph; all six criteria ticked); done T45.2 (hand-offs in scratchpad plan06-handoffs.md; PENDING P18 P19 P20)

### 2026-11-06 15:11 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 3 ops - pending_add P18; pending_add P19; pending_add P20

### 2026-11-06 15:09 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 3 ops - done T44.1, T44.2 (1f27cc08); done T44.3 (proof: tests/lang/test_plan06.py 17 pass; graphify lang list --check all ok); done (all steps) T44 (Plan 06 S5: global read/write edges and load/autoload edges)

### 2026-11-06 15:02 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 3 ops - done T43.1, T43.2 (18cc0910); done T43.3 (proof: graphify query "ust:bench-say callers" on the live ust graph prints the miss line and 'graph built at 1293e618, HEAD is ee649587 (44 commits)'); done (all steps) T43 (Plan 06 S4: query miss line and staleness line (CLI and MCP))

### 2026-11-06 14:58 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 2 ops - done T42.1 (d23c5e09); done T42.2 (proof: ust scratch rebuild has one ust:rget god node; get_neighbors ust:cfg-from-drawing resolves to src only); done (all steps) T42 (Plan 06 S3: query ranking, god_nodes and get_neighbors skip shadows)

### 2026-11-06 14:53 (UTC+10)

- edit: tests/lang/test_plan06.py
- batch: 3 ops - done T41.1 (748cb63e); done T41.2 (report _shadow_section, 748cb63e); done T41.3 (proof: tests/lang/test_plan06.py 7 pass; red with mark_shadows call or the pick drop removed); done (all steps) T41 (Plan 06 S2: shadow-copy pairing, shadow_of, pick_by_prefix drop, report section)

### 2026-11-06 14:44 (UTC+10)

- edit: docs/plans/06-autolisp-graph-quality-shadow-copies-freshness-inferred-calls-and-global-edges.md
- T40.1 done: --graph mode in tools/measure_autolisp.py (e06bf79f)
- T40.2 done: ust 55.9% INFERRED, 2364 dup labels, 0/222 globals used; htt 0% INFERRED, 30 dups, 0/1063 globals
- T40 done (all steps): Plan 06 S1: AutoLISP baseline numbers (INFERRED share, duplicate labels, unlink…

## 4. LAST SESSION

### 2026-09-26 20:08 (UTC+10)

- T38 done: Fixed a296fa7 (test-first 21a82f2): bmake, cc-kb, autolisp sidecar resolvers use _common.is_file_node (upstream _is_file_node_label); released v0.9.68+lang.5 (f2fd223), CI green, pipx installed, 3 graphs rebuilt unchanged; case_008 §6
- T38 done: E5 dupname parity cases (bmake watch+cli, cc-kb, autolisp sidecar) strict-xfail at 21a82f2, fixed at a296fa7 via _common.is_file_node; full suite 6309 passed/14 skipped/4 xfailed.
- Released v0.9.68+lang.5 (f2fd223, tag pushed to origin), CI incl. wheel green; pipx installed, lang list --check 0, MCP initialize ok; skill copy committed in ~/.claude (7230988).
- Real-corpus E5: BentleyHelp .mke depends_on and ~/.claude 48 cites now kept; remaining diffs are upstream stubs plus one pre-existing cc-kb reverse-edge extra (T39). BentleyHelp, claude-config, ~/.claude rebuilt: id-level identical (case_008 §6).
- autolisp not an ancestor of rr-fix: left untouched; README release recipe names rr-fix.

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

## 5. EARLIER SESSIONS
