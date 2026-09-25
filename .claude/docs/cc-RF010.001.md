# Prior art: declaratively defining a language's structure and symbol/relation extraction

> **Prepared for**: `graphify-lang` (fork of [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)), 8 September 2026
> **Question**: what existing systems let you define a language — its suffixes, node kinds, edge kinds, and how to find them — in a configuration file rather than in code, and what should `graphify-lang`'s plugin manifest look like?
> **Method**: web research against primary documentation (URLs on every claim), plus two local measurements run against the `graphifyy 0.9.55` pipx venv (`tree-sitter 0.25.2`) and the [AutoLITHP](https://github.com/p4ndr/autolithp) corpus.

---

## 0. Executive summary

| Rank | System | What to take | What to leave |
|-----:|:-------|:-------------|:--------------|
| 1 | **tree-sitter tag queries (`tags.scm`)** | The whole extraction-rule layer. A `.scm` query file *is* the declarative rule format, it already has a standard capture vocabulary (`@definition.function` / `@reference.call` / `@name` / `@doc`), and grammars already ship them. | Nothing. This is the closest fit and the cheapest. |
| 2 | **universal-ctags optlib** | The mental model for grammar-less languages: `--langdef` + `--kinddef` + `--regex-<LANG>` + `{_role=...}` gives you kinds, roles (= edge types) and a scope stack from a text file. | Its POSIX-ERE engine, its `.ctags` flag-soup syntax, and the C-binary dependency. Re-express the *concepts* as manifest rules. |
| 3 | **GitHub linguist `languages.yml`** | The registry shape: one map per language, `type` / `extensions` / `filenames` / `interpreters` / `aliases` / `group`. Directly models the `suffixes` half of the manifest. | Its display-oriented keys (`color`, `ace_mode`, `codemirror_mode`, `language_id`). |
| 4 | **Semgrep rule YAML** | The composable-predicate idea (`patterns` / `pattern-either` / `pattern-not-inside` / `metavariable-regex`) as the shape for a prose/regex rule block. | Its whole pattern engine — Semgrep parses with its own per-language grammars; you cannot borrow the matcher. |
| 5 | **SCIP / Kythe / LSIF** | The *output* vocabulary — role bitsets (`Definition`, `Import`, `ReadAccess`, `WriteAccess`), relationship kinds (`is_reference` / `is_implementation`), `defines/binding` vs `ref/call`. Use it to name graphify's edge kinds. | The protobuf/JSON-lines wire formats. graphify has its own schema. |
| — | **tree-sitter-graph / stack-graphs** | Proof that arbitrary graph construction from a syntax tree can be fully declarative. Read the DSL for ideas. | Do not adopt: Rust-only, no Python bindings, and `github/stack-graphs` was **archived 9 September 2025**. |
| — | **Prose: Akoma Ntoso, StrictDoc, sphinx-needs, Doorstop** | The *node-type + typed-link* manifest shape (`needs_types` + `needs_extra_links`), and the `num`/`heading`/`content` + `<ref eId=…>` hierarchy-plus-cross-reference model. | Their storage formats. graphify already extracts markdown headings and `[[wikilinks]]`. |

**Headline measurement** (§7): a **two-line tree-sitter query** recovers 27 function definitions and 298 call references from `~/repos/autolithp/src/core/err.lsp`, where graphify's hand-written Common Lisp walker produces 1 node and 0 edges. The AutoLISP gap described in `README.md` is a *query* problem, not a parser problem.

**Format recommendation**: **TOML**, because graphify already ships a TOML reader (`tomli>=2.0.1; python_version < '3.11'` in [`pyproject.toml:18`](file:///home/p4ndr/repos/graphify-lang/pyproject.toml)) and explicitly refuses a PyYAML dependency (`graphify/ingest.py:23`: *"We intentionally do not depend on PyYAML (not in pyproject deps)"*). See §9.

---

## 1. universal-ctags optlib

The canonical "define a language in a config file" system. A parser is a set of command-line options, normally stored in a `.ctags` file, that universal-ctags loads at startup.

Sources: [Extending ctags with Regex parser (optlib)](https://docs.ctags.io/en/latest/optlib.html) · [`ctags-optlib(7)` man page](https://docs.ctags.io/en/latest/man/ctags-optlib.7.html) · [`docs/optlib.rst` source](https://github.com/universal-ctags/ctags/blob/master/docs/optlib.rst) · [`optlib/cmake.ctags` real-world example](https://github.com/universal-ctags/ctags/blob/master/optlib/cmake.ctags)

### What the definition file looks like

```ctags
# foo.ctags — a complete optlib parser
--langdef=FOO
--map-FOO=.foo
--kinddef-FOO=m,module,modules
--kinddef-FOO=f,func,functions

# a *role* turns a match into a reference tag (an edge), not a definition
--_roledef-FOO.m=imported,imported module
--regex-FOO=/import[ \t]+([a-z]+)/\1/m/{_role=imported}

# a custom *field* attaches arbitrary metadata to the tag
--_fielddef-FOO=protection,access scope
--regex-FOO=/^((public|private) +)?func ([^(]+)\((.*)\)/\3/f/{_field=protection:\1}{_field=signature:(\4)}

--extras=+r
--fields=+r
--fields-FOO=+'{protection}{signature}'
```

Scope tracking uses a stack driven by long flags on each pattern
([optlib.html](https://docs.ctags.io/en/latest/optlib.html), [`ctags-optlib(7)`](https://docs.ctags.io/en/latest/man/ctags-optlib.7.html)):

| Flag | Effect |
|:-----|:-------|
| `{scope=push}` | push the captured tag onto the internal scope stack |
| `{scope=ref}` | fill the tag's `scope:` field from the stack top |
| `{scope=pop}` / `{scope=clear}` / `{scope=set}` / `{scope=replace}` | pop / empty / clear-then-push / pop-ref-push |
| `{placeholder}` | match but emit no tag (used for scope bookkeeping) |
| `{exclusive}` | if this pattern matches the line, skip the remaining patterns |
| `{icase}` | case-insensitive |
| `{postrun}` | run these patterns after a built-in parser has finished |

Beyond single-line `--regex-<LANG>` there are two escalation tiers:

- **`--mline-regex-<LANG>`** — matches across line boundaries; requires `{mgroup=N}` to say which capture group fixes the tag's line number ([`ctags-optlib(7)`](https://docs.ctags.io/en/latest/man/ctags-optlib.7.html)).
- **Multi-table regex** — `--_tabledef-<LANG>=NAME` declares lexer states and `--_mtable-regex-<LANG>=TABLE/PATTERN/NAME/KIND/FLAGS` adds patterns to a state, with `{tenter=T}` (push + enter), `{tleave}` (pop), `{tjump=T}` (switch without stacking), `{treset}`, `{tquit}`. The docs describe it as "inspired by `lex`", introduced because "the `--regex-<LANG>` and `--mline-regex-<LANG>` options are not sufficient" for nested scopes and commented regions ([optlib.html](https://docs.ctags.io/en/latest/optlib.html)).

```ctags
# multi-table: skip comments, only tag vars inside a `var ... ;` block
--_tabledef-X=toplevel
--_tabledef-X=comment
--_tabledef-X=vars
--_mtable-regex-X=toplevel/\/\*//{tenter=comment}
--_mtable-regex-X=toplevel/var[ \n\t]//{tenter=vars}
--_mtable-regex-X=toplevel/.//
--_mtable-regex-X=comment/\*\///{tleave}
--_mtable-regex-X=comment/.//
--_mtable-regex-X=vars/;//{tleave}
--_mtable-regex-X=vars/([a-zA-Z][a-zA-Z0-9]*)/\1/v/
--_mtable-regex-X=vars/.//
```

### Node / edge concepts it can express

- **Node kinds** — arbitrary, user-declared (`--kinddef`), each with a letter, a name and a description.
- **Edges, weakly** — via *roles*. `--extras=+r` plus `{_role=imported}` emits a *reference tag* whose `roles:` field names the relationship. `docs/optlib.rst` shows one pattern carrying two roles: `roles:lvalue,incremented`. This is the closest thing in ctags to a typed edge, and it names the relation but not both endpoints — the source endpoint is implicit (the containing scope).
- **Containment** — the scope stack yields `scope:` / `scopeKind:` fields, i.e. a parent-child edge.
- **Arbitrary attributes** — custom fields via `--_fielddef` + `{_field=name:\1}`.

### What it cannot express

- **Anything needing real parsing.** The default engine is POSIX ERE, which the docs say "does *not* support many of the 'modern' extensions such as lazy captures, non-capturing grouping, atomic grouping, possessive quantifiers, look-ahead/behind", and "may be notoriously slow when backtracking" ([optlib.html](https://docs.ctags.io/en/latest/optlib.html)). PCRE2 is available only if built against libpcre2 (`--list-features`).
- **`.` does not match newline** in `--regex-<LANG>`.
- **Cross-file resolution.** A reference tag records that *something* named `X` was imported; it does not bind it to the definition of `X` in another file. That is what SCIP/Kythe/stack-graphs exist for.
- **No recursion** — nesting is emulated with the table stack only.

### Maturity and Python availability

Mature and widely deployed; universal-ctags ships dozens of stock optlib parsers in [`optlib/`](https://github.com/universal-ctags/ctags/tree/master/optlib). There is **no official Python binding** — it is a C executable. The practical integration is subprocess + `--output-format=json`, which emits **one JSON object per line** with fields `_type`, `name`, `path`, `pattern`, `language`, `kind`, `scope`, `scopeKind` (and any enabled extras/fields); this requires a build with `libjansson` ([`ctags-json-output(5)`](https://docs.ctags.io/en/latest/man/ctags-json-output.5.html)). Not installed on this host (`which ctags` → not found), so adopting it means adding a non-Python runtime dependency.

**Verdict for graphify-lang**: borrow the *concepts* — kinds, roles, scope-stack flags, `exclusive`, `placeholder` — as the vocabulary of a `[[rule]]` block for grammar-less languages. Do not shell out to ctags.

---

## 2. tree-sitter tag queries (`tags.scm`)

The closest fit to graphify's problem, and the layer GitHub's search-based code navigation and aider's repo map both build on.

Sources: [Code Navigation](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html) ([source](https://github.com/tree-sitter/tree-sitter/blob/master/docs/src/4-code-navigation.md)) · [Query syntax](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html) · [Predicates and directives](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/3-predicates-and-directives.html)

### What the definition file looks like

A `queries/tags.scm` file inside the grammar repository. Real example, from [`tree-sitter-commonlisp/queries/tags.scm`](https://github.com/tree-sitter-grammars/tree-sitter-commonlisp/blob/master/queries/tags.scm):

```scheme
;;; Function Definitions
(defun_header
  function_name: (sym_lit) @name) @definition.function

;;; exclude lambda-list symbols from being read as calls
(defun_header
  lambda_list: (list_lit . [(sym_lit) (package_lit)] @ignore))

;;; every list whose head is a symbol is a call
(list_lit . [(sym_lit) (package_lit)] @name) @reference.call
```

And from the JavaScript grammar, quoted in the tree-sitter docs:

```scheme
(assignment_expression
  left: [(identifier) @name
         (member_expression property: (property_identifier) @name)]
  right: [(arrow_function) (function)]) @definition.function
```

### Node / edge concepts it can express

The capture vocabulary is `@<role>.<kind>` plus two special captures ([Code Navigation](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html)):

| Capture | Meaning |
|:--------|:--------|
| `@name` | **required** — the identifier text of the entity |
| `@doc` | optional — the docstring/leading comment |
| `@definition.class` `.function` `.interface` `.method` `.module` | definition roles |
| `@reference.call` `.class` `.implementation` | reference roles |
| `@local.scope` `@local.definition` `@local.reference` | scope-local name binding (the `locals.scm` sibling query) |

Two built-in directives clean up doc capture: `(#strip! @doc "^#\\s*")` removes comment markers, `(#select-adjacent! @doc @definition.class)` keeps only the comment adjacent to the definition.

Query syntax capabilities ([1-syntax](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html)):

- S-expression node patterns, named `(identifier)` and anonymous `"!="` nodes;
- **field names** — `left: (member_expression object: (call_expression))`;
- **negated fields** — `(class_declaration name: (identifier) !type_parameters)`;
- **wildcards** — `(_)` any named node, `_` any node;
- **alternations** `[...]`, **quantifiers** `? * +`, **groups**, **anchors** `.` (immediate sibling / first child);
- **supertypes** — `(supertype)` or `supertype/subtype`;
- `(ERROR)` and `(MISSING)` for damaged parses.

Predicates ([3-predicates](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/3-predicates-and-directives.html)): `#eq?` / `#not-eq?` / `#any-eq?`, `#match?` / `#not-match?` / `#any-match?` (regex), `#any-of?`, `#is?` / `#is-not?`; directives `#set!`, `#select-adjacent!`, `#strip!`.

### What it cannot express

- **Predicates are not part of the C library.** The docs are explicit: *"Predicates and directives are not handled directly by the Tree-sitter C library"* — they are exposed structurally and **the binding must implement them**. The Rust crate and the WASM binding do; a Python consumer either uses `QueryCursor`'s predicate support or filters matches itself. This is the single biggest portability trap.
- **No cross-file linking.** A query is per-file and per-tree. Binding `(err:_console ...)` in file A to `(defun err:_console ...)` in file B is out of scope — that is graphify's `resolver_registry.py` / SCIP's job.
- **No computation.** You cannot derive a name, concatenate, count, or branch. `defun_header function_name: (package_lit)` gives you the whole `err:trap` text; splitting it into module + member needs code (or a regex predicate that only *filters*, never *transforms*).
- **No new edge kinds.** The vocabulary is definition/reference × a fixed kind list. There is no way to say "this is a `loads` edge from file A to file B".
- **Requires a grammar.** No grammar, no query.

### Maturity and Python availability

Very mature. Used by GitHub code navigation, and by [aider's repo map](https://aider.chat/2023/10/22/repomap.html), which "parses it with tree-sitter and runs language-specific tag queries (`.scm` files) to extract … `def` and `ref` tags", falling back to Pygments tokenisation when a grammar's tags query yields definitions only ([DeepWiki: aider repository mapping](https://deepwiki.com/Aider-AI/aider/4.1-repository-mapping-system), [`aider/repomap.py`](https://github.com/Aider-AI/aider/blob/3ec8ec5a/aider/repomap.py)).

Python: full support via [`py-tree-sitter`](https://tree-sitter.github.io/py-tree-sitter/). **Measured on this host**: the `graphifyy` pipx venv has `tree-sitter 0.25.2` exposing `Query`, `QueryCursor`, `QueryError`, `QueryPredicate` — i.e. the `QueryCursor(Query(lang, src)).captures(node)` API, not the pre-0.25 `language.query()` API. Any query-driven extractor must target `QueryCursor`.

CLI: `tree-sitter tags <file>` runs the tags query and prints name, role/kind, location, context and docstring.

---

## 3. tree-sitter-graph DSL and GitHub stack-graphs

The maximalist answer: a full DSL for constructing an arbitrary graph from a syntax tree.

Sources: [tree-sitter-graph repo](https://github.com/tree-sitter/tree-sitter-graph) · [DSL language reference on docs.rs](https://docs.rs/tree-sitter-graph/latest/tree_sitter_graph/reference/index.html) · [github/stack-graphs](https://github.com/github/stack-graphs) · [stack-graphs crate docs](https://docs.rs/stack-graphs/latest/stack_graphs/)

### What the definition file looks like

A `.tsg` file is a list of **stanzas**; each stanza is a tree-sitter query followed by a block of statements executed once per match ([docs.rs reference](https://docs.rs/tree-sitter-graph/latest/tree_sitter_graph/reference/index.html)):

```
global ROOT_NODE

(function_definition name: (identifier) @name) @func
{
  node def
  attr (def) kind = "function", symbol = (source-text @name)
  edge ROOT_NODE -> def
  attr (ROOT_NODE -> def) precedence = 10
  let n = (source-text @name)
  scan n {
    "^([a-z]+):(.*)$" {
      attr (def) module = $1, member = $2
    }
  }
}
```

Statements: `node`, `edge A -> B`, `attr (…) k = v`, `let` (immutable) / `var` + `set` (mutable), `scan` (regex against a string, with per-branch blocks and `$1` captures), `if` / `elif` / `else` with `some`/`none` on optional captures, `for x in list`, `print` (stderr).

Three variable kinds: **global** (injected from outside, `global name`), **local** (stanza-scoped), and **scoped** (`@node.var`) — attached to a syntax node and **persisting across stanzas**, which is how one stanza hands a graph node to another.

### Node / edge concepts it can express

Essentially anything: arbitrary node creation, arbitrary directed edges, arbitrary key/value attributes on both, regex-derived attribute values, conditionals, iteration, and cross-stanza wiring through scoped variables. This is the only system surveyed that can *construct a graph* declaratively rather than emit a flat tag list.

Layered on top, **stack-graphs** defines a name-resolution model — push-symbol / pop-symbol / scope / definition / reference nodes, resolved by simultaneously manipulating a **symbol stack** and a **scope stack** during path finding, with **incrementality** as the design goal: *"define the name resolution rules for an arbitrary programming language in a way that is efficient, incremental, and does not need to tap into existing build or program analysis tools"* ([github/stack-graphs](https://github.com/github/stack-graphs)). It is "heavily based on the *scope graphs* framework from Eelco Visser's group at TU Delft". The rules for a language are written as `.tsg` stanzas.

### What it cannot express / limitations

From the [docs.rs reference](https://docs.rs/tree-sitter-graph/latest/tree_sitter_graph/reference/index.html):

- **at most one edge between any given source/sink pair**;
- **an attribute cannot be redefined** on the same element;
- list comprehensions iterate only over *local* values, not scoped variables;
- `scan` requires a local value; conditional values must be local;
- unused captures must be named `@_foo`.

And structurally: it is not a general programming language — no user functions, no data structures beyond lists, no I/O.

### Maturity and Python availability

`tree-sitter-graph` is **Rust-only**; the repository lists a Rust crate, a language reference, and a VS Code extension — **no Python bindings**. `github/stack-graphs` was **archived by the owner on 9 September 2025** and is now read-only, with the note *"This repository is no longer supported or updated by GitHub"* ([github/stack-graphs](https://github.com/github/stack-graphs)).

**Verdict for graphify-lang**: the DSL is the right *idea* and the wrong *dependency*. Its statement vocabulary (`node` / `edge` / `attr` / `scan`) is worth reading as a design source for a future graphify rule format, but a Rust-only, partially-archived toolchain cannot be a runtime dependency of a Python package.

---

## 4. Python tree-sitter grammar distributions

### tree-sitter-language-pack

Sources: [repo README](https://github.com/Goldziher/tree-sitter-language-pack) · [PyPI](https://pypi.org/project/tree-sitter-language-pack/) · [full language list](https://docs.tree-sitter-language-pack.xberg.io/languages/)

| Property | Value |
|:---------|:------|
| Version | 1.16.2 (6 September 2026) |
| Grammars | **371 languages** |
| `requires-python` | **>= 3.10** |
| ABI | parsers bundled at **ABI 14**, backwards compatible with tree-sitter 0.21–0.26 |
| Wheels | macOS 10.12+ x86-64 and 11.0+ arm64; **Linux manylinux 2.34+ x86-64 and manylinux 2.34+ aarch64**; Windows x86-64 and arm64. Wheels are 2.1–2.4 MB; sdist 88.5 kB |
| License | **MIT** for the package. Grammar inclusion policy: *"Copyleft licenses (GPL, AGPL, LGPL, MPL) are not accepted"*; included grammars are "MIT, Apache-2.0, BSD, ISC, or similar" |
| API | `get_language()` returns a native `Language`; `get_parser()` returns a parser |

**aarch64 answer**: yes — `manylinux 2.34+ aarch64` wheels are published, which covers this Linux host. (Note that manylinux **2.34** implies glibc ≥ 2.34, i.e. Ubuntu 22.04+; older distros fall back to the sdist.)

**Grammars relevant to graphify-lang** (verified against the generated table in the README, whose columns are `Language | Repository | ABI | highlights | injections | locals | indents | folds | tags`):

| Language | Upstream | ABI | ships `tags.scm`? |
|:---------|:---------|:---:|:------------------|
| Commonlisp | [theHamsta/tree-sitter-commonlisp](https://github.com/theHamsta/tree-sitter-commonlisp) | 14 | **yes** |
| Markdown | [tree-sitter-grammars/tree-sitter-markdown](https://github.com/tree-sitter-grammars/tree-sitter-markdown) | 14 | no |
| YAML | [tree-sitter-grammars/tree-sitter-yaml](https://github.com/tree-sitter-grammars/tree-sitter-yaml) | 14 | no |
| TOML | [tree-sitter-grammars/tree-sitter-toml](https://github.com/tree-sitter-grammars/tree-sitter-toml) | 14 | no |
| Scheme | [6cdh/tree-sitter-scheme](https://github.com/6cdh/tree-sitter-scheme) | 14 | no |
| Emacs Lisp | [Wilfred/tree-sitter-elisp](https://github.com/Wilfred/tree-sitter-elisp) | 14 | yes |
| **AutoLISP** | — | — | **absent** |
| **DCL** (AutoCAD Dialog Control Language) | — | — | **absent** (the pack's only "D…C…L"-adjacent entry is `Devicetree`, an unrelated grammar) |

There is **no AutoLISP and no DCL tree-sitter grammar** anywhere I could find — a targeted search returned only `tree-sitter-commonlisp`, `tree-sitter-elisp` and `tree-sitter-clojure` in the Lisp family, and nothing AutoCAD-specific ([tree-sitter parser list](https://github.com/tree-sitter/tree-sitter/wiki/List-of-parsers)). This is load-bearing for graphify-lang: AutoLISP must either keep riding the Common Lisp grammar (which parses `err.lsp` with **zero ERROR nodes**, per the fork README) or get a hand-written parser. DCL has no grammar at all and is a regex/hand-parser candidate.

### tree-sitter-languages (the older package)

[grantjenks/py-tree-sitter-languages](https://github.com/grantjenks/py-tree-sitter-languages) / [PyPI](https://pypi.org/project/tree-sitter-languages/). **Unmaintained** — the grep-ast maintainers filed [`py-tree-sitter-languages is unmaintained`](https://github.com/Aider-AI/grep-ast/issues/7) and the ecosystem has migrated to `tree-sitter-language-pack`. Last release 1.10.2 (4 February 2024) does include aarch64 wheels, but it does not build on Python 3.13 ([writeup](https://mars-wangyang.medium.com/cannot-install-tree-sitter-languages-in-python-3-13-f123840d0cca)). **Do not use.**

### What graphify already pins

`pyproject.toml` pins ~25 individual `tree-sitter-<lang>` packages with tight upper bounds and `tree-sitter>=0.23.0,<0.26`. It does **not** depend on `tree-sitter-language-pack`. A language plugin that wants a grammar the core does not pin therefore declares its own dependency — which is exactly what the manifest's `grammar` / `extra` fields are for (fork `README.md`, manifest table).

---

## 5. Registry and rule formats from adjacent ecosystems

### 5.1 GitHub linguist `languages.yml`

Source: [`lib/linguist/languages.yml`](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml) · [CONTRIBUTING](https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md)

The purest example of a suffix→language registry. Required keys per language: `type` (`data` | `programming` | `markup` | `prose`), `ace_mode`, `extensions` (ASCII order, primary first), `filenames`, `language_id`, `tm_scope`. Optional: `aliases`, `codemirror_mode`, `codemirror_mime_type`, `color`, `fs_name`, `group`, `interpreters`, `wrap`.

```yaml
Common Lisp:
  type: programming
  tm_scope: source.commonlisp
  color: "#3fb68b"
  aliases: [lisp]
  extensions: [".lisp", ".asd", ".cl", ".l", ".lsp", ".ny", ".podsl", ".sexp"]
  interpreters: [lisp, sbcl, ccl, clisp, ecl]
  ace_mode: lisp
  language_id: 66

Markdown:
  type: prose
  aliases: [md, pandoc]
  extensions: [".md", ".livemd", ".markdown", ".mdown", …]
  filenames: [contents.lr]
  tm_scope: text.md
  wrap: true
  language_id: 222
```

**Note the collision that bites graphify-lang directly**: linguist assigns `.lsp` to *Common Lisp*, and graphify's `_DISPATCH` follows suit (`extract.py`: `".lsp": extract_commonlisp`). A language plugin claiming `.lsp` is therefore **overriding an existing mapping**, not adding a new one — the registry needs a documented precedence rule (see §9).

**Expresses**: file→language classification, aliases, grouping, prose/data/markup/programming typing.
**Cannot express**: anything about symbols, edges, or structure. Classification only.
**Python**: linguist is Ruby; `languages.yml` is just data and is widely re-consumed (e.g. by `identify`, `github-linguist` ports). Reading the *shape* costs nothing.

### 5.2 TextMate grammars

Source: [TextMate manual — Language Grammars](https://macromates.com/manual/en/language_grammars)

Root keys: `scopeName` (dot-separated, e.g. `source.python`), `fileTypes`, `firstLineMatch`, `foldingStartMarker` / `foldingStopMarker`, `patterns`, `repository`. Rules use `match` (single regex) or `begin`/`end` (paired, with backreferences from `begin` captures into `end`), plus `name`, `contentName`, `captures` / `beginCaptures` / `endCaptures`, `include` (`$self`, `#repoRule`, or another grammar's `source.php`), and nested `patterns`.

```
{ scopeName = 'source.simple';
  fileTypes = ( 'sim' );
  patterns = (
    { name = 'keyword.control'; match = '\b(if|while|return)\b'; },
    { name = 'string.quoted.double'; begin = '"'; end = '"';
      patterns = ( { name = 'constant.character.escape'; match = '\\\\.'; } ); }
  ); }
```

Scope names come from eleven root groups: `comment`, `constant`, `entity`, `invalid`, `keyword`, `markup`, `meta`, `storage`, `string`, `support`, `variable`.

**Expresses**: lexical classification with nesting and language embedding.
**Cannot express**: multi-line `match` regexes (only `begin`/`end` spans lines), cross-file symbols, semantic analysis, or genuine recursion beyond `$self`. **It is a highlighter, not an extractor** — there is no notion of a definition, a reference, or an edge. Relevant only as evidence that scope-string vocabularies are a workable classification device, and as the thing linguist's `tm_scope` points at.

### 5.3 Semgrep rule YAML

Source: [Semgrep rule syntax](https://docs.semgrep.dev/writing-rules/rule-syntax)

Required: `id`, `message`, `severity` (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), `languages`, and exactly one of `pattern` / `patterns` / `pattern-either` / `pattern-regex`.

```yaml
rules:
  - id: insecure-crypto
    languages: [python]
    severity: HIGH
    message: "Insecure hashing detected"
    pattern-either:
      - pattern: hashlib.md5(...)
      - pattern: hashlib.sha1(...)
```

Operators: `pattern`, `patterns` (AND), `pattern-either` (OR), `pattern-not`, `pattern-inside`, `pattern-not-inside`, `pattern-regex` (PCRE2), `metavariable-regex`, `metavariable-pattern`, `metavariable-comparison`, `focus-metavariable`.

**Expresses**: composable boolean predicates over syntax with containment constraints (`inside`/`not-inside`) and metavariable binding — a genuinely good model for "find X but only within Y".
**Cannot express**: graph construction. Semgrep emits findings, not nodes and edges. And its matcher is not reusable: patterns are parsed by Semgrep's own per-language front-ends. For languages it does not support it offers **generic mode** (structure-aware matching on arbitrary text) and **regex mode** (line-oriented, for INI/config files) — a useful precedent for a two-tier "grammar or regex" manifest.
**Python**: the CLI is Python-packaged (`pip install semgrep`) but the engine is OCaml; not embeddable as a library.

### 5.4 SCIP, LSIF and Kythe — the output vocabularies

These are not language *definition* formats; they are the *target* vocabularies. They matter because they tell you which edge kinds are worth having.

**SCIP** ([sourcegraph/scip](https://github.com/sourcegraph/scip), [`scip.proto`](https://github.com/sourcegraph/scip/blob/main/scip.proto)) — protobuf: `Index` → `Document` → `Occurrence` + `SymbolInformation`. Symbols are *strings* with a formal grammar:

```
<symbol>     ::= <scheme> ' ' <package> ' ' (<descriptor>)+ | 'local ' <local-id>
<package>    ::= <manager> ' ' <package-name> ' ' <version>
<descriptor> ::= <namespace> | <type> | <term> | <method> | <type-parameter> | <parameter> | <meta> | <macro>
<namespace>  ::= <name> '/'      <type>   ::= <name> '#'
<term>       ::= <name> '.'      <method> ::= <name> '(' (<disambiguator>)? ').'
<meta>       ::= <name> ':'      <macro>  ::= <name> '!'
```

`SymbolRole` is a **bitset**: `Definition` 0x1, `Import` 0x2, `WriteAccess` 0x4, `ReadAccess` 0x8, `Generated` 0x10, `Test` 0x20, `ForwardDefinition` 0x40. `Relationship` carries `symbol` plus booleans `is_reference`, `is_implementation`, `is_type_definition`, `is_definition`. Indexers exist for Java/Scala/Kotlin, TypeScript, Rust, C/C++, Ruby, **Python (`scip-python`)**, C#, Dart, PHP.

**LSIF 0.6** ([spec](https://microsoft.github.io/language-server-protocol/specifications/lsif/0.6.0/specification/)) — JSON-lines vertex/edge graph. Vertices: `document`, `range`, `resultSet`, `hoverResult`, `definitionResult`, `referenceResult`, `implementationResult`, `moniker`, `project`. Edges: `contains`, `next`, `item`, `textDocument/definition`, `textDocument/references`, `moniker`, `attach`. Monikers carry `scheme` / `identifier` / `kind` (export|import|local) / `unique` for cross-project identity. SCIP is Sourcegraph's successor to LSIF; the LSIF spec itself makes no claim about being superseded.

**Kythe** ([schema](https://kythe.io/docs/schema/)) — the richest vocabulary. Nodes: `record`, `package`, `interface`, `function`, `variable`, `constant`, `tapp`, `tvar`, `tbuiltin`, `talias`, `file`, `anchor`, `doc`, `name`, `diagnostic`, `macro`, `lookup`, `sum`, `meta`. Edges (all `/kythe/edge/`): `defines`, `defines/binding`, `ref`, `ref/call`, `ref/call/direct`, `ref/doc`, `typed`, `param.N`, `childof`, `extends`, `overrides`, `documents`. Identity is a five-field **VName** (`signature`, `corpus`, `root`, `path`, `language`). Crucially, *"the schema is documentation-driven, not code-based"* — it is narrative prose plus a conformance test suite, which is itself a lesson: a vocabulary can be specified and tested without a DSL.

**Take-away for graphify-lang**: `defines/binding` vs `ref/call` vs `childof` vs `typed` is the minimal useful edge taxonomy, and SCIP's role *bitset* is the right shape for a `roles = ["definition", "read"]` manifest field. graphify's own edge kinds (`references`, `calls`, …) should be declared in the manifest against this vocabulary rather than invented per plugin.

---

## 6. Rule-based graph extraction from prose

### 6.1 Akoma Ntoso / LegalDocML — the structural model

Source: [OASIS Akoma Ntoso v1.0 Part 1: XML Vocabulary](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/cs01/part1-vocabulary/akn-core-v1.0-cs01-part1-vocabulary.html) · [LegalDocML TC](https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=legaldocml) · [Wikipedia](https://en.wikipedia.org/wiki/Akoma_Ntoso)

Named hierarchical containers: `book`, `tome`, `part`, `chapter`, `section`, `paragraph`, `article`, `clause`, `division`, `level`, `list`, `subtitle`, `subpart`, `subchapter`, `subsection`, `subparagraph`, `subclause`, `sublist`, `point`, `indent`, `alinea` — plus a generic `<hcontainer name="…">` escape hatch when none fits. **This list is the answer to "what are the node kinds of a prose language."**

Every container follows the same three-part shape:

```xml
<section eId="sec_4">
  <num>4</num>
  <heading>Context of the organization</heading>
  <content>
    <p>The organization shall determine external issues, see <ref href="#sec_4__subsec_2">4.2</ref>.</p>
  </content>
</section>
```

Cross-references: `<ref href="…">` (single), `<mref>` (multiple), `<rref>` (a range, e.g. articles 3–5). Identity attributes: `eId` (expression-level), `wId` (work-level), `GUID`. A Python parser exists — **[bluebell](https://github.com/laws-africa/bluebell)**, "a generic Akoma Ntoso 3 parser" from Laws.Africa, whose [text-extraction tutorial](https://developers.laws.africa/tutorial/module-3-text-extraction-for-search-and-analysis/basics-of-text-extraction) documents XPath-based extraction against the `http://docs.oasis-open.org/legaldocml/ns/akn/3.0` namespace.

**Expresses**: hierarchy (`childof`), typed cross-references (`ref`/`mref`/`rref`), stable identity per fragment.
**Cannot express**: it is a *markup* standard — it presumes someone already segmented the document. Getting from a PDF of ISO 9001 to tagged AKN is the hard part, and AKN says nothing about how.

### 6.2 Requirement-ID extractors

**sphinx-needs** ([configuration](https://sphinx-needs.readthedocs.io/en/latest/configuration.html)) is the most manifest-like of the three, and the closest existing analogue to what graphify-lang wants for prose. Node types and edge types are both **declared in config**:

```python
needs_types = [
    dict(directive="req",  title="Requirement",   prefix="R_", color="#BFD8D2", style="node"),
    dict(directive="spec", title="Specification", prefix="S_", color="#FEDCD2", style="node"),
]
needs_extra_links = [
    {"option": "triggers", "incoming": "is triggered by", "outgoing": "triggers", "style": "#00AA00"},
]
needs_extra_options = ["priority", "verification_method"]
```

```rst
.. req:: System shall validate input
   :id: REQ_001
   :status: open
   :tags: security, validation
   :triggers: TEST_001
```

`needs_types` is literally a node-kind table (directive name, display title, ID prefix); `needs_extra_links` is literally an edge-kind table with directional labels. **This is the shape to copy for prose rules.**

**StrictDoc** ([user guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html)) uses a **textX** grammar over a `.sdoc` text format, and lets a document declare its own schema in a `[GRAMMAR]` block:

```
[REQUIREMENT]
UID: REQ-001
TITLE: Requirements management
STATEMENT: >>>
StrictDoc shall enable requirements management.
<<<
RELATIONS:
- TYPE: Parent
  VALUE: REQ-002
```

```
[GRAMMAR]
ELEMENTS:
- TAG: CUSTOM_ELEMENT
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: True
  RELATIONS:
  - TYPE: Parent
    ROLE: Refines
```

Relation types are `Parent`, `Child`, `File`, optionally with a `ROLE` (e.g. `Refines`). Source-code traceability uses `@relation` markers in code comments, with "language-aware parsing of source code". *"Requirements, tests and functions become individual nodes in the traceability graph and are connected by their stable IDs."* StrictDoc is Python, actively developed, and explicitly the successor to Doorstop.

**Doorstop** ([item reference](https://github.com/doorstop-dev/doorstop/blob/develop/docs/reference/item.md)) stores one YAML file per item:

```yaml
active: true
derived: false
normative: true
level: 1.2.3
header: Input validation
text: |
  The system shall validate all external input.
links:
- REQ001: avwblqPimDJ2OgTrRCXxRPN8FQhUBWqPIXm7kSR95C4=
- REQ002: null
references:
- path: tests/test1.cpp
  type: file
  sha: 28c1655…
reviewed: null
```

`links` is a list of parent UIDs each carrying the parent's SHA256 fingerprint, so a changed parent invalidates the link — a neat trick worth stealing for stale-edge detection. Document config `.doorstop.yml` holds `prefix`, `sep`, `digits`, `parent`, which is how UIDs like `REQ001` are minted and how documents chain into a hierarchy. Python, mature, but in maintenance relative to StrictDoc.

### 6.3 Clause and cross-reference extraction from unstructured standards

This is the least mature area — there is no `tags.scm` for prose. What exists:

- **Cross-reference extraction as an NLP task**: "Identifying external cross-references using natural language processing" ([ACM CSSE 2022](https://dl.acm.org/doi/abs/10.5555/3432601.3432620)) combines NLP, pattern recognition and web scraping, using "semantic cues for identifying cross-references, grammatical structures for supporting various combinations of word roles in a sentence, standards for validating cross-references".
- **Document-navigator graphs over standards**: patented approaches index section IDs in a graph database, capturing cross-reference relationships and parent-child hierarchy "aligning with standard naming and numbering conventions" ([US 12,411,896](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12411896), [US 11,763,321 "extracting requirements from regulatory content"](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11763321)).
- **"Shall"-statement extraction**: [ARSENAL](https://arxiv.org/pdf/1403.3142) (automatic requirements specification extraction from natural language) and [autonomous requirements specification processing using NLP](https://arxiv.org/pdf/1407.6099) are the reference academic pipelines; both parse sentences and classify extracted terms as function / entity / attribute.
- **Practical Python**: spaCy's `Matcher` for pattern rules over token sequences is the standard tool.

**Reality check**: for numbered technical standards, `^(\d+(?:\.\d+)*)\s+(.+)$` for headings plus `\b(?:Clause|Section|§)\s*(\d+(?:\.\d+)*)\b` for references gets you most of the graph. The academic and patented work is about the residual — implicit references, "the preceding paragraph", defined-term resolution. **A regex-rule tier in the manifest is sufficient and proportionate here**; anything more wants a Python callable.

### 6.4 Markdown / reStructuredText section graphs

Well-trodden and — importantly — **graphify already does it**. Upstream's README documents that `.md .mdx .qmd .html .txt .rst .yaml .yml` are handled as Docs, and that "markdown `[text](./other.md)` links and `[[wikilinks]]` become `references` edges between docs" (`docs/UPSTREAM-README.md:350`), with H2/H3 headings becoming nodes. `_DISPATCH` routes `.md`, `.mdx`, `.qmd` and `.skill` to `extract_markdown`.

The wider ecosystem does the same thing: [Kwipu](https://github.com/benmaster82/Kwipu) extracts entity-relation triples from wikilinks and YAML frontmatter; the usual Python route is `markdown-it-py` to walk a vault into a graph store. Nothing here is novel.

**Consequence for the recommendation**: the prose rule tier should be modelled on `extract_markdown`'s existing behaviour (heading→node, link→edge) generalised to *configurable* heading patterns and reference patterns, not designed from scratch.

---

## 7. Measurement: what this means for AutoLISP concretely

The fork's `README.md` establishes that `extract_commonlisp` yields **1 node, 0 edges** for `src/core/err.lsp` (27 `defun` forms), because `_handle_defun_node` reads the name as the first `sym_lit` child of `defun_header`, and AutoLISP names like `err:trap` parse as `package_lit`.

I re-ran that against the **query** layer instead of the walker. Instrument: `/tmp/tq.py`, executed with `~/.local/share/pipx/venvs/graphifyy/bin/python` (`tree-sitter 0.25.2`, `tree_sitter_commonlisp`), corpus `~/repos/autolithp/src/core/err.lsp`.

| Query | `definition.function` | `reference.call` | `name` captures |
|:------|----------------------:|-----------------:|----------------:|
| `(defun_header function_name: (sym_lit) @name) @definition.function` — the upstream `tags.scm` line, verbatim | **0** | — | 0 |
| `(defun_header function_name: [(sym_lit) (package_lit)] @name) @definition.function` + `(list_lit . [(sym_lit) (package_lit)] @name) @reference.call` | **27** | **298** | 325 |

Sample names recovered: `/`, `=`, `>`, `T`, `and`, `assoc`, `caller`, `caller-sym`, `car`, `cdr`, `command`, `cond`, …

Two conclusions:

1. **The entire AutoLISP definition/call gap closes with a one-token alternation** — `(sym_lit)` → `[(sym_lit) (package_lit)]` — expressed in a *data file*, not code. The upstream `tags.scm` already uses exactly that alternation in its call-exclusion patterns; it just does not use it in the definition pattern.
2. Therefore **a tree-sitter query rule type is not a nice-to-have in the manifest — it is the single highest-value rule type**, and it validates the whole declarative premise on the fork's own first target language.

Caveat, and it is a real one: 298 `reference.call` captures include every built-in (`car`, `cdr`, `cond`, `and`). Upstream already has the machinery for this — `_LANGUAGE_BUILTIN_GLOBALS` in `graphify/extractors/base.py:13`, "the denylist that stops constructor-like built-ins becoming god nodes" (fork `README.md`). The manifest needs a `builtins` / denylist field, and the AutoLISP package must supply the ~700-symbol AutoLISP built-in list.

---

## 8. Cross-cutting comparison

| System | Definition artefact | Node kinds | Edge kinds | Cross-file | Needs a grammar | Python | Maturity |
|:-------|:--------------------|:-----------|:-----------|:-----------|:----------------|:-------|:---------|
| ctags optlib | `.ctags` flag file | user-defined (`--kinddef`) | roles only, source implicit | no | no | subprocess + JSON-lines | mature |
| tree-sitter `tags.scm` | `.scm` query file | fixed vocabulary | definition/reference | no | **yes** | native (`py-tree-sitter`) | mature |
| tree-sitter-graph | `.tsg` stanza file | arbitrary | arbitrary, attributed | via scoped vars | **yes** | **none** | active (Rust) |
| stack-graphs | `.tsg` + crate | name-resolution nodes | symbol/scope stacks | **yes**, incremental | **yes** | none | **archived 2025-09-09** |
| linguist `languages.yml` | YAML map | n/a | n/a | n/a | no | data only | mature |
| TextMate grammar | plist/JSON | scope strings | none | no | no | via `vscode-textmate` ports | mature, frozen |
| Semgrep rules | YAML | findings | none | limited | its own | CLI only | mature |
| SCIP | protobuf output | symbol descriptors | role bitset + `Relationship` | **yes** | indexer-dependent | `scip-python` | active |
| LSIF | JSON-lines output | vertices | labelled edges | via monikers | indexer-dependent | yes | superseded in practice |
| Kythe | prose schema + tests | ~19 node kinds | ~12 edge kinds | **yes** (VNames) | indexer-dependent | yes | mature, niche |
| sphinx-needs | Python config + RST | `needs_types` | `needs_extra_links` | yes (by ID) | no | **native** | active |
| StrictDoc | textX `.sdoc` + `[GRAMMAR]` | user-defined elements | `Parent`/`Child`/`File` + roles | yes (by UID) | no | **native** | active |
| Doorstop | per-item YAML | documents/items | `links` with fingerprints | yes (by UID) | no | **native** | mature |
| Akoma Ntoso | XML instance + XSD | ~20 hierarchy elements | `ref`/`mref`/`rref` | yes (`eId`) | no | `bluebell` | OASIS standard |

---

## 9. Recommendation for graphify-lang

### 9.1 The shape of the decision

The fork's `README.md` already specifies a manifest with eight fields (`name`, `suffixes`, `extract`, `grammar`, `extra`, `resolver`, `hook_suffixes`, `fixture`), and the core already has `LanguageConfig` (`graphify/extractors/models.py:14-57`) — a dataclass with ~20 declarative fields (`class_types`, `function_types`, `call_types`, `name_field`, `body_field`, `call_function_field`, …) plus five `Callable` escape hatches (`import_handler`, `resolve_function_name_fn`, `sanitize_symbol_name_fn`, `extra_walk_fn`). **The declarative model already exists in Python; what is missing is a serialisable form of it plus a rule tier that can express things `LanguageConfig` cannot** (AutoLISP is the proof: its names are `package_lit`, its definer is a dedicated node type, so it does not fit `LanguageConfig` — fork `README.md`).

So the manifest should be a **file-backed superset of `LanguageConfig`**, not a new parallel universe. Two hard constraints follow from the survey:

- **Do not invent a rule DSL.** `tags.scm` is the industry-standard declarative extraction rule format, grammars already ship the files, GitHub and aider both consume them, and §7 measured that it fixes AutoLISP outright. Inventing a graphify-specific query language would be strictly worse and strictly more work.
- **Do not depend on tree-sitter-graph / stack-graphs.** Rust-only, no Python bindings, and the stack-graphs half is archived.

### 9.2 Format: TOML

| Criterion | TOML | YAML | JSONC |
|:----------|:-----|:-----|:------|
| Parser in graphify today | **yes** — `tomllib` (stdlib ≥3.11) and `tomli>=2.0.1` already a dependency for 3.10 (`pyproject.toml:18`) | **no** — and `graphify/ingest.py:23` states *"We intentionally do not depend on PyYAML (not in pyproject deps)"* | no stdlib parser; needs `json5`/`commentjson` |
| Comments | yes | yes | yes |
| Multi-line regex without escaping | yes — literal `'''…'''` strings | yes — block scalars, but `\` and indentation rules bite | no — JSON escaping doubles every `\` |
| Ambiguity hazards | none material | the Norway problem, `1.10` → float, tabs illegal (Doorstop's docs warn to quote `'1.10'`) | trailing-comma / comment dialects vary |
| Repeated-block ergonomics (`[[rule]]`) | native array-of-tables | native list of maps | verbose |
| Matches project convention | **yes** — `pyproject.toml` is the project's own config | no | no |

**Choose TOML.** The decisive fact is not aesthetic: adding YAML means adding PyYAML to a project that has explicitly refused it, and JSONC means adding a parser for no benefit. TOML is free. `requires-python = ">=3.10"` means the manifest loader must be `try: import tomllib / except ImportError: import tomli as tomllib` — three lines, and the dependency is already declared.

Ship the manifest as `graphify_lang.toml` inside the language package, discovered via `importlib.resources`, with the Python entry point providing only the *pointer* (name → package) as the fork's `README.md` design goal 1 already proposes.

### 9.3 Proposed data model

```toml
# graphify_lang.toml — AutoLISP language plugin
schema = 1

[language]
name          = "autolisp"
type          = "programming"        # linguist's vocabulary: programming|markup|data|prose
suffixes      = [".lsp", ".mnl"]
overrides     = [".lsp"]             # explicit: claims a suffix graphify already maps
filenames     = ["acaddoc.lsp", "acad.lsp"]
hook_suffixes = [".lsp"]             # feeds cli.py _HOOK_SOURCE_EXTS
priority      = 100                  # higher wins when two plugins claim a suffix

[grammar]
kind      = "tree-sitter"            # tree-sitter | regex | prose | python
module    = "tree_sitter_commonlisp" # the pip module providing language()
language_fn = "language"
extra     = "autolisp"               # -> pip install "graphifyy[autolisp]"; feeds _EXTRA_FOR_EXTENSION

[extract]
builtins_file = "data/autolisp-builtins.txt"   # feeds base.py _LANGUAGE_BUILTIN_GLOBALS
queries       = ["queries/tags.scm"]           # tree-sitter tag queries, in order
```

```toml
# --- rule tier 1: tree-sitter queries (preferred; requires a grammar) ---
# Either point at .scm files (above) or inline them:

[[rule]]
kind  = "query"
node  = "function"                    # graphify node kind
query = '''
(defun_header function_name: [(sym_lit) (package_lit)] @name) @definition.function
'''
name_capture = "@name"
doc_capture  = "@doc"

[[rule]]
kind  = "query"
edge  = "calls"                       # graphify edge kind
query = '''
(list_lit . [(sym_lit) (package_lit)] @name) @reference.call
'''
name_capture = "@name"
exclude_builtins = true               # apply the builtins denylist to this rule
```

```toml
# --- rule tier 2: regex (no grammar needed; the DCL / prose fallback) ---

[[rule]]
kind    = "regex"
suffix  = ".dcl"
node    = "dialog"
pattern = '''^\s*([A-Za-z_][\w-]*)\s*:\s*dialog\b'''
name_group = 1
scope   = "push"                      # push | pop | ref | set | clear  (ctags optlib vocabulary)
exclusive = true

[[rule]]
kind    = "regex"
suffix  = ".dcl"
edge    = "includes"
pattern = '''^\s*:\s*([A-Za-z_][\w-]*)\s*\{'''
name_group = 1
scope   = "ref"                       # source endpoint = current scope stack top
```

```toml
# --- rule tier 3: prose sections (sphinx-needs / Akoma Ntoso shape) ---

[[rule]]
kind        = "section"
suffix      = ".md"
node        = "clause"
number_pattern = '''^(#{1,6})\s+(\d+(?:\.\d+)*)\s+(.*)$'''
number_group   = 2                    # "4.2.1" -> hierarchical id, parent = "4.2"
title_group    = 3
hierarchy      = "dotted-number"      # dotted-number | heading-depth | akn-container

[[rule]]
kind    = "reference"
suffix  = ".md"
edge    = "cross-references"
pattern = '''\b(?:Clause|Section|§)\s*(\d+(?:\.\d+)*)\b'''
target_group  = 1
target_kind   = "clause"              # resolve against nodes of this kind, by number
target_scope  = "corpus"              # file | corpus

[[rule]]
kind    = "requirement"
suffix  = ".md"
node    = "requirement"
id_pattern     = '''\b(REQ-\d{3,})\b'''
modal_pattern  = '''\b(shall|must|shall not)\b'''   # "shall" statement detection
edge_to_section = "belongs-to"
```

```toml
# --- rule tier 4: python escape hatch (always available) ---

[extract.python]
extractor = "graphify_lang_autolisp.extract:extract_autolisp"   # Callable[[Path], dict]
resolver  = "graphify_lang_autolisp.resolve:AutolispResolver"   # LanguageResolver
# fine-grained hooks mirroring LanguageConfig's Callable fields:
resolve_function_name = "graphify_lang_autolisp.names:split_package_lit"
sanitize_symbol_name  = "graphify_lang_autolisp.names:normalise"
```

```toml
# --- vocabulary declaration (SCIP/Kythe-derived; keeps edge kinds honest) ---

[[node_kind]]
name = "function"
scip_descriptor = "method"            # SCIP <method> ::= <name> '(' ').'
label_parens = true                   # mirrors LanguageConfig.function_label_parens

[[edge_kind]]
name = "calls"
inverse = "called-by"                 # sphinx-needs incoming/outgoing shape
kythe = "/kythe/edge/ref/call"
roles = ["read"]                      # SCIP SymbolRole bitset names
```

### 9.4 Field reference

| Field | Source of the idea | Purpose |
|:------|:-------------------|:--------|
| `schema` | every versioned config format | forward compatibility; refuse unknown majors |
| `language.name` / `.type` / `.suffixes` / `.filenames` | [linguist `languages.yml`](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml) | registry key + classification |
| `language.overrides` / `.priority` | **new, forced by `.lsp`** | `.lsp` already maps to `extract_commonlisp` (`extract.py` `_DISPATCH`); a claim must be explicit, and two plugins claiming one suffix must resolve deterministically |
| `language.hook_suffixes` | fork `README.md` manifest table | `cli.py:71` `_HOOK_SOURCE_EXTS` |
| `grammar.kind` | Semgrep's grammar/generic/regex tiering | selects the rule engine |
| `grammar.module` / `.language_fn` / `.extra` | `LanguageConfig.ts_module`, `_EXTRA_FOR_EXTENSION` | grammar import + install hint |
| `extract.builtins_file` | `base.py:13` `_LANGUAGE_BUILTIN_GLOBALS` | stops `car`/`cdr` becoming god nodes (§7 caveat) |
| `[[rule]] kind="query"` | [tree-sitter tags](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html) | **the primary rule type** |
| `[[rule]] kind="regex"` + `scope` | [ctags optlib](https://docs.ctags.io/en/latest/optlib.html) `{scope=push\|pop\|ref}`, `{exclusive}` | grammar-less languages (DCL) |
| `[[rule]] kind="section"` / `"reference"` | [Akoma Ntoso](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/cs01/part1-vocabulary/akn-core-v1.0-cs01-part1-vocabulary.html) `num`/`heading`/`ref` | prose: standards, legislation, manuals |
| `[[rule]] kind="requirement"` | [sphinx-needs](https://sphinx-needs.readthedocs.io/en/latest/configuration.html), [StrictDoc](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html), [Doorstop](https://github.com/doorstop-dev/doorstop/blob/develop/docs/reference/item.md) | REQ-IDs and "shall" statements |
| `[extract.python]` | `LanguageConfig`'s five `Callable` fields | escape hatch — AutoLISP needs it today |
| `[[node_kind]]` / `[[edge_kind]]` | [Kythe schema](https://kythe.io/docs/schema/), [SCIP `SymbolRole`](https://github.com/sourcegraph/scip/blob/main/scip.proto), sphinx-needs `needs_extra_links` | declared vocabulary with inverse names, so plugins cannot invent divergent edge names |

### 9.5 Sequencing (what to build, in order)

1. **Manifest loader + registry + `[language]` block only.** Suffix registration into `_DISPATCH` / `CODE_EXTENSIONS` / `_WATCHED_EXTENSIONS` / `_HOOK_SOURCE_EXTS` via one lookup each, exactly as the fork `README.md` proposes. Rule tiers not yet parsed. This is the generic, upstreamable commit.
2. **`kind="query"` rules + `builtins_file`.** One engine, driven by `QueryCursor(Query(lang, src)).captures(...)` (measured API on `tree-sitter 0.25.2`), mapping the `@definition.*` / `@reference.*` vocabulary onto graphify's node/edge schema. §7 shows this alone fixes AutoLISP.
3. **`[extract.python]` escape hatch.** Needed anyway for the `package_lit` → module/member split and the `(args / locals)` separator, neither of which a query can compute.
4. **`kind="regex"` rules with the ctags scope stack.** Unlocks DCL, and any future grammar-less language.
5. **Prose tiers (`section` / `reference` / `requirement`).** Last, because graphify's `extract_markdown` already covers the common case and the incremental value is standards/legislation specifically.

### 9.6 Things to explicitly *not* do

- **Do not write a graphify query DSL.** `tags.scm` exists, is standard, and is already shipped by the grammars.
- **Do not depend on `tree-sitter-graph`, `stack-graphs`, `ctags`, `semgrep`, or `tree-sitter-languages`.** Rust-only, archived, non-Python-runtime, non-embeddable, and unmaintained respectively.
- **Do not add PyYAML.** `graphify/ingest.py:23` records a deliberate decision; TOML is already a dependency.
- **Do not attempt cross-file name resolution in the manifest.** That is what `resolver_registry.py` (`LanguageResolver.resolve(per_file, all_nodes, all_edges)`) is for, and it is a Python interface by design. SCIP/Kythe/stack-graphs all treat resolution as code, not config.
- **Do not model `tree-sitter-language-pack` as a dependency of the core.** It is 371 grammars at MIT with manylinux 2.34 aarch64 wheels, and it is a fine *optional extra* for a plugin — but graphify pins individual grammar packages, and swapping that policy is an upstream argument, not a fork change.

---

## 10. Source index

**ctags**: [optlib guide](https://docs.ctags.io/en/latest/optlib.html) · [`ctags-optlib(7)`](https://docs.ctags.io/en/latest/man/ctags-optlib.7.html) · [`docs/optlib.rst`](https://github.com/universal-ctags/ctags/blob/master/docs/optlib.rst) · [`optlib/cmake.ctags`](https://github.com/universal-ctags/ctags/blob/master/optlib/cmake.ctags) · [`ctags-json-output(5)`](https://docs.ctags.io/en/latest/man/ctags-json-output.5.html) · [tags file format](https://docs.ctags.io/en/latest/output-tags.html)

**tree-sitter**: [Code Navigation](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html) · [docs source](https://github.com/tree-sitter/tree-sitter/blob/master/docs/src/4-code-navigation.md) · [Query syntax](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html) · [Predicates](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/3-predicates-and-directives.html) · [py-tree-sitter](https://tree-sitter.github.io/py-tree-sitter/) · [parser list](https://github.com/tree-sitter/tree-sitter/wiki/List-of-parsers) · [tree-sitter-commonlisp](https://github.com/tree-sitter-grammars/tree-sitter-commonlisp)

**tree-sitter-graph / stack-graphs**: [repo](https://github.com/tree-sitter/tree-sitter-graph) · [DSL reference](https://docs.rs/tree-sitter-graph/latest/tree_sitter_graph/reference/index.html) · [github/stack-graphs (archived)](https://github.com/github/stack-graphs) · [stack-graphs crate](https://docs.rs/stack-graphs/latest/stack_graphs/)

**Python grammar packs**: [tree-sitter-language-pack](https://github.com/Goldziher/tree-sitter-language-pack) · [PyPI](https://pypi.org/project/tree-sitter-language-pack/) · [language list](https://docs.tree-sitter-language-pack.xberg.io/languages/) · [py-tree-sitter-languages (unmaintained)](https://github.com/grantjenks/py-tree-sitter-languages) · [grep-ast issue #7](https://github.com/Aider-AI/grep-ast/issues/7)

**Registries and rule formats**: [linguist languages.yml](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml) · [TextMate grammars](https://macromates.com/manual/en/language_grammars) · [Semgrep rule syntax](https://docs.semgrep.dev/writing-rules/rule-syntax)

**Symbol vocabularies**: [SCIP](https://github.com/sourcegraph/scip) · [`scip.proto`](https://github.com/sourcegraph/scip/blob/main/scip.proto) · [LSIF 0.6](https://microsoft.github.io/language-server-protocol/specifications/lsif/0.6.0/specification/) · [Kythe schema](https://kythe.io/docs/schema/)

**Prose / requirements**: [Akoma Ntoso v1.0 Part 1](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/cs01/part1-vocabulary/akn-core-v1.0-cs01-part1-vocabulary.html) · [LegalDocML TC](https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=legaldocml) · [bluebell parser](https://github.com/laws-africa/bluebell) · [Laws.Africa text extraction](https://developers.laws.africa/tutorial/module-3-text-extraction-for-search-and-analysis/basics-of-text-extraction) · [sphinx-needs configuration](https://sphinx-needs.readthedocs.io/en/latest/configuration.html) · [StrictDoc user guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html) · [Doorstop item reference](https://github.com/doorstop-dev/doorstop/blob/develop/docs/reference/item.md) · [ACM: identifying external cross-references with NLP](https://dl.acm.org/doi/abs/10.5555/3432601.3432620) · [ARSENAL](https://arxiv.org/pdf/1403.3142) · [NLP requirements processing](https://arxiv.org/pdf/1407.6099)

**aider repo map**: [Building a better repository map with tree sitter](https://aider.chat/2023/10/22/repomap.html) · [`aider/repomap.py`](https://github.com/Aider-AI/aider/blob/3ec8ec5a/aider/repomap.py) · [DeepWiki](https://deepwiki.com/Aider-AI/aider/4.1-repository-mapping-system)

**Local measurements** (this host, 2026-09-08): `/tmp/tq.py` run with `~/.local/share/pipx/venvs/graphifyy/bin/python` against `~/repos/autolithp/src/core/err.lsp`; `pyproject.toml`, `graphify/extractors/models.py`, `graphify/ingest.py`, `graphify/extract.py` read from `/home/p4ndr/repos/graphify-lang` at `a5dcc70`.
