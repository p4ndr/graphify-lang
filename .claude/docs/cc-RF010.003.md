# AutoLISP / DCL / MNL extractor research — graphify-lang

> **Date**: 2026-09-08
> **For**: `graphify-lang` fork (`/home/p4ndr/repos/graphify-lang`), AutoLISP language extension
> **Corpus**: `/home/p4ndr/repos/autolithp`
> **Local KB reused**: `cc-AR760.000.md` (AutoLISP/Visual LISP hub, §DCL dialog patterns AR760.005,
> §OpenDCL AR760.006), `cc-DB760.001.md` (failure-path cleanup recipe),
> `/home/p4ndr/repos/autolithp/.claude/docs/cc-RF760.001.md` (ecosystem survey §1 libraries/tools),
> `cc-AR710.*`/`cc-AR720.*`/`cc-AR730.*` (AutoCAD general/.NET/ObjectARX — not load-bearing here).
> All web claims below were fetched 2026-09-08 unless noted.

---

## 0. Corrections to the brief (measured)

The brief states the corpus is "480 `.lsp`, 18 `.dcl`". Measured:

```
find /home/p4ndr/repos/autolithp -name '*.lsp' | wc -l      -> 480
find /home/p4ndr/repos/autolithp/src -name '*.lsp' | wc -l  ->  36
```

**444 of the 480 are copies inside `/home/p4ndr/repos/autolithp/.claude/worktrees/`** (agent
worktrees, each a near-complete clone; `pltrn.lsp` alone appears 5+ times at ~1 MB each).
Any extractor measurement or acceptance test that globs `**/*.lsp` will inflate counts ~13x
and produce duplicate function nodes. The real source tree is `src/` (36 files).

Verification of the README acceptance number, on the real tree:

```
grep -ocE '\(defun ' /home/p4ndr/repos/autolithp/src/core/err.lsp   -> 27   ✅ matches README
```

Frequencies over `src/**/*.lsp` (36 files) vs whole tree (480 files):

| Construct | `src/` | whole tree |
|:----------|------:|-----------:|
| `(defun ` | 2530 | 14871 |
| `(defun-q` | 0 | 0 |
| `(lambda` | 169 | 1017 |
| `(defun C:` | 44 | 248 |
| `(vl-catch-all-apply` | 292 | 1916 |
| `*error*` | 241 | 1236 |
| `(action_tile` | 21 | 88 |
| `(load_dialog` | 5 | 48 |
| `(new_dialog` | 5 | 43 |
| `(eval ` | 17 | 138 |
| `(read ` | 14 | 108 |
| `(autoload ` | 0 | 0 |
| `(vlax-import-type-library` | 0 | 0 |
| `(vl-doc-export` / `(vl-bb-set` | 0 | 0 |
| distinct `vla-`/`vlax-` head symbols | — | 66 |
| `'symbol` quoted refs | — | 16691 |
| `.mnl` / `.cuix` / `.mnu` files | 0 | 0 |

Header-tag census (whole tree):
`@doc` 2304, `@module` 138, `@version` 138, `@prefix` 138, `@depends` 138, `@description` 138,
`@sidecar` 62, `@tags` 6, `@return` 6.

**Consequence for the roadmap**: `defun-q`, `autoload`, `vlax-import-type-library`,
`vl-doc-export`, `vl-bb-set` and `.mnl` have **zero** occurrences in this corpus. They are
correctness/robustness concerns, not measurable acceptance criteria. Ship them as
"parse without crashing / low-confidence edge", not as phase gates.

---

## 1. Existing AutoLISP parsers, grammars and tooling

### 1.1 `shioshosho/tree-sitter-autolisp` — the only tree-sitter AutoLISP grammar that exists

- URL: <https://github.com/shioshosho/tree-sitter-autolisp>
- GitHub search `tree-sitter-autolisp` → `total_count: 1`. `tree-sitter dcl` → 0.
  There is **no** tree-sitter DCL grammar anywhere.
- Stars 0, pushed 2026-02-17, 23 KB, 19 files, README in Japanese.
- **Licence: ambiguous.** `package.json` says `"license": "MIT"` and `tree-sitter.json`
  `metadata.license: "MIT"`, but **there is no `LICENSE` file** and the GitHub API returns
  `license: null`. Reusing it means either asking the author to add a LICENSE, or treating
  the declared MIT in the manifests as sufficient (weak). Flag this before vendoring.
- **No language bindings shipped.** File list is: `grammar.js`, `src/grammar.json`,
  `src/node-types.json`, `src/parser.c`, `src/tree_sitter/*.h`, `queries/{highlights,locals,context}.scm`,
  `test/corpus/{comments,defun,expressions,literals}.txt`. `package.json` declares
  `"main": "bindings/node"` but `bindings/` does not exist. **No `bindings/python`, no
  `pyproject.toml`, no PyPI package, no wheels.** Using it from Python means vendoring
  `src/parser.c` and compiling it yourself.
- `tree-sitter.json` `file-types: ["lsp", "mnl"]` (package.json also lists `fas`, which is a
  compiled binary and is wrong).

Grammar shape (verbatim from `grammar.js`):

| Node | Fields | Notes |
|:-----|:-------|:------|
| `source_file` | `repeat(_sexp)` | |
| `function_definition` | `name`, `parameter_list`, `docstring`, `body*` | covers **both** `defun` and `defun-q` (aliased `defun_keyword` / `defun_q_keyword`) |
| `lambda` | `parameter_list`, `body*` | |
| `parameter_list` | `parameter*`, `/`, `local*` | **the `/ locals` split is a first-class field** |
| `list` / `dotted_pair` / `quote` | `car`,`cdr` / — | `'sexp` is a `quote` node |
| `integer`, `real`, `string`, `nil`, `t_literal`, `symbol` | | |
| `line_comment` | `; …` | |
| `block_comment` | `;\| … \|;` | |

Two properties that matter for this fork:

1. **Case-insensitivity is handled correctly**: keywords are built by a `kw()` helper that
   expands each letter to `[dD]`-style character classes, so `DEFUN`/`defun`/`Defun` all parse.
2. **`err:trap` is one symbol.** The symbol rule is
   `token(prec(-1, /[a-zA-Z_*+\-=<>&~^\/][a-zA-Z0-9_\-*+:$!?.=<>&~^\/]*/))` — `:` is in the
   *continuation* class, so `err:trap`, `C:LITHP` and `*err:debug*` each lex as a single
   `symbol`. This is exactly what `tree-sitter-commonlisp` gets wrong (it reads the prefix as
   `package_lit`), and it is the single strongest argument for this grammar over the
   Common Lisp one.

Gaps: no DCL. No `#` reader syntax (AutoLISP has none, so fine). `parameter_list` does not
model the `defun (a b / c d)` case where `/` is glued to a name without spaces — AutoLISP
requires whitespace around `/`, so acceptable.

