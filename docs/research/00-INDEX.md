<!-- TEMPLATE-VERSION: 2026-09-19-001 -->
<!-- DOC-TYPE: LIVE -->
<!-- TEMPLATE-START -->
# Research hub

This document is the LIVE hub for the research documents (spokes) of this repo.

- `§1` is the instructions. These apply to every document in `docs/research/`.
- `§2` is a list of CONDITIONS. Each sub-section is one CONDITION.
- `§3` is the list of spokes. A script writes it. Do not edit it by hand.

## 1. INSTRUCTIONS

- Put all research for this repo in `docs/research/`. NEVER put it in the repo root.
- One spoke covers one question or topic. Create each spoke with the script, not by hand:
  `pwsh -NoProfile -File ~/.claude/skills/repo-docs/scripts/repo-docs.ps1 new research "<title>"`.
- The first line under the H1 of a spoke is one sentence that says what the spoke answers. `§3` shows it.
- Every claim ends with its source URL and `[VERIFIED]` or `[UNVERIFIED]`.
- Keep raw material (fetched pages, notes) in a raw/ sub-folder. Spokes cite it.
- Read this hub first. Open only the spokes that you need.

## 2. CONDITIONS

When a CONDITION is TRUE, execute the tasks listed under that CONDITION.

### IF you add, rename, or delete a spoke, or change its first line:

-   Update `§3`: run the script with the verb `manifest`.

### IF a finding changes how the software is built or behaves:

-   Record it in `docs/40-DECISIONS.md` as a DECISION that names the spoke.
<!-- TEMPLATE-END -->

## 3. SPOKES

<!-- MANIFEST-START -->
| File | Title | Purpose | Type / Status |
|---|---|---|---|
| `01-prior-art-declaratively-defining-a-language-s-structure-and-extraction.md` | Prior art: declaratively defining a language's structure and extraction | Which existing systems let a language be defined in a config file rather than in code, and what the `graphify-lang` plugin manifest should … | FINAL |
| `02-upstream-state-relevant-to-a-plugin-registry-layer.md` | Upstream state relevant to a plugin/registry layer | What upstream (Graphify-Labs/graphify) already does about plugins and registries, and which of its tests constrain the fork's design. | FINAL |
| `03-autolisp-dcl-and-mnl-extraction.md` | AutoLISP, DCL and MNL extraction | What parsers, grammars, builtin lists and syntax references exist for AutoLISP, DCL and MNL, and which of them the extractor should use. | FINAL |
<!-- MANIFEST-END -->
