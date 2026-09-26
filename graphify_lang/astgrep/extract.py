"""ast-grep project YAML extractor for graphify-lang (plan 04 §3.4, S11).

One file node per file, stamped ``astgrep_role``: ``sgconfig``, ``rule``,
``util``, ``test`` or ``snapshot`` (from the keys of its first document; a
rule-shaped document under a ``utils/`` directory is a util). Each YAML
document (``---``-separated) with a scalar ``id`` gives:

- a rule: a ``rule`` node (``language``, ``severity`` as attrs), and a ``util``
  node per local ``utils:`` entry, which the rule contains;
- a global util: a ``util`` node (``astgrep_scope = "global"``);
- a test / snapshot: nothing beyond the file node's ``astgrep_id``.

``matches: <util>`` gives a ``references`` edge here when a local util of the
same document has that id. Everything cross-file is left on the result as
``astgrep_refs`` for ``resolve.py``: global util references, a test or
snapshot's rule id, and the ``ruleDirs`` / ``utilDirs`` of an sgconfig.

PyYAML (a runtime dependency) parses each document. A document that does not
parse adds nothing; any other error stops the document, keeps what it added
so far and logs the exception type (S1-L2).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from graphify_lang._common import Sink, _make_id, line_index

_LOG = logging.getLogger(__name__)
_DOC_SPLIT_RE = re.compile(r"^---[ \t]*(?:#.*)?$", re.MULTILINE)
_INDENTED_KEY_RE = re.compile(r"^[ \t]+([^:\n]*):", re.MULTILINE)


def _matches(obj, seen: set[int] | None = None) -> list[str]:
    """Every ``matches: <id>`` value under ``obj``.

    Each dict / list is visited once (``seen`` holds their ids): YAML aliases
    share subtrees, so without it N levels of 10 aliases cost 10^N visits and a
    self-referencing alias never ends (cc-CR000.001 H4).
    """
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


def _key_line(line_of, text: str, first: int, pattern: str) -> int:
    m = re.search(pattern, text, re.MULTILINE)
    return first + line_of(m.start()) - 1 if m else first


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


def _rule_doc(out: Sink, doc: dict, text: str, first: int, role: str, line_of) -> None:
    rid = str(doc["id"])
    line = _key_line(line_of, text, first, r"^id:")
    attrs = {k: str(doc[k]) for k in ("language", "severity") if isinstance(doc.get(k), (str, int))}
    if role == "util":
        owner = out.add(_make_id(out.stem, "util", rid), rid, "util", line,
                        astgrep_scope="global", **attrs)
    else:
        owner = out.add(_make_id(out.stem, "rule", rid), rid, "rule", line, **attrs)
    out.edge(out.file_nid, owner, "contains", line)
    local: dict[str, str] = {}
    utils = doc.get("utils") if isinstance(doc.get("utils"), dict) else {}
    # S1-M1: every indented key's first offset in one pass (what a re.search per
    # util returned), not a scan from the document start per util.
    keys: dict[str, int] = {}
    for m in _INDENTED_KEY_RE.finditer(text):
        keys.setdefault(m.group(1), m.start())
    for uid in map(str, utils):
        if uid in keys:
            uline = first + line_of(keys[uid]) - 1
        elif ":" in uid or uid != uid.lstrip():  # a key the one-pass capture cannot hold
            uline = _key_line(line_of, text, first, rf"^[ \t]+{re.escape(uid)}:")
        else:
            uline = first
        local[uid] = out.add(_make_id(owner, "util", uid), uid, "util", uline,
                             astgrep_scope="local")
        out.edge(owner, local[uid], "contains", uline)
    uses = [(owner, line, _matches({k: v for k, v in doc.items() if k != "utils"}))]
    uses += [(local[str(u)], line, _matches(body)) for u, body in utils.items()]
    for src, ln, names in uses:
        for name in dict.fromkeys(names):
            if name in local:
                out.edge(src, local[name], "references", ln)
            else:
                out.ref("util", src, name=name, line=ln)


def _document(out: Sink, path: Path, chunk: str, first: int) -> None:
    """One ``---``-separated document; an error stops it (the caller logs)."""
    doc = yaml.safe_load(chunk)
    if not isinstance(doc, dict):
        return
    role = _role(doc, path)
    line_of = line_index(chunk)
    if "astgrep_role" not in out.nodes[0]:
        out.nodes[0]["astgrep_role"] = role
    if role == "sgconfig":
        tests = doc.get("testConfigs") if isinstance(doc.get("testConfigs"), list) else []
        test_dirs = [str(t["testDir"]) for t in tests
                     if isinstance(t, dict) and isinstance(t.get("testDir"), (str, int))
                     and str(t["testDir"])]
        for key in ("ruleDirs", "utilDirs"):
            for d in _dirs(doc.get(key)):
                out.ref("dir", out.file_nid, name=d, line=_key_line(line_of, chunk, first, rf"^{key}:"))
        out.nodes[0].update({"rule_dirs": _dirs(doc.get("ruleDirs")),
                             "util_dirs": _dirs(doc.get("utilDirs")),
                             "test_dirs": test_dirs})
        return
    if not isinstance(doc.get("id"), (str, int)):  # S1-H1: never str() an alias tree
        return
    if role in ("test", "snapshot"):
        out.nodes[0].setdefault("astgrep_id", str(doc["id"]))
        out.ref(role, out.file_nid, name=str(doc["id"]), line=_key_line(line_of, chunk, first, r"^id:"))
        return
    _rule_doc(out, doc, chunk, first, role, line_of)


def extract_astgrep(path: Path) -> dict:
    """Extract one ast-grep project YAML file (plan 04 §3.4)."""
    path = Path(path)
    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    out = Sink(path)
    for first, chunk in _documents(text):
        try:
            _document(out, path, chunk, first)
        except yaml.YAMLError as exc:  # nothing added yet
            _LOG.warning("astgrep: %s line %d: document skipped (YAML does not parse): %s",
                         path, first, (str(exc).splitlines() or [""])[0])
        except Exception as exc:  # keep the file node, never crash (H4)
            _LOG.warning("astgrep: %s line %d: document stopped at %s: %s; nodes added"
                         " before it are kept (S1-L2)", path, first, type(exc).__name__,
                         (str(exc).splitlines() or [""])[0])
    return out.result("astgrep_refs")
