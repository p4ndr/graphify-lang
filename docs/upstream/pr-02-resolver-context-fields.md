# Upstream PR draft: resolver context fields on incremental rebuilds

- Status: DRAFT. Not opened on GitHub; opening it needs owner approval.
- Plan: 01 T10 (roadmap phase 6); plan 05 hub D2.
- Base: upstream `v8` at `4000de1` (release 0.9.68). The diff applies with `git apply` and its test passes there (verified 2026-09-26, plan 05 S6.3).
- Fork finding: H1 / E3 (`cc-CR000.001`, fixed in the fork by `03dfe51` (`context_fields` hook), `cc0e296` (incremental cross-file edges) on `rr-s6`; E3 is this draft).

## Problem

On an incremental rebuild (`watch._rebuild_code(changed_paths=...)`, and
the `graphify extract` incremental path in `cli.py`), unchanged files reach
the cross-file resolvers only as context nodes rebuilt from `graph.json`. The
rebuild copies a fixed field list (`id`, `label`, `source_file`, `file_type`,
`type`, a few `_callable` / Rust / Elixir markers and some Ruby / Erlang
`metadata`). A resolver registered through `graphify.resolver_registry` that
indexes other files' nodes by any other field finds nothing, so every edge it
would draw into an unchanged file is lost until the next full build. In the
fork this broke 23 of 49 plugin files' edges on an incremental build (plan 05
S4). Second gap: a context node's `source_file` is root-relative while fresh
nodes carry an absolute path, so a resolver cannot compare the two.

## Change

`LanguageResolver` gets an optional `context_fields` (default empty), and
`registered_context_fields()` returns their union. Both context-node builders
forward those fields when the persisted node has them, and add
`_abs_source_file`, the absolute path of the node's file. With no resolver
declaring fields, only `_abs_source_file` is new, and nothing is emitted from
context nodes.

## Diff

