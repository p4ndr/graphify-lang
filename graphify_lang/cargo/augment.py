"""Cargo.toml augment: the workspace node and the payload the resolver needs.

Core ``extract_package_manifest`` already gives each crate a ``pkg_<name>`` node
and ``depends_on`` edges to ``pkg_<dep>`` for runtime dependencies, so a path or
workspace dependency on a sibling crate already lands on that crate's node, and
an external crate's edge is pruned at build time. It gives a virtual workspace
root nothing.

The augment reads only its own file (the AST cache keys a result by the file's
bytes, cc-CR000.001 H3), and adds:

- a ``cargo_workspace_<dir>`` node for a ``[workspace]`` manifest, carrying
  ``cargo_ws_deps``: each ``[workspace.dependencies]`` entry as
  ``key=package`` (``key=package@path`` for a path dependency), so a member
  can inherit it in an incremental build too;
- a ``cargo_refs`` payload: the workspace's ``members`` globs and ``exclude``
  paths, and the crate's runtime dependencies (external, renamed in-repo, and
  ``workspace = true`` ones by key).

``resolve.py`` matches the payload against the graphed nodes: ``has_member``
edges, ``external_deps`` on the crate node, and a ``depends_on`` edge for an
in-repo dependency renamed with ``package =``.
"""
from __future__ import annotations

from pathlib import Path

from graphify.ids import make_id
from graphify_lang.manifest import tomllib


def _load(path: Path) -> dict | None:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _table(data: dict, key: str) -> dict:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _name(data: dict) -> str | None:
    name = _table(data, "package").get("name")
    return name if isinstance(name, str) and name else None


def _strs(value) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _spec(key: str, spec) -> tuple[str | None, bool]:
    """(``package =`` rename or None, has ``path``) of a dependency spec."""
    spec = spec if isinstance(spec, dict) else {}
    package = spec.get("package")
    return (package if isinstance(package, str) and package else None), "path" in spec


def _deps(data: dict) -> dict:
    """Runtime dependencies (core's scope), by kind."""
    tables = [_table(data, "dependencies")]
    tables += [_table(cfg, "dependencies") for cfg in _table(data, "target").values()
               if isinstance(cfg, dict)]
    external, renamed, inherit = set(), set(), set()
    for table in tables:
        for key, spec in table.items():
            package, path = _spec(key, spec)
            if isinstance(spec, dict) and spec.get("workspace") is True:
                inherit.add(f"{key}={package or ''}{'@path' if path else ''}")
            elif not path:
                external.add(package or key)
            elif (package or key) != key:
                renamed.add(package)
    return {"external": sorted(external), "renamed": sorted(renamed), "inherit": sorted(inherit)}


def augment_cargo(path: Path, base: dict) -> dict:
    data = _load(path)
    if data is None:
        return {}
    nodes, refs = [], {}
    if "workspace" in data:
        ws = _table(data, "workspace")
        ws_deps = []
        for key, spec in _table(ws, "dependencies").items():
            package, has_path = _spec(key, spec)
            ws_deps.append(f"{key}={package or key}{'@path' if has_path else ''}")
        wid = make_id("cargo", "workspace", path.parent.name)
        nodes.append({
            "id": wid,
            "label": f"{path.parent.name} (cargo workspace)",
            "file_type": "code",
            "type": "workspace",
            "ecosystem": "cargo",
            "source_file": str(path),
            "source_location": "L1",
            "cargo_ws_deps": sorted(ws_deps),
        })
        refs["workspace"] = {"id": wid, "members": _strs(ws.get("members")),
                             "exclude": _strs(ws.get("exclude"))}
    name = _name(data)
    if name:
        refs["crate"] = {"id": make_id("pkg", name), **_deps(data)}
    out: dict = {"nodes": nodes}
    if refs:
        out["cargo_refs"] = {"source_file": str(path), **refs}
    return out
