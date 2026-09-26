# Upstream PR draft: language plugins through entry points

- Status: DRAFT. Not opened on GitHub; opening it needs owner approval.
- Plan: 01 T10 (roadmap phase 6); plan 05 hub D2.
- Base: upstream `v8` at `4000de1` (release 0.9.68). The diff applies with `git apply` and its test passes there (verified 2026-09-26, plan 05 S6.3).
- Fork finding: the registry lookups in `detect.py` and `extract.py` (plan 01; the fork's `graphify/lang_registry.py` hooks).

## Problem

Adding a language to graphify means editing the core: a `_DISPATCH` entry
in `extract.py`, a `CODE_EXTENSIONS` entry in `detect.py`, and more
(`README.md`, 'Adding a language costs six edits across five files'). A
language that upstream does not want (AutoLISP, VBA, Bentley bmake) can only
be carried as a patch on the core, and every rebase has to carry it.
`graphify/extractors/__init__.py` already calls `LANGUAGE_EXTRACTORS` 'the
registry seed; wiring dispatch through it is a later, separate step'. This
PR is that step for installed packages.

## Change

A package declares an entry point in the `graphify.languages` group that
loads to an object with `SUFFIXES` and `extract(path) -> dict`. At import,
`detect.py` adds the suffixes to `CODE_EXTENSIONS` and `extract.py` adds the
extractors to `_DISPATCH`. A built-in entry is never replaced, so with no
plugin installed nothing changes; a plugin that fails to load is logged and
skipped.

## Diff

```diff
diff --git a/graphify/detect.py b/graphify/detect.py
index 2c9eb01..bbfa282 100644
--- a/graphify/detect.py
+++ b/graphify/detect.py
@@ -42,6 +42,9 @@ _MTIME_COARSE_S = 2.0
 _MTIME_SUBSECOND_S = 0.05
 
 CODE_EXTENSIONS = {'.py', '.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs', '.ejs', '.ets', '.go', '.rs', '.vb', '.cbl', '.cob', '.cobol', '.cpy', '.java', '.groovy', '.gradle', '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.cu', '.cuh', '.metal', '.rb', '.rake', '.swift', '.kt', '.kts', '.cs', '.scala', '.php', '.lua', '.luau', '.toc', '.zig', '.ps1', '.psm1', '.psd1', '.ex', '.exs', '.m', '.mm', '.ml', '.mli', '.jl', '.vue', '.svelte', '.astro', '.dart', '.v', '.sv', '.svh', '.sql', '.r', '.f', '.F', '.f90', '.F90', '.f95', '.F95', '.f03', '.F03', '.f08', '.F08', '.pas', '.pp', '.dpr', '.dpk', '.lpr', '.inc', '.dfm', '.lfm', '.lpk', '.sh', '.bash', '.json', '.tf', '.tfvars', '.hcl', '.dm', '.dme', '.dmi', '.dmm', '.dmf', '.sln', '.slnx', '.csproj', '.fsproj', '.vbproj', '.xaml', '.razor', '.cshtml', '.cls', '.trigger', '.lisp', '.cl', '.lsp', '.asd', '.robot', '.resource', '.sol', '.erl', '.hrl', '.escript'}
+# Suffixes of installed language plugins (graphify.languages entry points).
+from graphify.language_plugins import plugins as _language_plugins  # noqa: E402
+CODE_EXTENSIONS.update(_language_plugins())
 DOC_EXTENSIONS = {'.md', '.mdx', '.qmd', '.skill', '.txt', '.rst', '.html', '.yaml', '.yml'}
 PAPER_EXTENSIONS = {'.pdf'}
 IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
diff --git a/graphify/extract.py b/graphify/extract.py
index b20fdc9..5d0bfb2 100644
--- a/graphify/extract.py
+++ b/graphify/extract.py
@@ -6712,6 +6712,10 @@ _DISPATCH: dict[str, Any] = {
     ".cls": extract_apex,
     ".trigger": extract_apex,
 }
+# Installed language plugins add suffixes; a built-in entry is never replaced.
+from graphify.language_plugins import plugins as _language_plugins  # noqa: E402
+for _suffix, _extract in _language_plugins().items():
+    _DISPATCH.setdefault(_suffix, _extract)
 
 
 # Extensions whose extractor depends on an optional-dependency extra
diff --git a/graphify/language_plugins.py b/graphify/language_plugins.py
new file mode 100644
index 0000000..b5d4051
--- /dev/null
+++ b/graphify/language_plugins.py
@@ -0,0 +1,34 @@
+"""Language extractors registered by installed packages (entry points).
+
+A package adds a language without editing the core by declaring an entry point
+in the ``graphify.languages`` group that loads to an object with ``SUFFIXES``
+(lower-case suffixes such as ``".lsp"``) and ``extract(path) -> dict`` (the
+extraction schema in ``ARCHITECTURE.md``). At import, ``detect.py`` adds the
+suffixes to ``CODE_EXTENSIONS`` and ``extract.py`` adds the extractors to
+``_DISPATCH`` without replacing a built-in entry. A plugin that fails to load
+is logged and skipped. A plugin module must not import ``graphify.detect`` or
+``graphify.extract`` at module level: it is loaded while they import.
+"""
+from __future__ import annotations
+
+import functools
+import logging
+from collections.abc import Callable
+from importlib.metadata import entry_points
+
+_LOG = logging.getLogger(__name__)
+GROUP = "graphify.languages"
+
+
+@functools.cache
+def plugins() -> dict[str, Callable]:
+    """``suffix -> extract`` over every loadable entry point; the first wins."""
+    found: dict[str, Callable] = {}
+    for ep in entry_points(group=GROUP):
+        try:
+            lang = ep.load()
+            for suffix in lang.SUFFIXES:
+                found.setdefault(suffix.lower(), lang.extract)
+        except Exception as exc:
+            _LOG.warning("language plugin %s failed to load, skipping: %s", ep.name, exc)
+    return found
diff --git a/tests/test_language_plugins.py b/tests/test_language_plugins.py
new file mode 100644
index 0000000..a78b24d
--- /dev/null
+++ b/tests/test_language_plugins.py
@@ -0,0 +1,49 @@
+"""Entry-point language plugins (graphify.languages) reach the core tables."""
+import os
+import subprocess
+import sys
+from pathlib import Path
+from types import SimpleNamespace
+
+import graphify
+import graphify.language_plugins as lp
+
+
+def test_installed_plugin_is_wired_at_import(tmp_path):
+    """A dist-info on sys.path is found when detect / extract import; a
+    built-in suffix is not taken over."""
+    (tmp_path / "zzlang.py").write_text(
+        "SUFFIXES = ('.zz', '.py')\n"
+        "def extract(path):\n    return {'nodes': [], 'edges': []}\n", encoding="utf-8")
+    info = tmp_path / "zzlang-0.1.dist-info"
+    info.mkdir()
+    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: zzlang\nVersion: 0.1\n",
+                                   encoding="utf-8")
+    (info / "entry_points.txt").write_text("[graphify.languages]\nzz = zzlang\n",
+                                           encoding="utf-8")
+    code = ("from pathlib import Path\n"
+            "from graphify.detect import classify_file, FileType\n"
+            "from graphify.extract import _get_extractor, collect_files\n"
+            "Path('a.zz').write_text('x')\n"
+            "assert classify_file(Path('a.zz')) is FileType.CODE\n"
+            "assert _get_extractor(Path('a.zz')).__module__ == 'zzlang'\n"
+            "assert _get_extractor(Path('B.ZZ')).__module__ == 'zzlang'\n"
+            "assert _get_extractor(Path('a.py')).__module__ != 'zzlang'\n"
+            "assert 'a.zz' in [p.name for p in collect_files(Path('.'))]\n")
+    core = str(Path(graphify.__file__).resolve().parents[1])
+    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path), core])}
+    subprocess.run([sys.executable, "-c", code], check=True, env=env, cwd=tmp_path)
+
+
+def test_broken_plugin_is_logged_and_skipped(monkeypatch, caplog):
+    def boom():
+        raise ImportError("no grammar")
+    good = SimpleNamespace(SUFFIXES=(".ZZ",), extract=print)
+    eps = [SimpleNamespace(name="bad", load=boom), SimpleNamespace(name="zz", load=lambda: good)]
+    monkeypatch.setattr(lp, "entry_points", lambda group: eps if group == lp.GROUP else [])
+    lp.plugins.cache_clear()
+    try:
+        assert lp.plugins() == {".zz": print}
+    finally:
+        lp.plugins.cache_clear()
+    assert "bad failed to load" in caplog.text
```

## Test

`tests/test_language_plugins.py` (in the diff):

- `test_installed_plugin_is_wired_at_import` writes a `zzlang` module and a
  `zzlang-0.1.dist-info` with the entry point into a temporary folder, puts it
  on `PYTHONPATH` and imports the core in a subprocess: `a.zz` is CODE,
  `_get_extractor` returns the plugin's `extract` (also for `B.ZZ`),
  `collect_files` finds `a.zz`, and `a.py` keeps the built-in extractor.
  Without the two core hooks it fails (`classify_file` returns `None`).
- `test_broken_plugin_is_logged_and_skipped`: a failing entry point is logged
  and the next one still loads.

Measured on the base: 2 passed with the diff; the import test fails without
the `detect.py` hook. Full suite with the diff: 5990 passed, 14 skipped.

## Fork side

The fork's registry (`graphify/lang_registry.py`, `graphify_lang/`) does
more than this seam: content sniffing for shared suffixes (`.cls`, `.xml`,
`.yml`), `[match]` claims for data files, augments of built-in extractors, the
hook-nudge suffixes, an AST-cache fingerprint of the plugin set, and
`graphify lang list`. Those can follow as separate PRs once this seam exists;
the fork would then register through this group and drop its own
`detect.py` / `extract.py` blocks. Follow-up seams not in this PR:
`_HOOK_SOURCE_EXTS` (`cli.py`) and `_EXTRA_FOR_EXTENSION` (`extract.py`).
