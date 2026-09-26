"""ast-grep project YAML extractor for graphify-lang (plan 04 §3.4, S11).

One file node per file, stamped ``astgrep_role``: ``sgconfig``, ``rule``,
``util``, ``test`` or ``snapshot`` (from the keys of its first document; a
rule-shaped document under a ``utils/`` directory is a util). Each YAML
document (``---``-separated) with an ``id`` gives:

- a rule: a ``rule`` node (``language``, ``severity`` as attrs), and a ``util``
  node per local ``utils:`` entry, which the rule contains;
- a global util: a ``util`` node (``astgrep_scope = "global"``);
- a test / snapshot: nothing beyond the file node's ``astgrep_id``.

``matches: <util>`` gives a ``references`` edge here when a local util of the
same document has that id. Everything cross-file is left on the result as
``astgrep_refs`` for ``resolve.py``: global util references, a test or
snapshot's rule id, and the ``ruleDirs`` / ``utilDirs`` of an sgconfig.

PyYAML is used when importable; it is not a graphify dependency, so without it
a flat parser reads the top-level keys this module needs. A document that does
not parse keeps the file node only and logs a warning.
"""
from __future__ import annotations

import logging
import re
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path

_LOG = logging.getLogger(__name__)

try:
    import yaml as _yaml
except ImportError:  # not a graphify dependency (upstream treats it as optional too)
    _yaml = None


def _file_stem(path):
    # Lazy: graphify.extractors at plugin load re-enters graphify.detect (see autolisp).
    from graphify.extractors.base import _file_stem as f
    return f(path)


def _make_id(*parts):
    from graphify.extractors.base import _make_id as f
    return f(*parts)


_DOC_SPLIT_RE = re.compile(r"^---[ \t]*(?:#.*)?$", re.MULTILINE)
_TOP_RE = re.compile(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*$")
_CHILD_KEY_RE = re.compile(r"^([ \t]+)(?:-[ \t]+)?([\w.-]+):(?:[ \t]+(.*?))?[ \t]*$")
# A ``matches:`` key: at a line start (after an optional ``- ``) or in a flow map.
_MATCHES_RE = re.compile(r"(?:^[ \t]*(?:-[ \t]+)?|[{,][ \t]*)matches:[ \t]*['\"]?([\w.-]+)",
                         re.MULTILINE)


def _scalar(value: str | None):
    if value is None or value in ("", "|", ">", "|-", ">-"):
        return None
    value = re.sub(r"[ \t]+#.*$", "", value).strip()
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(v) for v in value[1:-1].split(",") if v.strip()]
    return value.strip("'\"")


def _flat_load(text: str) -> dict:
    """Top-level keys only: a scalar, a list (of scalars or ``- key: value``
    maps), or the child keys of a mapping. Fallback when PyYAML is absent.

    ponytail: nested rule trees are not parsed; ``matches:`` is found by regex
    over the whole document (``_matches``), so a local util's references are
    credited to its rule. Install PyYAML for exact attribution.
    """
    out: dict = {}
    key, indent = None, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            m = _TOP_RE.match(line)
            key, indent = (m.group(1), None) if m else (None, None)
            if m:
                out[key] = _scalar(m.group(2))
            continue
        if key is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and (indent is None or len(line) - len(line.lstrip()) <= indent):
            indent = len(line) - len(line.lstrip())
            if not isinstance(out[key], list):
                out[key] = []
            m = _CHILD_KEY_RE.match(line)
            out[key].append({m.group(2): _scalar(m.group(3))} if m else _scalar(stripped[2:]))
            continue
        m = _CHILD_KEY_RE.match(line)
        if m and not isinstance(out[key], list) and (indent is None or len(m.group(1)) == indent):
            indent = len(m.group(1))
            if not isinstance(out[key], dict):
                out[key] = {}
            out[key][m.group(2)] = _scalar(m.group(3))
    return out


def _load(text: str):
    return _yaml.safe_load(text) if _yaml is not None else _flat_load(text)


def _matches(obj, text: str | None = None, seen: set[int] | None = None) -> list[str]:
    """Every ``matches: <id>`` value under ``obj``; the regex scan of ``text``
    when the tree was not parsed (flat fallback).

    Each dict / list is visited once (``seen`` holds their ids): YAML aliases
    share subtrees, so without it N levels of 10 aliases cost 10^N visits and a
    self-referencing alias never ends (cc-CR000.001 H4).
    """
    if _yaml is None:
        return _MATCHES_RE.findall(text or "") if text is not None else []
    if not isinstance(obj, (dict, list)):
        return []
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return []
    seen.add(id(obj))
    if isinstance(obj, dict):
        return [x for k, v in obj.items()
                for x in ([str(v)] if k == "matches" and isinstance(v, (str, int))
                          else _matches(v, seen=seen))]
    return [x for v in obj for x in _matches(v, seen=seen)]


def _documents(text: str) -> list[tuple[int, str]]:
    """(first line, text) per ``---``-separated document."""
    docs, start, pos = [], 1, 0
    for m in _DOC_SPLIT_RE.finditer(text):
        docs.append((start, text[pos:m.start()]))
        start += text.count("\n", pos, m.end()) + 1
        pos = m.end() + 1
    docs.append((start, text[pos:]))
    return [(ln, t) for ln, t in docs if t.strip()]


@lru_cache(maxsize=4)
def _newlines(text: str) -> tuple[int, ...]:
    return tuple(m.start() for m in re.finditer("\n", text))


def _line_of(text: str, pos: int) -> int:
    """1-based line of offset ``pos``: a bisect over newline offsets built once
    per text, not a count from the start per match (cc-CR000.001 N4)."""
    return bisect_left(_newlines(text), pos) + 1


