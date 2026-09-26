"""Shared plugin core (plan 05 S3, cc-CR000.001 E2): the id, sink and resolver
contracts every plugin follows, in one place.

- ``_make_id`` / ``_file_stem``: upstream's helpers, imported lazily (a
  top-level ``graphify.extractors`` import at plugin load re-enters
  ``graphify.detect`` while it is still loading the registry).
- ``Sink``: nodes, edges and resolver refs for one file. The file node id is
  ``_make_id(str(path))``, suffix included, as the built-in extractors mint it,
  so upstream's portable-id remap applies and ``x.lsp`` / ``x.mnl`` salt apart
  without the scan root in the id (M4). Symbol ids stay ``stem``-based.
- Refs store ``node``, the index of their source node in the result's
  ``nodes``; ``resolve_ref_id`` reads the current id back, because upstream
  renames colliding ids in place before resolvers run (H2, ltm learning 1477).
- ``source_of``: a node's path in the fresh nodes' form, for any node the
  resolver compares by path (incremental context nodes are root-relative).
- ``is_file_node``: a file node by upstream's own test, so the path-suffix
  label a colliding basename persists (#2032) still counts (T38).
- ``pick_by_prefix``: one candidate, or the one sharing the longest directory
  prefix with the source (INFERRED); a tie resolves to nothing.
- ``load_manifest`` / ``load_builtins``: a package's TOML manifest and its
  ``builtins_file`` / ``builtins_prefixes`` / ``case_insensitive`` filter.
- ``line_index``: offset -> line for one text, built once per extraction.
"""
from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import replace
from pathlib import Path
from typing import Callable

from graphify_lang.builtins import Builtins
from graphify_lang.manifest import LanguageManifest, tomllib


def _file_stem(path):
    from graphify.extractors.base import _file_stem as f
    return f(path)


def _make_id(*parts):
    from graphify.extractors.base import _make_id as f
    return f(*parts)


def line_index(text: str) -> Callable[[int], int]:
    """1-based line of an offset in ``text``: newline offsets built once, then a
    bisect per lookup, not a count from the start (cc-CR000.001 N4). The caller
    holds it for one extraction, so no module cache keeps the text alive (S1-N2)."""
    newlines = [m.start() for m in re.finditer("\n", text)]
    return lambda pos: bisect_left(newlines, pos) + 1


class Sink:
    """Node / edge / ref sink for one file."""

    def __init__(self, path: Path, builtins: Builtins | None = None) -> None:
        self.sf = str(path)
        self.stem = _make_id(_file_stem(path))
        self.builtins = builtins or Builtins()
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.refs: list[dict] = []
        self._ids: set[str] = set()
        self._order: dict[str, int] = {}
        self._edge_keys: set[tuple] = set()
        self.file_nid = self.add(_make_id(str(path)), Path(path).name, "file", 1)

    def add(self, nid: str, label: str, kind: str, line: int, **attrs) -> str:
        """Append a node; a clash gets ``_l<line>``. Returns the id used."""
        if nid in self._ids:
            nid = f"{nid}_l{line}"
        self._ids.add(nid)
        self._order[nid] = len(self.nodes)
        self.nodes.append({"id": nid, "label": label, "file_type": "code", "node_kind": kind,
                           "source_file": self.sf, "source_location": f"L{line}", **attrs})
        return nid

    def node(self, kind: str, label: str, line: int, **attrs) -> str:
        """A symbol ``<stem>_<label>`` (label case-folded when the manifest says
        ``case_insensitive``) that the file contains."""
        nid = self.add(_make_id(self.stem, self.builtins.fold(label)), label, kind, line, **attrs)
        self.edge(self.file_nid, nid, "contains", line)
        return nid

    def edge(self, src: str, tgt: str, relation: str, line: int,
             confidence: str = "EXTRACTED", *, self_loop: bool = False) -> None:
        """One edge per (src, tgt, relation); ``src == tgt`` only with ``self_loop``."""
        if (src == tgt and not self_loop) or (src, tgt, relation) in self._edge_keys:
            return
        self._edge_keys.add((src, tgt, relation))
        self.edges.append({"source": src, "target": tgt, "relation": relation,
                           "confidence": confidence, "source_file": self.sf,
                           "source_location": f"L{line}", "weight": 1.0})

    def ref(self, kind: str, source: str, line: int, *, unique: bool = False, **fields) -> None:
        """A resolver ref from node ``source``; ``unique`` drops a repeat of the
        same kind, source and fields."""
        if unique:
            key = (kind, source, *sorted(fields.items()))
            if key in self._edge_keys:
                return
            self._edge_keys.add(key)
        self.refs.append({"kind": kind, "node": self._order[source], "line": line,
                          "source_file": self.sf, **fields})

    def result(self, refs_key: str) -> dict:
        return {"nodes": self.nodes, "edges": self.edges, refs_key: self.refs}