### 1.2 `shioshosho/autolisp-lsp` — a Rust LSP with a symbol table

- URL: <https://github.com/shioshosho/autolisp-lsp>
- **Licence: none** (no LICENSE file, API `license: null`). Not reusable as code.
- Rust; hand-written lexer/parser (`src/parser/{lexer,token,ast,parser}.rs`), not tree-sitter.
- `src/analysis/symbol_table.rs`, `src/features/document_symbol.rs`,
  `src/features/definition.rs` (cross-file go-to-definition) — i.e. a real cross-file symbol index.
- `src/builtins.rs`, 3505 lines, `BuiltinFunction { name, signature, description, params,
  return_type, category }` with 8 categories (Math/String/List/Entity/SelectionSet/Conversion/
  FileIO/Display). ~2100 quoted strings. **Not a licensed source for a name list.**
- Useful only as a design reference (its `by_prefix` lookup, its category split).

### 1.3 `Autodesk-AutoCAD/AutoLispExt` — the VS Code extension. **This is the reusable asset.**

- URL: <https://github.com/Autodesk-AutoCAD/AutoLispExt>
- **Licence: Apache-2.0** (`LICENSE.md` is the verbatim Apache 2.0 text; GitHub API
  `spdx_id: "Apache-2.0"`). `NOTICE.md` (34 KB) is third-party attribution for npm deps
  (execa, fs-extra, vscode-vsce, …) — it is not a restriction on the repo's own data files.
- 145 stars, 38 forks, actively maintained (pushed 2026-05-27), 728 files (322 excluding i18n).
- Written in TypeScript; `language: "Common Lisp"` is GitHub's mis-detection of the test corpus.

What it contains, by area:

| Area | Files |
|:-----|:------|
| Tokeniser / AST (LISP) | `src/parsing/lispParser.ts`, `src/parsing/comments.ts`, `src/parsing/containers.ts`, `src/astObjects/{lispAtom,lispContainer,sexpression,ILispFragment}.ts` |
| Tokeniser / AST (DCL) | `src/parsing/dclParser.ts` (7.8 KB), `src/astObjects/{dclAtom,dclAttribute,dclTile,dclInterfaces}.ts` |
| Symbol / outline index | `src/symbols.ts` (`SymbolManager`, per-document `RootSymbolMapHost` cache), `src/services/symbolServices.ts`, `src/services/flatContainerServices.ts` |
| Navigation | `src/providers/{gotoProvider,referenceProvider,renameProvider,hoverProvider}.ts` |
| Grammars (TextMate) | `syntaxes/autolisp.tmLanguage.json` (73 KB), `syntaxes/autolispdcl.tmLanguage.json` (2.3 KB) |
| **Builtin data files** | `data/alllispkeys.txt`, `data/alldclkeys.txt`, `data/winonlylispkeys_prefix.txt`, `data/cmdAndVarsList.txt` |
| **Structured help index** | `src/help/webHelpAbstraction.json` (2.86 MB) |
| Project files | `src/project/*` (`.prj` project format, ripgrep-backed find/replace) |
| Formatter | `src/format/{autoIndent,listreader,formatter}.ts` |

`dclParser.ts` is a hand-written character-scanner (not a grammar). It tokenises on
`{ } ; : = "` plus `//` and `/* */` comments, builds `DclTile` containers and `DclAttribute`
leaves, and has the special rule that *"when there is only 2 atoms and the last one is the
semi-colon"* and the first atom is a known tile name, it is a **default (alias) tile** —
i.e. `ok_cancel;`. **It has no `@include` handling** (`grep -n include dclParser.ts` → nothing).

`src/help/userDocumentation.ts` is the source of the only Autodesk-published doc-comment
convention — see §6.

### 1.4 `ten0s/velisp` — an AutoLISP interpreter with a real ANTLR DCL grammar

- URL: <https://github.com/ten0s/velisp>, 23 stars, **GPL-3.0-or-later**, pushed 2025-07-12.
- `grammar/VeDcl.g4` and `grammar/VeLisp.g4` are complete ANTLR4 grammars. Also ships
  `lib/dcl/base.dcl`, `lib/dcl/acad.dcl`, `DCL-Functions.md`, and ~40 `.dcl` test fixtures
  under `test/dcl/` with paired `.lsp` drivers.
- **GPL-3.0 makes the grammar text unusable as copied source in a permissively-licensed
  fork.** It is however the single best *specification* of DCL to read and re-implement
  independently, and the `test/dcl/*.dcl` corpus is an excellent (read-only) validation set
  for a fixture suite written from scratch.

### 1.5 Everything else surveyed (no symbol index)

From GitHub `topic:autolisp` and `cc-RF760.001.md` §1:

