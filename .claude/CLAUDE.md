# CLAUDE.md

Project instructions for Claude Code in the `graphify-lang` fork.

## Output discipline (MUST — inherited, not overridable)

The Two-Sentence Rule in `$CLAUDE_HOME/PROMPT-BASE.md` §Output discipline
applies in this repo and outranks every reporting or verbosity instruction
here. Every user-facing turn: at most two short sentences plus one optional
table. Subagent reports are compressed before any of it reaches the user;
detail goes to a file, and you report the path.

## What this repo is

A fork of `Graphify-Labs/graphify` (remote `upstream`, default branch `v8`)
that adds a language-extension layer so a language can be registered from a
package outside `graphify/extract.py`. First target: AutoLISP (`.lsp`,
`.dcl`, `.mnl`). `README.md` is the fork's own document; upstream's README is
at `docs/UPSTREAM-README.md`.

## Authoritative documents

- **Core pipeline**: upstream's `ARCHITECTURE.md` and `AGENTS.md` stay
  authoritative. `ARCHITECTURE.md` is test-pinned by
  `tests/test_architecture_doc.py`, which imports every symbol it names.
- **Extractor split**: `graphify/extractors/MIGRATION.md`. Its invariants
  (lines 36-51) hold here: no import of `graphify.extract` from inside
  `graphify/extractors/`, facade re-exports kept, one language per PR.
- **Fork intent, design, roadmap**: `README.md`.

## Tracking upstream

- `v8` mirrors `upstream/v8` and only ever fast-forwards. Work on branches
  off `v8`.
- Update with `git fetch upstream && git rebase upstream/v8`. Rebase, never
  merge.
- Never edit an existing language extractor, `graphify/extractors/engine.py`,
  or `graphify/extractors/resolution.py`. Never add a suffix by hand to
  `_DISPATCH` (`graphify/extract.py:5630`), `CODE_EXTENSIONS`
  (`graphify/detect.py:44`), or `_HOOK_SOURCE_EXTS` (`graphify/cli.py:71`);
  the registry lookup is the only permitted change to those tables.
- Generic registry work is meant to go upstream; keep it in commits separate
  from AutoLISP-specific work.

## Verification

- `pytest tests/ -q` must exit 0 with no upstream test file edited.
- Measure, do not assert. A claim about extractor output names the call
  that produced it (`extract_commonlisp(Path(...))`) and the corpus
  (`~/repos/autolithp`); a claim about a parse names the grammar version.
- The user's `graphify` on `PATH` (and both MCP servers) runs this fork from
  the pipx venv `~/.local/share/pipx/venvs/graphifyy`, installed from a pinned
  wheel of a release tag (`README.md`, 'Installing the fork'). Develop and test
  in the repo `.venv`; never install an editable or untagged build into pipx.

## Harness

`.claude/` is tracked in this fork although upstream's `.gitignore:19`
ignores it; the fork's `.gitignore` re-includes `.claude/CLAUDE.md` and
`.claude/docs/`. Global harness rules in `$CLAUDE_HOME/CLAUDE.md` apply.