def source_of(node: dict) -> str:
    """A node's source path as the fresh nodes carry it during resolution: an
    unchanged file's context node (incremental build) has the root-relative
    ``source_file`` and, from the registry hook, its absolute form (H1)."""
    return str(node.get("_lang_source_file") or node.get("source_file", ""))


def is_file_node(node: dict) -> bool:
    """Whether ``node`` is its file's node: label = the basename, or the
    shortest unique path suffix upstream persists when basenames collide
    (#2032). An incremental build's context nodes carry that suffix (T38)."""
    from graphify.build import _is_file_node_label
    return _is_file_node_label(node.get("label"), source_of(node))


def resolve_ref_id(res: dict, ref: dict) -> str | None:
    """The current id of a ref's source node (salted by now if it collided).
    A ref without a valid ``node`` comes from a pre-S3 AST cache entry (S3-M1):
    its ``source`` id, or None, so a stale entry degrades one file only."""
    i = ref.get("node")
    if isinstance(i, int) and 0 <= i < len(res.get("nodes", ())):
        return res["nodes"][i]["id"]
    return ref.get("source")


def refs_of(per_file: list, refs_key: str) -> list[dict]:
    """Every ``refs_key`` ref of the corpus, ``source`` set to its current id;
    a ref whose source cannot be found is dropped."""
    return [{**r, "source": src} for res in per_file
            if isinstance(res, dict) and res.get(refs_key) for r in res[refs_key]
            if (src := resolve_ref_id(res, r))]


def pick_by_prefix(found: list[dict], source_file: str) -> tuple[str | None, str]:
    """(target id, confidence). One candidate: EXTRACTED. Several: the one sharing
    the longest directory prefix with ``source_file``, INFERRED (an archived copy
    must not capture live references); a tie on that prefix: None."""
    if len(found) <= 1:
        return (found[0]["id"] if found else None), "EXTRACTED"
    caller = Path(source_file).parts

    def shared(node: dict) -> int:
        n = 0
        for a, b in zip(caller, Path(source_of(node)).parts):
            if a != b:
                break
            n += 1
        return n
    scores = sorted(((shared(n), n["id"]) for n in found), reverse=True)
    if scores[0][0] == scores[1][0]:
        return None, "EXTRACTED"
    return scores[0][1], "INFERRED"


def load_manifest(pkg_file: str, toml: str, **fields) -> LanguageManifest:
    """The manifest ``toml`` beside ``pkg_file`` with ``fields`` (``extract=``,
    ``resolver=``, ``augment=``) set; a manifest error raises ``ValueError``."""
    manifest, errors = LanguageManifest.from_toml(Path(pkg_file).parent / toml)
    if errors:
        raise ValueError(f"{toml}: {errors}")
    return replace(manifest, **fields)


def load_builtins(pkg_file: str, toml: str) -> Builtins:
    """The builtins filter the manifest ``toml`` beside ``pkg_file`` declares."""
    path = Path(pkg_file).parent / toml
    return Builtins.from_manifest(path, tomllib.loads(path.read_text(encoding="utf-8")))
