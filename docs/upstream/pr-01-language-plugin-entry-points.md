# Upstream PR draft: language plugins through entry points

- Status: DRAFT. Not opened on GitHub; opening it needs owner approval.
- Plan: 01 T10 (roadmap phase 6); plan 05 hub D2.
- Base: upstream `v8` at `4000de1` (release 0.9.68). The diff applies with `git apply` and its test passes there (verified 2026-09-26, plan 05 S6.3; re-verified after the cc-CR000.003 S6 review fixes).
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

The AST cache is valid only for the extractor code that wrote it
(`cache.py`: "namespaced by package version"), and a plugin's code ships in
its own distribution. So `language_plugins.fingerprint()` hashes the name and
version of every loaded plugin's distribution, and `cache_dir` appends it to
the AST namespace: `cache/ast/v{version}-s{schema}-p{hash}/`. Upgrading a
plugin without upgrading graphify moves the namespace, and the existing sweep
of other `v*` folders removes the old entries. With no plugin the hash is
empty and the namespace is unchanged.

## Diff

```diff
diff --git a/graphify/cache.py b/graphify/cache.py
index 4b07636..7054fe9 100644
--- a/graphify/cache.py
+++ b/graphify/cache.py
@@ -954,7 +954,11 @@ def cache_dir(root: Path = Path("."), kind: str = "ast",
     base = _out if _out.is_absolute() else Path(root).resolve() / _out
     d = base / "cache" / kind
     if kind == "ast":
-        d = d / f"v{_EXTRACTOR_VERSION}-s{_AST_CACHE_SCHEMA}"
+        # Installed language plugins add -p{fingerprint}: their code ships
+        # outside graphify's version (graphify/language_plugins.py).
+        from graphify.language_plugins import fingerprint as _plugin_fp
+        fp = _plugin_fp()
+        d = d / (f"v{_EXTRACTOR_VERSION}-s{_AST_CACHE_SCHEMA}" + (f"-p{fp}" if fp else ""))
         _cleanup_stale_ast_entries(d.parent, d)
     elif prompt_fp:
         d = d / f"p{prompt_fp}"
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
index 0000000..1909c47
--- /dev/null
+++ b/graphify/language_plugins.py
@@ -0,0 +1,55 @@
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
+
+AST cache entries are only valid for the extractor code that wrote them
+(``cache.py``), and a plugin's code ships in its own distribution, so
+``fingerprint()`` hashes the name and version of every loaded plugin's
+distribution and ``cache_dir`` appends it to the AST namespace. With no plugin
+it is empty and the namespace is unchanged.
+"""
+from __future__ import annotations
+
+import functools
+import hashlib
+import logging
+from collections.abc import Callable
+from importlib.metadata import entry_points
+
+_LOG = logging.getLogger(__name__)
+GROUP = "graphify.languages"
+
+
+@functools.cache
+def _load() -> tuple[dict[str, Callable], str]:
+    found: dict[str, Callable] = {}
+    dists: set[tuple[str, str]] = set()
+    for ep in entry_points(group=GROUP):
+        try:
+            lang = ep.load()
+            for suffix in lang.SUFFIXES:
+                found.setdefault(suffix.lower(), lang.extract)
+        except Exception as exc:
+            _LOG.warning("language plugin %s failed to load, skipping: %s", ep.name, exc)
+            continue
+        dist = getattr(ep, "dist", None)
+        dists.add((getattr(dist, "name", None) or ep.name, getattr(dist, "version", None) or ""))
+    fp = hashlib.sha256(repr(sorted(dists)).encode()).hexdigest()[:12] if dists else ""
+    return found, fp
+
+
+def plugins() -> dict[str, Callable]:
+    """``suffix -> extract`` over every loadable entry point; the first wins."""
+    return _load()[0]
+
+
+def fingerprint() -> str:
+    """Hash of the loaded plugins' distribution names and versions; ``""`` with none."""
+    return _load()[1]
diff --git a/tests/test_language_plugins.py b/tests/test_language_plugins.py
new file mode 100644
index 0000000..c88aeef
--- /dev/null
+++ b/tests/test_language_plugins.py
@@ -0,0 +1,72 @@
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
+    lp._load.cache_clear()
+    try:
+        assert lp.plugins() == {".zz": print}
+    finally:
+        lp._load.cache_clear()
+    assert "bad failed to load" in caplog.text
+
+
+def test_plugin_version_namespaces_ast_cache(monkeypatch, tmp_path):
+    """Two versions of one plugin give two AST cache directories; with no
+    plugin the namespace is graphify's own."""
+    from graphify import cache
+
+    def eps(version):
+        lang = SimpleNamespace(SUFFIXES=(".zz",), extract=print)
+        return [SimpleNamespace(name="zz", load=lambda: lang,
+                                dist=SimpleNamespace(name="zzlang", version=version))]
+
+    names = []
+    for found in ([], eps("0.1"), eps("0.2")):
+        monkeypatch.setattr(lp, "entry_points",
+                            lambda group, found=found: found if group == lp.GROUP else [])
+        lp._load.cache_clear()
+        names.append(cache.cache_dir(tmp_path).name)
+    lp._load.cache_clear()
+    base = f"v{cache._EXTRACTOR_VERSION}-s{cache._AST_CACHE_SCHEMA}"
+    assert names[0] == base
+    assert names[1].startswith(base + "-p") and names[2].startswith(base + "-p")
+    assert names[1] != names[2]
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
- `test_plugin_version_namespaces_ast_cache`: with no plugin `cache_dir` is
  `v{version}-s{schema}`; versions `0.1` and `0.2` of one plugin give two
  different `-p` folders. Without the `cache.py` hunk it fails.

Measured on the base: 3 passed with the diff; the import test fails without
the `detect.py` hook, the cache test without the `cache.py` hunk. Full suite
with the diff: 5991 passed, 14 skipped (review-fix pass, cc-CR000.003 S6-M2).

## Fork side

The fork's registry (`graphify/lang_registry.py`, `graphify_lang/`) does
more than this seam: content sniffing for shared suffixes (`.cls`, `.xml`,
`.yml`), `[match]` claims for data files, `overrides` (a plugin taking a
built-in suffix), augments of built-in extractors, the hook-nudge suffixes, a
plugin-set fingerprint that also hashes the plugins' code, and `graphify lang
list`. Only plugins that add new suffixes can move to this seam as drafted:
`.mnl`, `.dcl`, `.bas`, `.frm`, `.mki`, `.mke`. `.lsp` (AutoLISP overrides
Common Lisp), `.cls` (sniffed against Apex), the `[match]` data files
(`.xml`, `.yml`, `Cargo.toml`) and the two augments cannot, because
`_DISPATCH.setdefault` never replaces a built-in; so the fork keeps its
`detect.py` / `extract.py` blocks until the follow-up seams exist.
Follow-up seams not in this PR: `overrides`, sniffing for a shared suffix,
`[match]` data files, augments, `_HOOK_SOURCE_EXTS` (`cli.py`) and
`_EXTRA_FOR_EXTENSION` (`extract.py`).
