# Upstream PR draft: code-path claims in watch

- Status: DRAFT. Not opened on GitHub; opening it needs owner approval.
- Plan: 01 T10 (roadmap phase 6); plan 05 hub D2.
- Base: upstream `v8` at `4000de1` (release 0.9.68). The diff applies with `git apply` and its test passes there (verified 2026-09-26, plan 05 S6.3; re-verified after the cc-CR000.003 S6 review fixes).
- Fork finding: M3 (`cc-CR000.001`, fixed in the fork by `f8219a1` (`watch_claims`), `ae768d4` (`watch.py` lookup) on `rr-s6`).

## Problem

`graphify watch` decides by suffix alone whether a changed file is code:
the event filter checks `_WATCHED_EXTENSIONS`, `_batch_triggers_rebuild` and
`_has_non_code` check `_CODE_EXTENSIONS`. A language that owns only some files
of a data suffix (ECSchema `.xml`, ast-grep rule `.yml`, `Cargo.toml`) cannot
put the suffix in `CODE_EXTENSIONS` without turning every `.xml` into code, so
an edit to one of its files is dropped by the filter, or only sets the
`needs_update` flag with the 'semantic re-extraction requires LLM' message,
and the graph goes stale.

## Change

`watch.py` gets `register_code_path_claim(claim)` and a module list of
`claim(path) -> bool` predicates. The three suffix checks also accept a path
that a registered claim returns true for. A claim that raises counts as no
claim (logged at debug level). In the event handler the claim runs after
the `.graphifyignore`, dot-folder and `graphify-out` filters, because a claim
may open the file: a write under `.git/` never reaches it. With no claim
registered nothing changes.

## Diff