```diff
diff --git a/graphify/cli.py b/graphify/cli.py
index f31d3c59..45933fb4 100644
--- a/graphify/cli.py
+++ b/graphify/cli.py
@@ -3849,6 +3849,8 @@ def dispatch_command(cmd: str) -> None:
                     }
                     _ctx_live.discard(None)
                     _ctx_live.difference_update(_ctx_identity(p) for p in code_files)
+                    from graphify.resolver_registry import registered_context_fields
+                    _extra_fields = registered_context_fields()
                     for _node in _ctx_graph.get("nodes", []):
                         if not _node.get("id") or not _ctx_is_ast_tier(_node):
                             continue
@@ -3870,6 +3872,11 @@ def dispatch_command(cmd: str) -> None:
                         ):
                             if _node.get(_marker):
                                 _ctx_node[_marker] = _node[_marker]
+                        # Same forwarding as watch._rebuild_code.
+                        for _key in _extra_fields:
+                            if _key in _node and _key not in _ctx_node:
+                                _ctx_node[_key] = _node[_key]
+                        _ctx_node["_abs_source_file"] = _ctx_identity(_sf)
                         _metadata = _node.get("metadata")
                         if isinstance(_metadata, dict):
                             _fwd_metadata = {
diff --git a/graphify/resolver_registry.py b/graphify/resolver_registry.py
index b17478a7..afb404d2 100644
--- a/graphify/resolver_registry.py
+++ b/graphify/resolver_registry.py
@@ -33,11 +33,17 @@ class LanguageResolver:
     mutates ``all_nodes`` / ``all_edges`` in place, matching the existing
     member-call resolvers. ``suffixes`` gates activation: the pass runs only when
     the corpus contains at least one file with one of these extensions.
+
+    ``context_fields`` names node fields the pass reads on other files' nodes.
+    On an incremental rebuild, unchanged files reach the resolvers only as
+    context nodes rebuilt from ``graph.json`` with a fixed field list; the
+    fields named here are forwarded too.
     """
 
     name: str
     suffixes: frozenset
     resolve: Callable
+    context_fields: frozenset = frozenset()
 
 
 # Module-level registry, populated by callers via register(). Ordered: resolvers
@@ -56,6 +62,11 @@ def registered_resolvers() -> list[LanguageResolver]:
     return list(_REGISTRY)
 
 
+def registered_context_fields() -> frozenset:
+    """Union of the registered resolvers' ``context_fields``."""
+    return frozenset().union(*(r.context_fields for r in _REGISTRY))
+
+
 def run_language_resolvers(
     paths: Sequence[Path],
     per_file: list[dict],
diff --git a/graphify/watch.py b/graphify/watch.py
index d1100a7d..c553275e 100644
--- a/graphify/watch.py
+++ b/graphify/watch.py
@@ -1714,6 +1714,8 @@ def _rebuild_code(
                 }
                 ctx_live -= deleted_source_identities
                 ctx_live.discard(None)
+                from graphify.resolver_registry import registered_context_fields
+                extra_fields = registered_context_fields()
                 for node in ctx_graph.get("nodes", []):
                     if not node.get("id") or not _is_ast_tier(node):
                         continue
@@ -1736,6 +1738,12 @@ def _rebuild_code(
                     ):
                         if node.get(marker):
                             ctx_node[marker] = node[marker]
+                    # Fields a registered resolver declared, and the absolute
+                    # path that fresh nodes carry as source_file.
+                    for key in extra_fields:
+                        if key in node and key not in ctx_node:
+                            ctx_node[key] = node[key]
+                    ctx_node["_abs_source_file"] = ctx_paths.identity(source_file)
                     metadata = node.get("metadata")
                     if isinstance(metadata, dict):
                         fwd_metadata = {
diff --git a/tests/test_resolver_context_fields.py b/tests/test_resolver_context_fields.py
new file mode 100644
index 00000000..b94f440c
--- /dev/null
+++ b/tests/test_resolver_context_fields.py
@@ -0,0 +1,90 @@
+"""A resolver's declared context_fields reach it on an incremental rebuild."""
+import json
+import os
+from pathlib import Path
+
+from graphify import resolver_registry as rr
+from graphify.watch import _rebuild_code
+
+
+def test_context_fields_reach_resolver_on_incremental_rebuild(tmp_path, monkeypatch):
+    a, b = tmp_path / "a.py", tmp_path / "b.py"
+    a.write_text("def fa():\n    return 1\n", encoding="utf-8")
+    b.write_text("def fb():\n    return 2\n", encoding="utf-8")
+    assert _rebuild_code(tmp_path, no_cluster=True, acquire_lock=False)
+    # Stand-in for a plugin extractor field: persisted on b.py's nodes.
+    graph_path = tmp_path / "graphify-out" / "graph.json"
+    graph = json.loads(graph_path.read_text(encoding="utf-8"))
+    for node in graph["nodes"]:
+        if str(node.get("source_file", "")).endswith("b.py"):
+            node["probe_field"] = "kept"
+    graph_path.write_text(json.dumps(graph), encoding="utf-8")
+
+    seen: list[dict] = []
+    probe = rr.LanguageResolver("probe", frozenset({".py"}),
+                                lambda per_file, nodes, edges: seen.extend(nodes),
+                                context_fields=frozenset({"probe_field"}))
+    monkeypatch.setattr(rr, "_REGISTRY", [*rr._REGISTRY, probe])
+    a.write_text("def fa():\n    return 3\n", encoding="utf-8")
+    assert _rebuild_code(tmp_path, changed_paths=[a], no_cluster=True, acquire_lock=False)
+
+    ctx = [n for n in seen if str(n.get("source_file", "")).endswith("b.py")]
+    assert ctx, "b.py's nodes are resolution context"
+    assert {n.get("probe_field") for n in ctx} == {"kept"}
+    # Context nodes carry a root-relative source_file, fresh nodes an absolute
+    # one; _abs_source_file lets a resolver compare them.
+    assert {n.get("_abs_source_file") for n in ctx} == {Path(b).resolve().as_posix()}
+
+
+def test_registered_context_fields_is_the_union(monkeypatch):
+    noop = lambda *a: None  # noqa: E731
+    monkeypatch.setattr(rr, "_REGISTRY", [
+        rr.LanguageResolver("x", frozenset({".x"}), noop, context_fields=frozenset({"k1"})),
+        rr.LanguageResolver("y", frozenset({".y"}), noop),
+        rr.LanguageResolver("z", frozenset({".z"}), noop, context_fields=frozenset({"k1", "k2"})),
+    ])
+    assert rr.registered_context_fields() == frozenset({"k1", "k2"})
+
+
+_CLI_PROBE = """
+import json, sys
+from pathlib import Path
+from graphify import resolver_registry as rr
+from graphify.__main__ import main
+
+seen = Path(sys.argv[1])
+def probe(per_file, nodes, edges):
+    seen.write_text(json.dumps([n for n in nodes if str(n.get("source_file", "")).endswith("b.py")]))
+rr.register(rr.LanguageResolver("probe", frozenset({".py"}), probe,
+                                context_fields=frozenset({"probe_field"})))
+sys.argv = ["graphify", "extract", sys.argv[2], "--code-only", "--no-cluster"]
+main()
+"""
+
+
+def test_context_fields_reach_resolver_on_incremental_extract(tmp_path):
+    """The `graphify extract` incremental path forwards the same fields."""
+    import subprocess
+    import sys
+    proj = tmp_path / "proj"
+    proj.mkdir()
+    a, b = proj / "a.py", proj / "b.py"
+    a.write_text("def fa():\n    return 1\n", encoding="utf-8")
+    b.write_text("def fb():\n    return 2\n", encoding="utf-8")
+    seen = tmp_path / "seen.json"
+    run = [sys.executable, "-c", _CLI_PROBE, str(seen), str(proj)]
+    env = {**os.environ, "PYTHONPATH": str(Path(rr.__file__).resolve().parents[1])}
+    subprocess.run(run, check=True, capture_output=True, cwd=tmp_path, env=env)
+    graph_path = proj / "graphify-out" / "graph.json"
+    graph = json.loads(graph_path.read_text(encoding="utf-8"))
+    for node in graph["nodes"]:
+        if str(node.get("source_file", "")).endswith("b.py"):
+            node["probe_field"] = "kept"
+    graph_path.write_text(json.dumps(graph), encoding="utf-8")
+    a.write_text("def fa():\n    return 3\n", encoding="utf-8")
+    seen.unlink()
+    subprocess.run(run, check=True, capture_output=True, cwd=tmp_path, env=env)
+    ctx = json.loads(seen.read_text(encoding="utf-8"))
+    assert ctx, "b.py's nodes are resolution context"
+    assert {n.get("probe_field") for n in ctx} == {"kept"}
+    assert {n.get("_abs_source_file") for n in ctx} == {Path(b).resolve().as_posix()}
```

