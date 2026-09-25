# AutoLISP, DCL and MNL extraction

What parsers, grammars, builtin lists and syntax references exist for AutoLISP, DCL and MNL, and which of them the extractor should use.

- Status: FINAL
- Created: 2026-09-21
- Full document: `.claude/docs/cc-RF010.003.md` (702 lines, 8 sections; ~60 source URLs in its §8)

## 1. Question

Which AutoLISP/DCL/MNL parsing assets can be reused, under which licences, and what constructs change symbol extraction beyond the table in `README.md`?

## 2. Findings

Corpus: `~/repos/autolithp`, measured 2026-09-08, excluding `.claude/worktrees/`. [VERIFIED]

| Asset | Licence | Use |
|---|---|---|
| `shioshosho/tree-sitter-autolisp` | MIT declared in manifests, **no LICENSE file** | the only tree-sitter AutoLISP grammar; its `function_definition{name, parameter_list, docstring, body}` maps 1:1 onto the target node model. Licence must be cleared first. [UNVERIFIED — licence] |
| `tree-sitter-commonlisp` | already a dependency | parses `err.lsp` with zero `ERROR` nodes, but `package_lit` mis-reads `err:` |
| `autolithp/tools/lread.py` | the user's own | 72-line s-expression reader with line numbers; the fallback if the grammar licence fails. Needs `;\| … \|;` block comments and dotted pairs |
| Autodesk `AutoLispExt` data files | **Apache-2.0** | builtin lists: 3 `vla-`/`vlax-`/`vlr-` prefixes, ~487 core names, 111 `functions`-only names, 1,738 AutoCAD commands, 114 DCL keys |
| `ten0s/velisp` | GPL-3.0-or-later | read-only: `grammar/VeDcl.g4` and `test/dcl/*.dcl` as a DCL conformance checklist |

DCL has no grammar to reuse and only 5 token classes → a hand-written reader of ~120 lines. [VERIFIED]

Constructs beyond the `README.md` table (full document §5): `defun-q` and `defun-q-list-ref`/`-set`, `autoload`, `load` with `onfailure`, `S::STARTUP`, VLX namespace functions, the blackboard (`vl-bb-set`/`vl-bb-ref`), reactors, and `@include` / `base.dcl` in DCL.

## 3. Implications for this repo

1. Extractor plan: vendored or re-derived AutoLISP grammar first, `lread.py` as fallback, hand reader for DCL — recorded as D-006.
2. The builtins denylist ships as package data with an `Apache-2.0` sidecar licence file.
3. Four behaviours have zero corpus instances (`defun-q`, direct `(load "x")`, DCL `@include`, `.mnl`) and need authored fixtures.
4. Every corpus claim must exclude `~/repos/autolithp/.claude/worktrees/`.

## 4. Sources

~60 URLs (repositories with licences, and the AutoCAD 2026 ENU AutoLISP/DCL/Customization reference) are listed in `.claude/docs/cc-RF010.003.md` §8, all fetched 2026-09-08.