```diff
diff --git a/graphify/watch.py b/graphify/watch.py
index d1100a7..f944ab2 100644
--- a/graphify/watch.py
+++ b/graphify/watch.py
@@ -282,6 +282,27 @@ from graphify.detect import (
 _WATCHED_EXTENSIONS = CODE_EXTENSIONS | DOC_EXTENSIONS | PAPER_EXTENSIONS | IMAGE_EXTENSIONS
 _CODE_EXTENSIONS = CODE_EXTENSIONS
 
+# Predicates for files that are code although their suffix is not in
+# CODE_EXTENSIONS: a language plugin that claims some `.xml` or `.yml` files by
+# name or content registers one, so their edits rebuild the graph.
+_CODE_PATH_CLAIMS: list[Callable[[Path], bool]] = []
+
+
+def register_code_path_claim(claim: Callable[[Path], bool]) -> Callable[[Path], bool]:
+    """Register ``claim(path) -> bool``; watch treats a claimed path as code."""
+    _CODE_PATH_CLAIMS.append(claim)
+    return claim
+
+
+def _claimed_as_code(path: Path) -> bool:
+    for claim in _CODE_PATH_CLAIMS:
+        try:
+            if claim(path):
+                return True
+        except Exception as exc:
+            logger.debug("code-path claim %r failed on %s: %s", claim, path, exc)
+    return False
+
 
 def _report_root_label(watch_path: Path) -> str:
     if watch_path.is_absolute():
@@ -2291,7 +2312,10 @@ def _notify_only(watch_path: Path) -> None:
 
 
 def _has_non_code(changed_paths: list[Path]) -> bool:
-    return any(p.suffix.lower() not in _CODE_EXTENSIONS for p in changed_paths)
+    return any(
+        p.suffix.lower() not in _CODE_EXTENSIONS and not _claimed_as_code(p)
+        for p in changed_paths
+    )
 
 
 def _batch_triggers_rebuild(batch: list[Path]) -> bool:
@@ -2303,7 +2327,7 @@ def _batch_triggers_rebuild(batch: list[Path]) -> bool:
     this, a doc-only deletion batch would sit behind the needs_update flag
     until the next code event or a manual `graphify update` (#2580).
     """
-    has_code = any(p.suffix.lower() in _CODE_EXTENSIONS for p in batch)
+    has_code = any(p.suffix.lower() in _CODE_EXTENSIONS or _claimed_as_code(p) for p in batch)
     has_deletion = any(not p.exists() for p in batch)
     return has_code or has_deletion
 
@@ -2383,8 +2407,7 @@ def watch(watch_path: Path, debounce: float = 3.0) -> None:
             # relative_to guard, so a stray symlinked event won't raise.
             if ignore_patterns and _is_ignored(path, watch_root_for_ignore, ignore_patterns):
                 return
-            if path.suffix.lower() not in _WATCHED_EXTENSIONS:
-                return
+            watched = path.suffix.lower() in _WATCHED_EXTENSIONS
             try:
                 filter_parts = path.relative_to(watch_root_for_ignore).parts
             except ValueError:
@@ -2393,6 +2416,9 @@ def watch(watch_path: Path, debounce: float = 3.0) -> None:
                 return
             if _GRAPHIFY_OUT in filter_parts:
                 return
+            # A claim may read the file, so it runs after the cheap filters.
+            if not watched and not _claimed_as_code(path):
+                return
             last_trigger = time.monotonic()
             pending = True
             changed.add(path)
diff --git a/tests/test_watch_code_path_claims.py b/tests/test_watch_code_path_claims.py
new file mode 100644
index 0000000..3f4c470
--- /dev/null
+++ b/tests/test_watch_code_path_claims.py
@@ -0,0 +1,66 @@
+"""A registered claim makes watch treat a non-code suffix as code."""
+import threading
+import time
+from pathlib import Path
+
+import pytest
+
+from graphify import watch
+
+
+def _schema(path: Path) -> bool:
+    return path.name.endswith(".ecschema.xml")
+
+
+@pytest.fixture
+def claimed(monkeypatch):
+    monkeypatch.setattr(watch, "_CODE_PATH_CLAIMS", [])
+    watch.register_code_path_claim(_schema)
+
+
+def test_claimed_file_triggers_rebuild_and_is_code(claimed, tmp_path):
+    schema = tmp_path / "Base.ecschema.xml"
+    schema.write_text("<ECSchema/>\n", encoding="utf-8")
+    plain = tmp_path / "settings.xml"
+    plain.write_text("<settings/>\n", encoding="utf-8")
+    assert watch._batch_triggers_rebuild([schema]) is True
+    assert watch._has_non_code([schema]) is False
+    assert watch._batch_triggers_rebuild([plain]) is False
+    assert watch._has_non_code([plain]) is True
+
+
+def test_failing_claim_is_not_a_claim(monkeypatch, tmp_path):
+    def boom(path):
+        raise RuntimeError("claim failed")
+    monkeypatch.setattr(watch, "_CODE_PATH_CLAIMS", [boom])
+    schema = tmp_path / "Base.ecschema.xml"
+    schema.write_text("<ECSchema/>\n", encoding="utf-8")
+    assert watch._batch_triggers_rebuild([schema]) is False
+
+
+def test_watch_handler_passes_claimed_file(tmp_path, monkeypatch):
+    """A claimed .xml write reaches _rebuild_code; a .git object write never
+    reaches a claim (the dot-folder filter runs first)."""
+    pytest.importorskip("watchdog")
+    seen: list[Path] = []
+
+    def claim(path: Path) -> bool:
+        seen.append(path)
+        return _schema(path)
+
+    monkeypatch.setattr(watch, "_CODE_PATH_CLAIMS", [claim])
+    root = tmp_path / "corpus"
+    (root / ".git" / "objects" / "ab").mkdir(parents=True)
+    calls: list[Path] = []
+    monkeypatch.setattr(watch, "_rebuild_code", lambda p, **kw: calls.append(p) or True)
+    monkeypatch.setattr(watch, "_notify_only", lambda p: None)
+    threading.Thread(target=watch.watch, args=(root,), kwargs={"debounce": 0.2},
+                     daemon=True).start()
+    time.sleep(0.5)
+    (root / ".git" / "objects" / "ab" / "cdef0123").write_bytes(b"x")
+    (root / "Base.ecschema.xml").write_text("<ECSchema/>\n", encoding="utf-8")
+    deadline = time.monotonic() + 5.0
+    while time.monotonic() < deadline and not calls:
+        time.sleep(0.1)
+    assert calls, "a claimed .xml write should trigger _rebuild_code"
+    assert not [p for p in seen if ".git" in p.parts], "a .git write reached a claim"
```

## Test

`tests/test_watch_code_path_claims.py` (in the diff):

- `test_claimed_file_triggers_rebuild_and_is_code`: with a claim for
  `*.ecschema.xml`, a claimed file triggers a rebuild and is not non-code; a
  plain `settings.xml` is unchanged.
- `test_failing_claim_is_not_a_claim`.
- `test_watch_handler_passes_claimed_file` (needs `watchdog`): `watch()` on a
  temporary folder calls `_rebuild_code` when a claimed `.xml` is written, and
  a write under `.git/objects/` never reaches the claim (it fails with the
  claim at the suffix filter).

Measured on the base: 2 failed and 1 error without the diff, 3 passed with
it; the handler test fails with the claim at the suffix filter. Full suite
with the diff: 5991 passed, 14 skipped (review-fix pass, cc-CR000.003 S6-L2).

## Fork side

The fork calls `graphify.lang_registry.watch_claims` from a `_lang_claims`
helper at the same three sites (its handler check sits at the suffix filter,
to keep the fork's edit to one upstream line). An augment claims a file when
its `watch` predicate says so; cc-kb's (`watch_cc_kb`) claims a
`docs/cc-*.md` by name, and any other `.md` only when it mentions another cc
id or names a file under its harness root, so a plain doc edit does not
rebuild. That rule stays in the plugin's predicate. With this PR merged
the fork would register `watch_claims` through `register_code_path_claim`
and drop its three edited lines.