## Test

`tests/test_resolver_context_fields.py` (in the diff):

- `test_context_fields_reach_resolver_on_incremental_rebuild`: two `.py`
  files, a full `_rebuild_code`, a `probe_field` written onto `b.py`'s
  persisted nodes (standing in for an extractor field), a probe resolver that
  declares it, then an incremental rebuild of `a.py`: the probe sees `b.py`'s
  context nodes with `probe_field` and an absolute `_abs_source_file`.
- `test_context_fields_reach_resolver_on_incremental_extract`: the same
  through `graphify extract --code-only --no-cluster` in a subprocess.
- `test_registered_context_fields_is_the_union`.

Measured on the base: 3 failed without the diff, 3 passed with it; the
`extract` test fails when only the `cli.py` hunk is missing. Full suite with
the diff: 5991 passed, 14 skipped.

## Fork side

The fork reads the field list from its manifests (`[resolve]
context_fields`) through `graphify.lang_registry.context_fields()` and names
the path field `_lang_source_file`; resolvers compare paths through
`graphify_lang._common.source_of`. With this PR merged the fork would declare
`context_fields` on its `LanguageResolver`s, read `_abs_source_file`, and drop
its two hook blocks. The E5 parity test
(`tests/lang/test_s4_build_coherence.py::test_e5_incremental_parity`) is the
fork-side check. Not covered here: an edge owned by an unchanged file into a
newly added file still appears only on the next full build (upstream's
incremental model).
