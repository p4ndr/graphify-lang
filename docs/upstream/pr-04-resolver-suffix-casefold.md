# Upstream PR draft: case-folded suffix match in run_language_resolvers

- Status: DRAFT. Not opened on GitHub; opening it needs owner approval.
- Plan: 01 T10 (roadmap phase 6); plan 05 hub D2.
- Base: upstream `v8` at `4000de1` (release 0.9.68). The diff applies with `git apply` and its test passes there (verified 2026-09-26, plan 05 S6.3).
- Fork finding: L13 (`cc-CR000.001`, pinned in the fork by plan 05 S5.4, T10.4).

## Problem

`run_language_resolvers` activates a resolver when one of its suffixes is
in `{p.suffix for p in paths}`, compared case-sensitively. Dispatch is not
case-sensitive (`_get_extractor` falls back to `suffix.lower()`), so a corpus
whose files are all upper case (`ERR.LSP`, common in AutoCAD and older Windows
trees) is extracted but its resolver never runs, and no cross-file edge is
drawn.

## Change

One line: compare `p.suffix.lower()`. Every built-in resolver registers
lower-case suffixes (the R resolver registers `.r` and `.R`; `.R` files still
match through `.r`). A side effect: a `.H` header now also activates the
C/C++ and Objective-C resolvers, as `.h` does, consistent with dispatch.

## Diff

```diff
diff --git a/graphify/resolver_registry.py b/graphify/resolver_registry.py
index b17478a7..10663bc5 100644
--- a/graphify/resolver_registry.py
+++ b/graphify/resolver_registry.py
@@ -75,7 +75,8 @@ def run_language_resolvers(
     exercise the driver in isolation.
     """
     active = _REGISTRY if resolvers is None else resolvers
-    suffixes_present = {p.suffix for p in paths}
+    # Suffixes are matched case-folded: `ERR.LSP` activates a `.lsp` resolver.
+    suffixes_present = {p.suffix.lower() for p in paths}
     for resolver in active:
         if not (resolver.suffixes & suffixes_present):
             continue
diff --git a/tests/test_resolver_suffix_casefold.py b/tests/test_resolver_suffix_casefold.py
new file mode 100644
index 00000000..1236d96d
--- /dev/null
+++ b/tests/test_resolver_suffix_casefold.py
@@ -0,0 +1,18 @@
+"""run_language_resolvers matches suffixes case-insensitively."""
+from pathlib import Path
+
+from graphify.resolver_registry import LanguageResolver, run_language_resolvers
+
+
+def test_upper_case_suffix_activates_resolver():
+    calls = []
+    resolver = LanguageResolver("probe", frozenset({".lsp"}), lambda *a: calls.append(a))
+    run_language_resolvers([Path("src/ERR.LSP")], [], [], [], resolvers=[resolver])
+    assert len(calls) == 1
+
+
+def test_absent_suffix_still_skips():
+    calls = []
+    resolver = LanguageResolver("probe", frozenset({".lsp"}), lambda *a: calls.append(a))
+    run_language_resolvers([Path("src/a.py")], [], [], [], resolvers=[resolver])
+    assert calls == []
```

## Test

`tests/test_resolver_suffix_casefold.py` (in the diff): a resolver for
`.lsp` runs for `src/ERR.LSP`, and still skips a corpus without the suffix.
Measured on the base: 1 failed, 1 passed without the diff; 2 passed with it,
with `tests/test_language_resolvers.py` (5 tests) unchanged and passing.

## Fork side

The fork carries the same line (`graphify/resolver_registry.py`) since
plan 01; the fork test is `tests/lang/test_s5_registry_robustness.py`
(L13). With this PR merged the fork's diff to `resolver_registry.py` goes to
zero.