def _key_line(text: str, first: int, pattern: str) -> int:
    m = re.search(pattern, text, re.MULTILINE)
    return first + _line_of(text, m.start()) - 1 if m else first


def _role(doc: dict, path: Path) -> str:
    if "ruleDirs" in doc:
        return "sgconfig"
    if "snapshots" in doc:
        return "snapshot"
    if "valid" in doc or "invalid" in doc:
        return "test"
    if any(p.lower() == "utils" for p in path.parent.parts):
        return "util"
    return "rule"


def _dirs(value) -> list[str]:
    items = value if isinstance(value, list) else [value]
    return [str(v) for v in items if isinstance(v, (str, int)) and str(v)]


class _Out:
    """Node / edge / ref sink for one file (the bmake plugin's shape)."""

    def __init__(self, path: Path) -> None:
        self.sf = str(path)
        self.stem = _make_id(_file_stem(path))
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.refs: list[dict] = []
        self._ids: set[str] = set()
        self._order: dict[str, int] = {}
        self._edge_keys: set[tuple[str, str, str]] = set()
        self.file_nid = self.add(self.stem, path.name, "file", 1)

    def add(self, nid: str, label: str, kind: str, line: int, **attrs) -> str:
        if nid in self._ids:
            nid = f"{nid}_l{line}"
        self._ids.add(nid)
        self._order[nid] = len(self.nodes)
        self.nodes.append({"id": nid, "label": label, "file_type": "code", "node_kind": kind,
                           "source_file": self.sf, "source_location": f"L{line}", **attrs})
        return nid

    def edge(self, src: str, tgt: str, relation: str, line: int) -> None:
        if src == tgt or (src, tgt, relation) in self._edge_keys:
            return
        self._edge_keys.add((src, tgt, relation))
        self.edges.append({"source": src, "target": tgt, "relation": relation,
                           "confidence": "EXTRACTED", "source_file": self.sf,
                           "source_location": f"L{line}", "weight": 1.0})

    def ref(self, kind: str, source: str, name: str, line: int) -> None:
        # The resolver reads the source id back through the node index (ids may be
        # salted apart before resolvers run; see bmake).
        self.refs.append({"kind": kind, "node": self._order[source], "name": name,
                          "line": line, "source_file": self.sf})


def _rule_doc(out: _Out, doc: dict, text: str, first: int, role: str) -> None:
    rid = str(doc["id"])
    line = _key_line(text, first, r"^id:")
    attrs = {k: str(doc[k]) for k in ("language", "severity") if isinstance(doc.get(k), (str, int))}
    if role == "util":
        owner = out.add(_make_id(out.stem, "util", rid), rid, "util", line,
                        astgrep_scope="global", **attrs)
    else:
        owner = out.add(_make_id(out.stem, "rule", rid), rid, "rule", line, **attrs)
    out.edge(out.file_nid, owner, "contains", line)
    local: dict[str, str] = {}
    utils = doc.get("utils") if isinstance(doc.get("utils"), dict) else {}
    for uid in map(str, utils):
        uline = _key_line(text, first, rf"^[ \t]+{re.escape(uid)}:")
        local[uid] = out.add(_make_id(owner, "util", uid), uid, "util", uline,
                             astgrep_scope="local")
        out.edge(owner, local[uid], "contains", uline)
    uses = [(owner, line, _matches({k: v for k, v in doc.items() if k != "utils"}, text))]
    uses += [(local[str(u)], line, _matches(body)) for u, body in utils.items()]
    for src, ln, names in uses:
        for name in dict.fromkeys(names):
            if name in local:
                out.edge(src, local[name], "references", ln)
            else:
                out.ref("util", src, name, ln)


def _document(out: _Out, path: Path, chunk: str, first: int) -> None:
    """One ``---``-separated document; any error skips it (the caller logs)."""
    doc = _load(chunk)
    if not isinstance(doc, dict):
        return
    role = _role(doc, path)
    if "astgrep_role" not in out.nodes[0]:
        out.nodes[0]["astgrep_role"] = role
    if role == "sgconfig":
        tests = doc.get("testConfigs") if isinstance(doc.get("testConfigs"), list) else []
        test_dirs = [str(t["testDir"]) for t in tests if isinstance(t, dict) and t.get("testDir")]
        for key in ("ruleDirs", "utilDirs"):
            for d in _dirs(doc.get(key)):
                out.ref("dir", out.file_nid, d, _key_line(chunk, first, rf"^{key}:"))
        out.nodes[0].update({"rule_dirs": _dirs(doc.get("ruleDirs")),
                             "util_dirs": _dirs(doc.get("utilDirs")),
                             "test_dirs": test_dirs})
        return
    if doc.get("id") is None:
        return
    if role in ("test", "snapshot"):
        out.nodes[0].setdefault("astgrep_id", str(doc["id"]))
        out.ref(role, out.file_nid, str(doc["id"]), _key_line(chunk, first, r"^id:"))
        return
    _rule_doc(out, doc, chunk, first, role)


def extract_astgrep(path: Path) -> dict:
    """Extract one ast-grep project YAML file (plan 04 §3.4)."""
    path = Path(path)
    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    out = _Out(path)
    for first, chunk in _documents(text):
        try:
            _document(out, path, chunk, first)
        except Exception as exc:  # keep the file node, never crash (H4)
            _LOG.warning("astgrep: %s line %d: document skipped (YAML does not parse"
                         " or is malformed): %s", path, first,
                         str(exc).splitlines()[0] if str(exc) else exc)
    return {"nodes": out.nodes, "edges": out.edges, "astgrep_refs": out.refs}