| Repo / source | Licence | What it is | Symbol index? |
|:--------------|:--------|:-----------|:--------------|
| `manualChair/commonlib` | MIT | function library for separate-namespace VLX | no |
| `manualChair/include` | MIT | `load` wrapper that tracks loaded files | no |
| `Jciel/cathedral` | MIT | function collection | no |
| `caadxyz/caad4lisp` | MIT | library | no |
| `sdfaheemuddin/autolisp-outline-extension` | MIT | VS Code outline of commands/functions (regex-level) | trivial regex only |
| `Xiao15888/LCAD-AutoCAD-AutoLISP-Extension` | none | fork of AutoLispExt | inherited |
| `JacobHyde/AutoLISP-Parser` | CC0-1.0 | "parser and structure analysis", last pushed 2014-03-28 | dead |
| Lee Mac (<https://www.lee-mac.com/programs.html>) | proprietary/free-to-use | 100+ end-user programs | **no parser, no index** |
| XDrx-API (<https://github.com/xdcad/XDrx-API>) | free, non-commercial | ObjectARX function library | no |
| AfraLISP, TheSwamp, CADTutor, JTB World | — | tutorials/forums | no |
| LispDe | — | no active open-source project found | — |

**Conclusion for §1**: exactly one tree-sitter AutoLISP grammar exists (licence-ambiguous,
no Python bindings, no DCL); one Apache-2.0 Autodesk-owned data trove exists and is the
right thing to reuse; one GPL ANTLR DCL grammar exists and should be read, not copied.

---

## 2. Builtin function name list — source, count, licence

### 2.1 Autodesk's own reference (the citable spec, but not machine-readable)

- Index: **Functions Reference (AutoLISP)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-4CEE5072-8817-4920-8A2D-7060F5E16547.htm>
- Organised as 23 A–Z pages (no J, K, Y), plus a **Non-alphabetic Functions Reference**
  (<…/GUID-EBDC1072-48BF-4204-80B1-73430DBF58E1.htm>) and an "External" page, plus
  feature-category pages (Application-Handling, Arithmetic, Error-Handling, Function-Handling,
  List Manipulation, String-Handling, Symbol-Handling, Data Conversion, Device Access,
  Display Control, File-Handling, Geometric, Query and Command, User Input, Memory Management,
  Windows Registry, Extended Data-Handling, Object-Handling, Selection Set Manipulation,
  Symbol Table and Dictionary-Handling, **the five DCL groups**, ActiveX Library, Express Tools).
- **The index states no total count.** Scraping 23+ pages is the only way to derive one.

DCL-relevant sub-indexes (all fetched):

- Dialog Box Opening and Closing —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-A96C28B5-4B9A-4EE8-8C46-808F14217777.htm>
  → `done_dialog` "Terminates a dialog box"; `load_dialog` "Loads a DCL file";
  `new_dialog` "Begins a new dialog box and displays it, and can also specify a default action";
  `start_dialog` "Displays a dialog box and begins accepting user input";
  `term_dialog` "Terminates all current dialog boxes as if the user had canceled each of them";
  `unload_dialog` "Unloads a DCL file".
- Tile- and Attribute-Handling —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-B254FD2A-669A-4A16-9816-AAC79E983571.htm>
  → `action_tile` "Assigns an action to evaluate when the user selects the specified tile in a
  dialog box"; `get_attr` "Retrieves the DCL value of a dialog box attribute";
  `get_tile` "Retrieves the current runtime value of a dialog box tile";
  `mode_tile` "Sets the mode of a dialog box tile"; `set_tile` "Sets the value of a dialog box tile".
- Plus (from `alllispkeys.txt`, all present): `start_list`, `add_list`, `end_list`,
  `start_image`, `vector_image`, `fill_image`, `slide_image`, `end_image`,
  `dimx_tile`, `dimy_tile`, `client_data_tile`. **22 DCL functions in total.**
- Non-alphabetic page confirms `*error*`, `*push-error-using-command*`,
  `*push-error-using-stack*`, `*pop-error-mode*`, and the operators `+ - * / = /= > >= < <= ~ 1+ 1-`.
- VLX Namespace Functions Reference —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-5784FC6F-82DD-4459-879B-6EC3BD5E88D1.htm>
  → `vl-arx-import`, `vl-doc-export`, `vl-doc-import`, `vl-doc-ref`, `vl-doc-set`,
  `vl-exit-with-error`, `vl-exit-with-value`, `vl-list-exported-functions`,
  `vl-list-loaded-vlx`, `vl-unload-vlx`, `vl-vlx-loaded-p` (11).

### 2.2 The shippable machine-readable list: AutoLispExt (Apache-2.0)

**Option A — flat name list.** `extension/data/alllispkeys.txt`
(<https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/data/alllispkeys.txt>),
54 226 bytes, one name per line.

```
2731 lines, 2730 unique names
  vla-get-   851
  vla-put-   693
  vla-       510   (methods)
  vlax-       69
  vl-         61
  acet-       54   (Express Tools)
  vlr-        46
  vlisp-      20
  c:           2
  other      425   (core AutoLISP + DCL + :keyword constants + Acet: constants)
487 names do NOT start with vla-/vlax-/vlr-/vlisp-/acet-  ← the "core" denylist
```

Includes `defun`, `defun-q`, `*error*`, all 22 DCL functions, `:vlax-true`, `:tlb-filename`,
`:vlr-*` reactor event keywords, `Acet:IDOK`-style constants.

**Option B — structured index (better).** `extension/src/help/webHelpAbstraction.json`
(<https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/src/help/webHelpAbstraction.json>),
2 857 069 bytes. Top-level:

| Key | Count | Contents |
|:----|------:|:---------|
| `year` | — | `"2021"` (the help release it was generated from) |
| `functions` | **2565** | `{signature, arguments[{id,typeNames,primitive,enums}], returnType, validObjects, id, category, guid, description, platforms}` |
| `ambiguousFunctions` | 27 | overloads (`vlax-3d-point`, `function`, `vla-add`, …) |
| `objects` | 156 | ActiveX objects with `methods[]` / `properties[]` |
| `enumerators` | 894 | `acAttachmentPointTopLeft`-style constants |
| `dclTiles` | 31 | per-tile `signature` + allowed `attributes[]` + `description` |
| `dclAttributes` | 35 | per-attribute `signature`, `valueType`, `description` |
| `events` | 41 | ActiveX events |

`functions` prefix breakdown: `vla-get-` 879, `vla-put-` 712, `vla-` 490, core/other 258,
`vl-` 70, `vlax-` 63, `acet-` 49, `vlr-` 43, `vlisp-` 1.

Set arithmetic between the two: 276 names in `alllispkeys.txt` are absent from
`functions` (mostly `:keyword` constants and `Acet:` constants, which are not functions);
111 names in `functions` are absent from `alllispkeys.txt` (`layerstate-*`,
`defun-q-list-ref/set`, `acad_colordlg`, `initdia`, `cal`, `3dsin`, `autoarxload`, …).
**Union ≈ 2841 names.** Ship the union.

**Option C — prefix denylist (cheapest, and the one to start with).**
`extension/data/winonlylispkeys_prefix.txt` is 5 lines, verbatim:

```
vla-
vlax-
vlr-
vl-load-com
vl-load-reactors
```

That single file collapses **2189 of the 2730 names (80%)** into 3 prefix tests. Combined with
the 487-name core list, it is a complete denylist in ~10 KB. The AutoLITHP corpus contains
only **66 distinct** `vla-`/`vlax-` head symbols, so the prefix rule alone kills the god-node
risk the README flags for `_LANGUAGE_BUILTIN_GLOBALS`.

Other data files: `alldclkeys.txt` (114 lines — tile types + attributes + colour words +
alignment words, flat and unstructured, one malformed line `dialog|dialog_background`);
`cmdAndVarsList.txt` (1738 lines — AutoCAD command and sysvar names, useful for the
`command_invokes` relation's stub nodes).

### 2.3 Licence position for shipping a name list

- The files are inside an **Apache-2.0** repository owned by Autodesk. Apache-2.0 §4 grants
  redistribution of the Work and Derivative Works in source or object form, provided you
  (a) include a copy of the licence, (b) carry a "changed files" notice, (c) retain
  attribution notices from the source, and (d) if the Work has a NOTICE file, include its
  attribution portions. `AutoLispExt/NOTICE.md` is npm third-party attribution and does not
  concern the data files, but the safe act is to carry it too.
- Practical recipe for the fork: put the derived list in e.g.
  `graphify_lang/autolisp/data/builtins.txt`, and next to it a `LICENSE.AutoLispExt` holding
  the Apache-2.0 text plus a line naming the upstream file, commit SHA, and the transformation
  applied ("lowercased, sorted, de-duplicated, union of `alllispkeys.txt` and the `functions`
  keys of `webHelpAbstraction.json`"). No copyleft, no share-alike, compatible with MIT/Apache
  hosting.
- Independent point: a bare list of API function *names* is a set of facts about a public API
  and is very weak subject matter for copyright in the first place (US: *Feist*; the list has
  no original selection/arrangement beyond alphabetical). The Apache grant makes the question
  moot — take the grant, keep the attribution, do not rely on the fact/idea argument alone.
- **Do not** take names from `shioshosho/autolisp-lsp` (`src/builtins.rs`) or from
  `ten0s/velisp` — the former has no licence at all, the latter is GPL-3.0.

---

## 3. DCL syntax reference

### 3.1 The grammar (independently corroborated: Autodesk prose + velisp `.g4` + AutoLispExt parser)

Autodesk sources:

- **About Syntax and Comments in DCL Files** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-1A629E01-828D-402E-965F-DE76F1BF28AD.htm>
  → *"A statement preceded by two forward slashes ( // ) is treated as a comment in a DCL file."*
  and *"DCL also allows C language style comments. These have the form /\* comment text \*/"*.
- **About Tile References (DCL)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-709DE551-4888-4FD6-8C0E-EAB6BA2C1B3A.htm>
  → *"Tile references have one of the following syntaxes in a DCL file: `name;` or
  `: name { attribute = value; . . . }`"* and *"The format of the second instance can refer only
  to prototypes, not to subassemblies. … The `ok_cancel` tile defined in `base.dcl` is a
  subassembly, so it too can be referenced only by name."*
- **About Referencing DCL Files (DCL)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-79DEC649-2DA1-4871-8C22-2C5B7DD287A7.htm>
  → `@include "filename"` (example `@include "usercore.dcl"`). Search order: *"the current
  directory first, then the directory containing the include directive itself"*; a full path
  restricts the search to that directory. *"All DCL files can use the tiles defined in the
  `base.dcl` file."* You **cannot** `@include` `acad.dcl` (or `acadlt.dcl`); definitions must
  be copied instead.
- **About Dialog Box Components (DCL)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-E10AFB89-89BF-4616-819A-439BAEAAD0B9.htm>
  → *"The basic tile types are predefined by the programmable dialog box (PDB) facility"*;
  subassemblies (OK/Cancel/Help groups) *"are treated as single tiles."*
- **Predefined Attributes for Tiles Reference (DCL)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-5B0C8B10-F968-4A56-B4A5-6A26935B341A.htm>
  → `key`: *"Specifies a name that the program uses to refer to this specific tile."*
  `action`: *"Specifies an AutoLISP expression to perform an action when this tile is selected.
  Also known as a callback."*
- **About Semantic Auditing of DCL Files (DCL)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-44C84FB7-5E87-46E9-9E14-24C157A87179.htm>

`ten0s/velisp` `grammar/VeDcl.g4` (GPL-3.0 — **read as a spec, do not copy**), reproduced here
in paraphrase for the extractor spec:

```
file        : (includeFile | defineTile)*
includeFile : '@include' STR ';'?
defineTile  : ID ':' clusterTile '{' entry* '}' ';'?      // named cluster
            | ID ':' simpleTile  '{' attribute* '}' ';'?  // named simple / prototype
innerTile   :     ':' clusterTile '{' entry* '}' ';'?     // anonymous child
            |     ':' simpleTile  '{' attribute* '}' ';'?
            |     ':' ID          '{' attribute* '}' ';'? // derive from a prototype
            |         ID ';'                              // alias, e.g.  ok_cancel;
entry       : attribute | innerTile
attribute   : ID '=' (BOOL|INT|REAL|STR|ALIGN|LAYOUT) ';'
COMMENT     : '/*' .*? '*/'      LINE_COMMENT : '//' .*? NEWLINE
ID          : LETTER (LETTER|DIGIT|'_')*
ALIGN       : left|right|top|bottom|centered|filled     LAYOUT : horizontal|vertical
```

Cluster tiles (11): `dialog row column boxed_row boxed_column concatenation paragraph
radio_row radio_column boxed_radio_row boxed_radio_column`.
Simple tiles (12): `button edit_box image image_button list_box popup_list radio_button
slider spacer text text_part toggle`.

Autodesk's own tile inventory, from `webHelpAbstraction.json.dclTiles` (**31**), adds the
predefined subassemblies and spacer variants:
`boxed_column boxed_radio_column boxed_radio_row boxed_row button column concatenation dialog
edit_box errtile image image_button list_box ok_cancel ok_cancel_help ok_cancel_help_errtile
ok_cancel_help_info ok_only paragraph popup_list radio_button radio_column radio_row row
slider spacer spacer_0 spacer_1 text text_part toggle`.

`webHelpAbstraction.json.dclAttributes` (**35**):
`action alignment allow_accept aspect_ratio big_increment children_alignment
children_fixed_height children_fixed_width color edit_limit edit_width fixed_height fixed_width
fixed_width_font height initial_focus is_bold is_cancel is_default is_enabled is_tab_stop key
label layout list max_value min_value mnemonic multiple_select password_char small_increment
tab_truncate tabs value width`. Each carries a `signature` (e.g. `action = "(function)";`)
and a `valueType.primitive`.

`alldclkeys.txt` (114 lines) is the same material flattened and polluted with colour words
(`red`, `blue`, `dialog_background`, …) and alignment words; prefer the JSON.

Note the AutoLITHP corpus contains **no `@include`** in any `.dcl` file, and 48
`name : dialog {` definitions across 18 real `.dcl` files.

### 3.2 The DCL ↔ AutoLISP link (the edge the extractor exists to produce)

The chain, and where each hop is `EXTRACTED` vs `INFERRED`:

```
.dcl:   lithp_mgr : dialog { ... : list_box { key = "lbxModules"; ... } ... }
                 │                              │
                 │  (new_dialog "lithp_mgr" id) │  (action_tile "lbxModules" "(mgr:on-select)")
                 ▼                              ▼
.lsp:   (setq id (load_dialog "manager.dcl"))   (set_tile "txtModName" v)
                              │                 (get_tile "lbxModules")
                              ▼                 (mode_tile "btnOK" 0)
                        file → file edge
```

- `key = "..."` in DCL is the **only** identifier AutoLISP can address a tile by
  (`action_tile` / `set_tile` / `get_tile` / `mode_tile` / `get_attr` / `client_data_tile`
  all take that string as their first argument). It is a plain string on both sides — there
  is no compiler check, so a typo is a silent runtime no-op. A graph edge here has real value.
- The dialog **name** (the `ID` before `: dialog`) is what `new_dialog` takes, not the key.
  Two different namespaces; do not conflate them.
- `action_tile`'s second argument is **AutoLISP source inside a string literal**. It must be
  re-parsed (the same reader, run on the string body) to yield the `dcl_action` →
  function edge. Same for the DCL `action = "(fn)";` attribute, which is the declarative
  equivalent, and for `new_dialog`'s optional 4th `default-action` argument.
- Confirmed in the corpus at `src/plugins/pltrn.lsp:10882` (`action_tile` with code-in-string),
  `:10903` (`load_dialog` with a **variable**, so `INFERRED` at best) and `:10907`
  (`new_dialog` with a literal, so `EXTRACTED`) — as already recorded in
  `README.md` §"Language traits an extractor must know".

---

## 4. `.mnl`, `.cuix`/`.cui`/`.mnu` and whether menu files are worth an edge

- **About Source Code Files (AutoLISP)** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-299DBF3D-7896-465A-9F79-D654E7E48F25.htm>
  → *"AutoLISP source code can also be stored in files with a `.mnl` extension. A Menu AutoLISP
  (MNL) file contains custom functions and commands that are required for the elements defined
  in a customization (CUIx) file."* Also: *"AutoLISP code can be loaded from any ASCII text
  file"* — the extension is convention, not a format.
- **About Loading an AutoLISP File with a CUIx File** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-830DF85D-4722-4B09-A311-D356C975E368.htm>
  → an MNL is *"an AutoLISP Menu Source (MNL) file that has the same name and in the location
  as the main, enterprise, or partial customization (CUIx) files being loaded"*. Loaded
  automatically with its paired CUIx (AutoCAD, **not** AutoCAD LT).
- **About Auto-Loading and Running AutoLISP Routines** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-FDB4038D-1620-4A56-8824-D37729D42520.htm>
  → load order: `acad.lsp` (once at app startup, or per-drawing when `ACADLSPASDOC = 1`) →
  `acaddoc.lsp` (*"always loaded with each drawing regardless of the settings of ACADLSPASDOC"*)
  → **MNL** (*"The MNL file is loaded after the `acaddoc.lsp` file"*) → `S::STARTUP`.
  `S::STARTUP` *"must be defined with the `defun-q` function rather than `defun`"* — this is the
  one place `defun-q` genuinely matters.

**So an `.mnl` is just an `.lsp` with a different suffix plus one implicit edge:**
`foo.mnl` → `foo.cuix` (or `foo.mnu`) **by basename in the same directory**. That is a
zero-parsing, filename-only rule and is worth implementing — it is one `Path.with_suffix`.

**Macro strings in `.cui`/`.cuix`/`.mnu`:**

- **About Special Control Characters in Command Macros** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-DDDB6E26-75E1-4643-8C6A-BEAEBA83A424.htm>
  → the table: `;` "Issues Enter"; `\` "Pauses for user input"; `.` access an undefined
  standard command; `_` global-name translation; `'` transparent invocation;
  **`^C` "Cancels the active command or command option; equivalent to pressing Esc"**;
  `^H` Backspace; `^M` Enter.
- **About Command Macro Strings** —
  <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-D991386C-FBAA-4094-9FCB-AADD98ACD3EF.htm>
  → *"`^C^C` means to press Esc twice before executing the macro"*, recommended because
  *"`^C^C` handles canceling out of most command sequences"*; *"a single `^C` cancels most
  commands, `^C^C` is required to return to the command prompt from a dimensioning command."*
  It has a section headed "About Using AutoLISP in Macros" whose only sentence is
  *"Creating commands that use AutoLISP is a more advanced way to use the program's
  customization feature."* — **Autodesk publishes no example of the `^C^C(c:foo)` form and no
  formal grammar for macro strings.**

**Recommendation: do not build a `.cuix` reader.**

1. A `.cuix` is a **ZIP archive** containing XML (`*.cui` + `.mnr`/`.mnl` siblings); a `.cui`
   is XML; a `.mnu` is legacy plain text. Three formats, one of them compressed, for one edge.
2. Autodesk documents no macro grammar, so the extraction would be a regex over
   `\^C\^C\(([A-Za-z0-9:_-]+)` with no spec behind it.
3. **The AutoLITHP corpus has zero `.mnl`, `.cui`, `.cuix` and `.mnu` files** — nothing to
   measure against and nothing to regress.

Ship instead: (a) `.mnl` claimed as an AutoLISP suffix (it *is* AutoLISP, and both
tree-sitter-autolisp and autolisp-lsp already register it); (b) the basename→CUIx edge, as
`INFERRED`, and only when the sibling file actually exists on disk. Defer macro parsing until
a corpus with menu files exists.

---

## 5. Constructs that change symbol extraction (beyond the README table)

Ordered by how much damage getting them wrong does. "Corpus" = `src/**/*.lsp` (36 files).

| # | Construct | Effect on extraction | Corpus | Handling |
|--:|:----------|:---------------------|-------:|:---------|
| 1 | `(defun name (a b / c d) …)` | the `/` splits **arguments** from **locals**. Everything after `/` is a *declaration*, not a call. Emitting `calls` edges for locals is the classic false-positive source | 2530 | tree-sitter `parameter_list` gives `parameter` vs `local` as separate fields — free |
| 2 | Undeclared locals are **global** and dynamically scoped (`cc-DB760.001.md`, last row: *"an UNDECLARED local is global and silently shared"*) | a `(setq x …)` inside a defun with no `/ x` is a genuine global write. Treating all in-defun `setq` as local loses real cross-function coupling; treating all as global creates noise | 8980 `setq` (whole tree) | emit a `global` node only for a top-level `setq`, or an in-defun `setq` to a name **not** in the enclosing `parameter_list`. This is the highest-volume defect class in AutoLISP, so it is worth the extra check |
| 3 | `'symbol` in a quoted position — `(vl-catch-all-apply 'log:add …)`, `(mapcar 'car lst)`, `(apply 'fn args)` | a function reference with no call syntax. Missing these loses most of the call graph in error-wrapped code | 292 `vl-catch-all-apply` in `src/`; 16 691 `'sym` tokens tree-wide | tree-sitter `quote` node; resolve `'x` to a function only when `x` is a known defun or a known builtin, else drop |
| 4 | `(function fn)` / `(function (lambda …))` | Visual LISP's "compile this reference" wrapper; semantically `quote` for the graph | 18 | same treatment as `'sym` |
| 5 | `(lambda (a / b) …)` | anonymous function; still a `parameter_list` with locals. Contains real calls. Do **not** emit a `function` node (no name) but **do** walk the body for `calls` | 169 | walk body, attribute calls to the enclosing named defun |
| 6 | `(setq fn (lambda …))` | binds a function to a variable. Later `(fn …)` is a call to a *variable*, unresolvable statically | rare | emit the global/local node; do not fabricate a `calls` edge |
| 7 | `(foreach v lst body…)` | `v` is a **binding form**, not a call. A naive "first symbol in a list is a call" walker emits `calls → v` | 964 tree-wide | special-case: `foreach`, `defun`, `defun-q`, `lambda`, `quote`, `setq`, `cond`, `if`, `while`, `repeat`, `progn` are the forms whose head is not a call and whose 2nd position is not an argument. `velisp/grammar/VeLisp.g4` special-cases exactly this set — a good checklist |
| 8 | `*error*` handler convention | the user-definable error handler (Non-alphabetic Functions Reference). Almost always `(defun *error* (msg) …)` **or** a lambda assigned via `(setq *error* handler)`. Per `cc-DB760.001.md`, `vl-catch-all-apply` **bypasses** the callee's `*error*` entirely | 241 | treat `*error*` as a well-known symbol, not a normal global; the assignment `(setq *error* fn)` is a real `calls`-ish edge worth an `INFERRED` relation |
| 9 | `c:` vs `C:` case | AutoLISP is case-insensitive; `(defun C:HELLO …)` and `(defun c:hello …)` are one symbol. Autodesk's own docs mix the two on the same page (<…/GUID-EF910176-86D2-4158-A7C3-E926A002F421.htm> writes the rule as `c:` and the example as `C:HELLO`) | 44 | **case-fold every symbol id**, then keep the first-seen spelling as the display label. Applies to *all* symbols, not just `C:` |
| 10 | `(princ)` bare at end of a defun | the idiomatic "return nothing quietly" terminator. It is a real call to a builtin, so it lands on the denylist and disappears — no special handling needed, but it explains why `princ` would otherwise be the #1 callee | 1089 tree-wide | denylist |
| 11 | `(command "_.UNDO" "_End")` | AutoCAD command invocation via string. `_` prefix = global name, `.` prefix = bypass redefinition (per the macro control-character table). Strip both before matching against `cmdAndVarsList.txt` | 96 (earlier count) | `command_invokes` → stub node, name normalised `^[_.]*` |
| 12 | `(autoload "BONUSAPP" '("APP1" "APP2"))` | <…/GUID-421B36DE-38EA-4161-9768-01647B5492E8.htm>. Declares that entering `APP1` loads `BONUSAPP.lsp`. Yields **two** edges: file → file (`loads`, deferred) and command-stub → file. Path and extension may be omitted (`.lsp`/`.fas`/`.vlx`) | **0** | implement, `INFERRED`, no acceptance gate |
| 13 | `(load "x" onfailure)` | <…/GUID-F3639BAA-FD70-487C-AEB5-9E6096EC0255.htm>. Extension search order when omitted is **`.vlx` → `.fas` → `.lsp`**. `onfailure` may itself be *"a valid AutoLISP function"* that is *evaluated* — a second edge | 20 (earlier count) | resolve literal 1st arg `EXTRACTED`; variable 1st arg `INFERRED`/drop; treat a symbol `onfailure` as a call |
| 14 | `(vl-load-com)` | <…/GUID-6C7A8632-C12F-42BD-909E-68D804863AE2.htm>. Pure side effect: makes `vla-*`/`vlax-*`/`vlr-*` available. **Not an edge** — it is the marker that COM names in the file are builtins | 102 tree-wide | ignore; optionally set a per-file flag that enables the COM prefix denylist |
| 15 | `(vlax-import-type-library :tlb-filename f :methods-prefix … :properties-prefix … :constants-prefix …)` | <…/GUID-1699B6A0-C4A6-4BC4-82DF-5040CFF3394A.htm>. **Synthesises new function names at runtime** from user-chosen prefixes. Any name matching a declared prefix is a builtin-like external, not a project symbol. The five keywords are in `alllispkeys.txt` as `:tlb-filename :methods-prefix :properties-prefix :constants-prefix :prog-id` | **0** | when present with literal prefixes, add them to the file's local denylist; otherwise ignore |
| 16 | `(vlr-*-reactor data callbacks)` where `callbacks` is `'((:vlr-event . cb-fn))` | the callback function name lives in the **cdr of a quoted dotted pair**, keyed by a `:vlr-*` event keyword. `alllispkeys.txt` carries ~120 `:vlr-*` keywords | 95 `vlr-` tree-wide | walk quoted dotted pairs whose car is a `:vlr-` keyword; the cdr is a `calls` target. `dotted_pair` is a first-class tree-sitter node, so this is cheap |
| 17 | `(eval (read "…"))` | fully dynamic. Unresolvable | 17 `eval`, 14 `read` in `src/` | emit nothing; optionally a `dynamic` marker so a human knows the graph is incomplete there |
| 18 | `defun-q` + `S::STARTUP` | <…/GUID-5EE138EF-D531-441B-9F12-8D5645C540FE.htm>: same signature as `defun`, but keeps the body accessible as a list (`defun-q-list-ref` / `defun-q-list-set`). Required for `S::STARTUP` per the auto-load doc | **0** | parse as a `function` node identical to `defun` (tree-sitter already aliases both into `function_definition`); `defun-q-list-set` mutation is out of scope |
| 19 | VLX separate-namespace: `(vl-doc-export 'sym)`, `(vl-doc-import …)`, `(vl-arx-import 'sym)`, `(vl-bb-set …)`/`(vl-bb-ref …)` | in a separate-namespace VLX, a `defun` is **not** visible to the document namespace until exported. <…/GUID-6210D0C8-BBF9-4C84-9220-2CFB579B0302.htm>: *"Functions defined in external ObjectARX applications can be accessed from a separate-namespace VLX, but you must first issue `vl-arx-import`"*. Blackboard: <…/GUID-0C8F8E36-7C10-45C4-9EF6-C284E56A8EA2.htm> | **0** | `(vl-doc-export 'x)` = a visibility attribute on the existing function node, not a new node. `vl-bb-set`/`vl-bb-ref` are a global read/write pair keyed by a string. Low priority — no VLX build in this corpus |
| 20 | Multi-pair `(setq a 1 b 2)` | already in the README table; restated because it interacts with #2 — every *odd* element is a name | 8980 | pair-wise walk |

---

## 6. Doc-comment conventions

### 6.1 Autodesk: no docstring syntax in the language — but one published tag convention

- **Confirmed: the AutoLISP Reference documents no docstring or doc-comment syntax.** The
  `defun` and `defun-q` pages give only `(defun sym ([args] [/ vars]) expr …)`; there is no
  "documentation string" position, no `@param`-style tag set, and no comment convention
  anywhere in the AutoLISP Developer's Guide. The only comment syntax the language has is
  `;` to end of line and `;| … |;` block.
- **However**, Autodesk's own VS Code extension ships a generator that defines a de-facto
  convention. `AutoLispExt/extension/src/help/userDocumentation.ts`, function
  `generateDocumentationSnippet` (backing the `autolisp.generateDocumentation` command),
  emits exactly:

  ```lisp
  ;|
    ${1:description}
    @Param arg1 ${2:?}
    @Param arg2 ${3:?}
    @Returns ${4:?}
  |;
  ```

  i.e. a **block comment** placed before the `defun`, with `@Param <name> <text>` per argument
  (arguments only — the function `getDefunArguments` deliberately slices off everything from
  the `/` divider onward, so locals are excluded) and a single `@Returns`. This is the closest
  thing to an official convention that exists, and it is Apache-2.0.
  Note the capitalisation: `@Param` / `@Returns`, not `@param` / `@return`.
- Third convention worth knowing: `tree-sitter-autolisp` models a **string literal
  immediately after the parameter list** as `field("docstring", $.string)`, resolved with
  `prec.dynamic` so `(defun f (x) "doc" x)` parses the string as the docstring rather than as
  the first body form. That is Common Lisp's convention, not AutoLISP's — AutoLISP has no such
  semantics, and the string is simply an ignored body expression at runtime. Harmless to
  consume if present, but do not expect it in real code (the AutoLITHP corpus uses none).

### 6.2 AutoLITHP's convention (the one that actually matters for this corpus)

Source: `/home/p4ndr/repos/autolithp/src/modules/lyr/mod.lsp:1-12` and
`/home/p4ndr/repos/autolithp/Docs/developer-guide.md` §"Module metadata header" (lines 95-142).

A `;;;`-prefixed header block at the top of a module entry point:

```lisp
;;; @sidecar mod.md
;;; ---------------------------------------------------------------
;;; Layer Management Module — lyr
;;; ---------------------------------------------------------------
;;;
;;; @module       layer-tools
;;; @version      1.0.0
;;; @prefix       lyr:
;;; @depends      utl, err, dxf, ss
;;; @description  Layer creation, deletion, property management,
;;; @doc mod.md#C0001
;;;
;;; ---------------------------------------------------------------
```

| Tag | Value shape | Graph meaning | Count (whole tree) |
|:----|:------------|:--------------|-------------------:|
| `@module` | bare identifier (`layer-tools`) | the `module` node's name | 138 |
| `@version` | semver | attribute on the module node | 138 |
| `@prefix` | `lyr:` — **includes the colon** | the `defines` (module → function) rule: a function whose name starts with this prefix belongs to this module. `INFERRED` per the README | 138 |
| `@depends` | comma-separated module short names (`utl, err, dxf, ss`) | `module_depends` edges. Note the values are *short* names (`utl`), not `@module` values (`layer-tools`) — resolution is by directory/prefix, not by `@module` | 138 |
| `@description` | free text, may wrap across lines with no continuation marker | attribute | 138 |
| `@sidecar` | a `.md` filename, resolved **relative to the `.lsp` file's directory** | `sidecar_doc` edge, file → doc | 62 |
| `@doc` | `file.md#Cnnnn` — filename plus an anchor | `sidecar_doc` edge with a fragment; appears both in module headers and **per-function**, which is why it dominates | 2304 |
| `@tags` | (undocumented in the developer guide) | seen 6 times; treat as free-form | 6 |
| `@return` | (undocumented in the developer guide) | seen 6 times, lowercase — note this is **not** AutoLispExt's `@Returns` | 6 |

Extraction rule: `^\s*;;;?\s*@([a-z]+)\s+(.*)$`, applied to the leading comment run of a file
for module-level tags, and to the comment run immediately preceding a `defun` for `@doc`.
`@description` wraps without a marker, so a continuation line is any `;;;` line that follows
and carries no `@tag`.

There is also a per-function prose convention (not tagged), visible at `mod.lsp:29-36`:

```lisp
;; lyr:_get-table-entry — Get a layer table entry by name.
;;
;; Parameters:
;;   name  [string]  Layer name.
;;
;; Returns:
;;   [list]  Table entry alist, or nil if not found.
```

`;;` (two semicolons) for function-level prose, `;;;` (three) for file/module-level tags —
the Emacs Lisp convention. A leading-comment-run reader keyed on the semicolon count gets both.

---

## 7. Recommendation for the extractor

1. **Grammar**: vendor `shioshosho/tree-sitter-autolisp`'s `grammar.js` + `src/parser.c`
   (resolve the licence question first), or re-derive an equivalent grammar. Its
   `function_definition{name, parameter_list{parameter,local}, docstring, body}` +
   case-insensitive keywords + `:`-in-symbol rule map 1:1 onto the README's target node model,
   which `tree-sitter-commonlisp` does not (`package_lit` mis-reads `err:`). If the licence
   cannot be cleared, extend `autolithp/tools/lread.py` (72 lines, already produces
   `Form`/`Sym`/`Str` with `.line`) — it handles `;` comments, strings with escapes, `'quote`
   and nesting, and needs only `;| … |;` block comments and dotted pairs added.
2. **DCL**: hand-written reader, ~120 lines, per the grammar in §3.1. No grammar exists to
   reuse, and the language is 5 token classes. `velisp`'s `test/dcl/*.dcl` (GPL — read-only)
   is a ready-made conformance checklist.
3. **Builtins**: ship `winonlylispkeys_prefix.txt`'s 3 prefixes + the ~487-name core list +
   the 111 `functions`-only names, under a `LICENSE.AutoLispExt` (Apache-2.0) sidecar.
4. **Measurement discipline**: every corpus claim must exclude
   `/home/p4ndr/repos/autolithp/.claude/worktrees/` (§0).

---

## 8. All URLs

### Repositories

| URL | Licence | Note |
|:----|:--------|:-----|
| <https://github.com/shioshosho/tree-sitter-autolisp> | MIT declared in manifests, **no LICENSE file**, API `null` | the only tree-sitter AutoLISP grammar |
| <https://github.com/shioshosho/autolisp-lsp> | **none** | Rust LSP, symbol table, `src/builtins.rs` |
| <https://github.com/Autodesk-AutoCAD/AutoLispExt> | **Apache-2.0** | Autodesk's VS Code extension |
| <https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/data/alllispkeys.txt> | Apache-2.0 | 2730 unique names |
| <https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/data/alldclkeys.txt> | Apache-2.0 | 114 lines, flat |
| <https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/data/winonlylispkeys_prefix.txt> | Apache-2.0 | 5 lines: `vla- vlax- vlr- vl-load-com vl-load-reactors` |
| <https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/data/cmdAndVarsList.txt> | Apache-2.0 | 1738 AutoCAD commands + sysvars |
| <https://raw.githubusercontent.com/Autodesk-AutoCAD/AutoLispExt/main/extension/src/help/webHelpAbstraction.json> | Apache-2.0 | 2565 functions, 31 dclTiles, 35 dclAttributes, 894 enums |
| <https://github.com/Autodesk-AutoCAD/AutoLispExt/blob/main/extension/src/parsing/dclParser.ts> | Apache-2.0 | DCL scanner |
| <https://github.com/Autodesk-AutoCAD/AutoLispExt/blob/main/extension/src/help/userDocumentation.ts> | Apache-2.0 | `@Param`/`@Returns` snippet |
| <https://github.com/Autodesk-AutoCAD/AutoLispExt/blob/main/extension/src/symbols.ts> | Apache-2.0 | symbol/outline index |
| <https://github.com/ten0s/velisp> | **GPL-3.0-or-later** | interpreter; `grammar/VeDcl.g4`, `grammar/VeLisp.g4`, `test/dcl/*` |
| <https://github.com/tree-sitter-grammars/tree-sitter-commonlisp> | — | the current dependency; `package_lit` mis-reads `err:` |
| <https://github.com/sdfaheemuddin/autolisp-outline-extension> | MIT | regex outline only |
| <https://github.com/manualChair/include> · <https://github.com/manualChair/commonlib> | MIT | `load` tracker / VLX common lib |
| <https://github.com/xdcad/XDrx-API> | free, non-commercial | ARX function library |

### Autodesk documentation (AutoCAD 2026, ENU)

| Topic | URL |
|:------|:----|
| Functions Reference index | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-4CEE5072-8817-4920-8A2D-7060F5E16547.htm> |
| Non-alphabetic Functions (`*error*`, operators) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-EBDC1072-48BF-4204-80B1-73430DBF58E1.htm> |
| Function-Handling Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-6804DF2D-E5C4-466A-9869-3CDD7A031FAA.htm> |
| Application-Handling Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-E2B683FE-43FB-4F5D-A9AE-809772FE8D3B.htm> |
| Dialog Box Opening and Closing Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-A96C28B5-4B9A-4EE8-8C46-808F14217777.htm> |
| Tile- and Attribute-Handling Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-B254FD2A-669A-4A16-9816-AAC79E983571.htm> |
| Predefined Attributes for Tiles (`key`, `action`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-5B0C8B10-F968-4A56-B4A5-6A26935B341A.htm> |
| VLX Namespace Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-5784FC6F-82DD-4459-879B-6EC3BD5E88D1.htm> |
| Reactor Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-B83B512E-CEF6-43C5-9099-398999E254AF.htm> |
| `defun-q` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-5EE138EF-D531-441B-9F12-8D5645C540FE.htm> |
| `defun-q-list-ref` / `-set` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-DAF4A76E-9346-4A68-A0C8-17695177033B.htm> · <…/GUID-CDA30337-9889-4D33-9461-503F307D1360.htm> |
| `autoload` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-421B36DE-38EA-4161-9768-01647B5492E8.htm> |
| `load` (incl. `onfailure`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-F3639BAA-FD70-487C-AEB5-9E6096EC0255.htm> |
| `vl-load-com` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-6C7A8632-C12F-42BD-909E-68D804863AE2.htm> |
| `vlax-import-type-library` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-1699B6A0-C4A6-4BC4-82DF-5040CFF3394A.htm> |
| `vl-doc-export` · `vl-doc-import` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-696970BC-3669-412C-8194-7ADD950EE7BA.htm> · <…/GUID-68A6C7D0-8EE9-4F78-829A-86D08D2BD193.htm> |
| `vl-bb-set` · `vl-bb-ref` | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-2B1484FC-BBD1-408B-A8A0-DB931363630F.htm> · <…/GUID-F4DAAAA4-5A96-4AFF-B8AE-C1F4F91C80C9.htm> |
| Namespace Communication Functions | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP-Reference/files/GUID-F5DD5472-1695-4CA3-9110-E6008E87BB89.htm> |
| Syntax and Comments in DCL Files | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-1A629E01-828D-402E-965F-DE76F1BF28AD.htm> |
| Referencing DCL Files (`@include`, `base.dcl`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-79DEC649-2DA1-4871-8C22-2C5B7DD287A7.htm> |
| Tile References (`name;` and `: name { }`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-709DE551-4888-4FD6-8C0E-EAB6BA2C1B3A.htm> |
| Dialog Box Components | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-E10AFB89-89BF-4616-819A-439BAEAAD0B9.htm> |
| Using DCL to Define Dialog Boxes | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-92C77010-5C56-460E-81AA-2F6631317DE6.htm> |
| Semantic Auditing of DCL Files | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-44C84FB7-5E87-46E9-9E14-24C157A87179.htm> |
| Managing Dialog Boxes (DCL) | <https://help.autodesk.com/cloudhelp/2026/HUN/AutoCAD-AutoLISP/files/GUID-D3B46441-1867-479E-9478-C604B6D7441D.htm> |
| Defining Commands (`c:` prefix) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-EF910176-86D2-4158-A7C3-E926A002F421.htm> |
| Redefining AutoCAD Commands | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-38D0244E-C0C7-4FF0-A4B9-DE6E05635BD6.htm> |
| Source Code Files (`.lsp`, `.mnl`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-299DBF3D-7896-465A-9F79-D654E7E48F25.htm> |
| Auto-Loading and Running AutoLISP Routines (load order, `S::STARTUP`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-FDB4038D-1620-4A56-8824-D37729D42520.htm> |
| Loading an AutoLISP File with a CUIx File (MNL rule) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-830DF85D-4722-4B09-A311-D356C975E368.htm> |
| Special Control Characters in Command Macros (`^C`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-DDDB6E26-75E1-4643-8C6A-BEAEBA83A424.htm> |
| Command Macro Strings (`^C^C`) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Customization/files/GUID-D991386C-FBAA-4094-9FCB-AADD98ACD3EF.htm> |
| Accessing External ObjectARX Functions from a Separate-Namespace VLX | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-6210D0C8-BBF9-4C84-9220-2CFB579B0302.htm> |
| Sharing Data Between Namespaces (blackboard) | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-0C8F8E36-7C10-45C4-9EF6-C284E56A8EA2.htm> |
| Making Functions Available to Documents and Other Applications | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-6439354D-BC69-4DFE-971F-ED8AA9907AAB.htm> |
| Importing a Type Library | <https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-AutoLISP/files/GUID-B140BF54-AD94-47EE-BC3E-91AEFA63D0CE.htm> |

### Beehive search endpoint used

```
https://beehive.autodesk.com/community/service/rest/cloudhelp/resource/cloudhelpchannel/search/
    ?q=<query>&p=OARX&v=2026&l=ENU&maxresults=N
```

### Community (from `cc-RF760.001.md` §1.5)

<https://www.lee-mac.com/programs.html> · <https://afralisp.net/dialog-control-language/> ·
<https://www.theswamp.org/> · <https://www.cadtutor.net/> · <https://jtbworld.com/autolisp-visual-lisp> ·
<https://en.wikipedia.org/wiki/Dialog_Control_Language>
