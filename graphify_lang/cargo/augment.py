"""Cargo.toml augment: workspace -> member edges, external crates as an attribute.

Core ``extract_package_manifest`` already gives each crate a ``pkg_<name>`` node
and ``depends_on`` edges to ``pkg_<dep>`` for runtime dependencies, so a path or
workspace dependency on a sibling crate already lands on that crate's node, and
an external crate's edge is pruned at build time. It gives a virtual workspace
root nothing. This adds only:

- a ``cargo_workspace_<dir>`` node for a ``[workspace]`` manifest, with a
  ``has_member`` edge to ``pkg_<name>`` of each member (``members`` globs minus
  ``exclude``, plus the root package when the root has ``[package]``);
- ``external_deps`` on the crate node: the runtime dependencies that are neither
  a ``path`` dependency nor a workspace dependency with a ``path``;
- a ``depends_on`` edge for an in-repo dependency renamed with ``package =``
  (core keys the edge by the dependency key, which names no crate).
"""
from __future__ import annotations

from pathlib import Path

from graphify.ids import make_id

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib


def _load(path: Path) -> dict | None:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _table(data: dict, key: str) -> dict:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _name(data: dict | None) -> str | None:
    name = _table(data or {}, "package").get("name")
    return name if isinstance(name, str) and name else None


def _members(root: Path, data: dict) -> list[str]:
    """Package names of the workspace members, as cargo resolves them."""
    ws = _table(data, "workspace")
    exclude = {(root / e).resolve() for e in ws.get("exclude", []) if isinstance(e, str)}
    dirs: dict[Path, None] = {}
    for pattern in ws.get("members", []):
        if isinstance(pattern, str):
            for d in sorted(root.glob(pattern)):
                if (d / "Cargo.toml").is_file() and d.resolve() not in exclude:
                    dirs[d.resolve()] = None
    names = [_name(_load(d / "Cargo.toml")) for d in dirs]
    if _name(data):
        names.append(_name(data))
    return sorted({n for n in names if n})


def _workspace_deps(path: Path) -> dict:
    """``[workspace.dependencies]`` of the workspace that contains ``path``."""
    for parent in path.parent.parents:
        data = _load(parent / "Cargo.toml") if (parent / "Cargo.toml").is_file() else None
        if data and "workspace" in data:
            return _table(_table(data, "workspace"), "dependencies")
    return {}


def _deps(path: Path, data: dict) -> tuple[list[str], list[str]]:
    """Runtime dependencies (core's scope): (external names, renamed in-repo names)."""
    tables = [_table(data, "dependencies")]
    tables += [_table(cfg, "dependencies") for cfg in _table(data, "target").values()
               if isinstance(cfg, dict)]
    ws_deps = _table(_table(data, "workspace"), "dependencies") if "workspace" in data else None
    external, renamed = set(), set()
    for table in tables:
        for key, spec in table.items():
            spec = spec if isinstance(spec, dict) else {}
            if spec.get("workspace") is True:
                if ws_deps is None:
                    ws_deps = _workspace_deps(path)
                inherited = ws_deps.get(key)
                spec = {**(inherited if isinstance(inherited, dict) else {}), **spec}
            name = spec.get("package") or key
            if "path" not in spec:
                external.add(name)
            elif name != key:
                renamed.add(name)
    return sorted(external), sorted(renamed)


def _edge(source: str, target: str, relation: str, context: str, src: str) -> dict:
    return {"source": source, "target": target, "relation": relation, "context": context,
            "confidence": "EXTRACTED", "confidence_score": 1.0, "source_file": src,
            "source_location": "L1", "weight": 1.0}


def augment_cargo(path: Path, base: dict) -> dict:
    data = _load(path)
    if data is None:
        return {}
    nodes, edges, attrs = [], [], {}
    src = str(path)
    if "workspace" in data:
        wid = make_id("cargo", "workspace", path.parent.name)
        nodes.append({
            "id": wid,
            "label": f"{path.parent.name} (cargo workspace)",
            "file_type": "code",
            "type": "workspace",
            "ecosystem": "cargo",
            "source_file": src,
            "source_location": "L1",
        })
        for member in _members(path.parent, data):
            edges.append(_edge(wid, make_id("pkg", member), "has_member", "workspace_member", src))
    name = _name(data)
    if name:
        pid = make_id("pkg", name)
        external, renamed = _deps(path, data)
        if external:
            attrs[pid] = {"external_deps": external}
        for dep in renamed:
            edges.append(_edge(pid, make_id("pkg", dep), "depends_on", "dependency", src))
    return {"nodes": nodes, "edges": edges, "attrs": attrs}
