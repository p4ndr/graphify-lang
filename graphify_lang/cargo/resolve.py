"""Cargo cross-file resolver (plan 05 S4, cc-CR000.001 H3, L9).

Consumes the ``cargo_refs`` payload of each augmented ``Cargo.toml``. It sees
only graphed nodes, so nothing outside the scan root is read (L9).

- ``workspace``: a ``has_member`` edge from the workspace node to the crate
  node of each graphed ``Cargo.toml`` whose folder matches a ``members`` glob
  (relative to the workspace folder) and is not an ``exclude`` path, plus the
  root crate when the workspace manifest has ``[package]``.
- ``crate``: ``external_deps`` on the crate node (dependencies with no
  ``path``); a ``depends_on`` edge for an in-repo dependency renamed with
  ``package =``. A ``workspace = true`` dependency takes its spec from the
  nearest graphed workspace at or above the crate (``cargo_ws_deps``); with
  none graphed it counts as external.
"""
from __future__ import annotations

import posixpath

from graphify.ids import make_id
from graphify.resolver_registry import LanguageResolver

from graphify_lang._common import source_of

_WS_PREFIX = "cargo_workspace_"


def _folder(source_file: str) -> str:
    return posixpath.dirname(posixpath.normpath(str(source_file).replace("\\", "/")))


def _glob_match(pattern: str, rel: str) -> bool:
    from graphify_lang.registry import _glob_re
    pattern = posixpath.normpath(pattern.replace("\\", "/"))
    return bool(_glob_re(pattern).fullmatch(rel))


def _edge(source: str, target: str, relation: str, context: str, src: str) -> dict:
    return {"source": source, "target": target, "relation": relation, "context": context,
            "confidence": "EXTRACTED", "confidence_score": 1.0, "source_file": src,
            "source_location": "L1", "weight": 1.0}


def resolve(per_file: list, all_nodes: list, all_edges: list) -> None:
    crates: dict[str, dict] = {}               # manifest folder -> crate node
    workspaces: dict[str, dict] = {}           # manifest folder -> workspace node
    by_id: dict[str, dict] = {}
    for n in all_nodes:
        sf = source_of(n)
        if not sf.endswith("Cargo.toml"):
            continue
        if n.get("type") == "workspace" and str(n.get("id", "")).startswith(_WS_PREFIX):
            workspaces.setdefault(_folder(sf), n)
        elif n.get("type") == "package":
            crates.setdefault(_folder(sf), n)
        by_id.setdefault(n["id"], n)

    seen = {(e.get("source"), e.get("target"), e.get("relation")) for e in all_edges}

    def add(src: str, tgt: str, relation: str, context: str, sf: str) -> None:
        if src != tgt and (src, tgt, relation) not in seen:
            seen.add((src, tgt, relation))
            all_edges.append(_edge(src, tgt, relation, context, sf))

    def ws_deps(folder: str) -> dict[str, tuple[str, bool]] | None:
        while True:
            ws = workspaces.get(folder)
            if ws is not None:
                out = {}
                for entry in ws.get("cargo_ws_deps") or ():
                    key, _, rest = entry.partition("=")
                    out[key] = (rest.removesuffix("@path"), rest.endswith("@path"))
                return out
            parent = posixpath.dirname(folder)
            if parent == folder:
                return None
            folder = parent

    for res in per_file:
        refs = res.get("cargo_refs") if isinstance(res, dict) else None
        if not refs:
            continue
        sf = refs["source_file"]
        folder = _folder(sf)
        ws = refs.get("workspace")
        if ws:
            exclude = {posixpath.normpath(posixpath.join(folder, e)) for e in ws["exclude"]}
            members = []
            for crate_dir, crate in crates.items():
                if crate_dir in exclude:
                    continue
                rel = posixpath.relpath(crate_dir, folder)
                if any(_glob_match(p, rel) for p in ws["members"]):
                    members.append(crate)
            if refs.get("crate") and folder in crates:
                members.append(crates[folder])
            for crate in sorted(members, key=lambda n: n["id"]):
                add(ws["id"], crate["id"], "has_member", "workspace_member", sf)
        crate = refs.get("crate")
        if crate:
            external, renamed = set(crate["external"]), set(crate["renamed"])
            inherited = ws_deps(folder) if crate["inherit"] else {}
            for entry in crate["inherit"]:
                key, _, rest = entry.partition("=")
                own_package, own_path = rest.removesuffix("@path"), rest.endswith("@path")
                ws_package, ws_path = (inherited or {}).get(key, (None, False))
                name = own_package or ws_package or key
                if not (own_path or ws_path):
                    external.add(name)
                elif name != key:
                    renamed.add(name)
            node = by_id.get(crate["id"])
            if external and node is not None and "external_deps" not in node:
                node["external_deps"] = sorted(external)
            for dep in sorted(renamed):
                add(crate["id"], make_id("pkg", dep), "depends_on", "dependency", sf)


RESOLVER = LanguageResolver(name="cargo", suffixes=frozenset({".toml"}), resolve=resolve)
