<!-- TEMPLATE-VERSION: 2026-09-19-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# Plans hub

This document is the LIVE hub for the plans, designs, and specifications of this repo.

- `§1` is the instructions. These apply to every document in `docs/plans/`.
- `§2` is a list of CONDITIONS. Each sub-section is one CONDITION.
- `§3` is the list of plans. A script writes it. Do not edit it by hand.

## 1. INSTRUCTIONS

- Put all plans, designs, and specifications for this repo in `docs/plans/`. NEVER put them in the repo root.
- Create each plan with the script, not by hand:
  `pwsh -NoProfile -File ~/.claude/skills/repo-docs/scripts/repo-docs.ps1 new plan "<title>"`.
- The first line under the H1 of a plan is one sentence that says what the plan delivers. `§3` shows it.
- Each plan has one status line: `- Status: DRAFT`, `ACTIVE`, `DONE`, or `SUPERSEDED`. `§3` shows it.
- A plan says what and why. `docs/30-TODO.md` tracks the work. An ACTIVE plan names its TASK numbers.
- NEVER delete a plan. Mark it DONE, or SUPERSEDED with the name of the plan that replaces it.

## 2. CONDITIONS

When a CONDITION is TRUE, execute the tasks listed under that CONDITION.

### IF you add or rename a plan, change its first line, or change its status:

-   Update `§3`: run the script with the verb `manifest`.

### IF a plan becomes ACTIVE:

-   Add its TASKS to `docs/30-TODO.md`, and write their numbers in the plan.
<!-- TEMPLATE-END -->

## 3. PLANS

<!-- MANIFEST-START -->
| File | Title | Purpose | Type / Status |
|---|---|---|---|
| `01-language-extension-layer-and-autolisp-plugin.md` | Language-extension layer and AutoLISP plugin | A registry that lets a language be registered from outside `graphify/extract.py`, plus an AutoLISP/DCL plugin built on it. | ACTIVE |
| `02-autolisp-extractor-fixes-from-case-003.md` | AutoLISP extractor fixes from case 003 | Fix defects D1-D12 from `docs/testing/case_003_local-autolisp-repos.md` and add the edges agreed on 2026-09-24, so that an AutoLISP repo gi… | DONE |
| `03-replace-stock-graphify-with-the-fork.md` | Replace stock graphify with the fork | Replace the pipx `graphifyy 0.9.55` install with a pinned build of this fork, rebased on `upstream/v8`, and rebuild the graph of every grap… | DONE |
| `04-content-sniffing-augment-plugins-and-five-new-languages.md` | Content sniffing, augment plugins, and five new languages | A content-sniff router for suffixes that two languages share, an `augment` manifest kind that adds to a built-in extractor's output, and pl… | DONE |
| `05-review-remediation-cc-cr000-001.md` | Review remediation (cc-CR000.001) | A six-stage fix of all 35 defects (4 High, 12 Medium, 13 Low, 6 Nit) and the 9 enhancements in `.claude/docs/cc-CR000.001.md`, released as … | ACTIVE |
| `05-S001-security-and-crash-safety.md` | Plan 05 S001: security and crash safety | Stage 1 of plan 05 (hub `05-review-remediation-cc-cr000-001.md`): no input file can hang a build, crash it, or make a whole file vanish fro… | ACTIVE |
| `05-S002-repo-and-ci-hygiene.md` | Plan 05 S002: repo and CI hygiene | Stage 2 of plan 05: the workflows parse, CI runs on the fork's release branches and tags, and the repo holds no junk. | DONE |
| `05-S003-shared-plugin-core.md` | Plan 05 S003: shared plugin core | Stage 3 of plan 05: one shared module carries the id, sink and resolver contracts that the five plugins now copy, so H2 and M4 are fixed in… | DONE |
| `05-S004-build-coherence.md` | Plan 05 S004: build coherence | Stage 4 of plan 05: an incremental build, a cached build and a clean build give the same graph. | DONE |
| `05-S005-registry-robustness.md` | Plan 05 S005: registry robustness | Stage 5 of plan 05: one bad plugin cannot take down the others, plugin files trigger every rebuild path, and the registry has one clear loa… | DONE |
| `05-S006-tests-docs-and-release.md` | Plan 05 S006: tests, docs and release | Stage 6 of plan 05: the test suite shows what CI really covers, the docs describe the fork as it is, the upstream PR drafts exist, and `v0.… | ACTIVE |
<!-- MANIFEST-END -->
