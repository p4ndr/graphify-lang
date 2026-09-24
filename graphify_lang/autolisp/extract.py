"""AutoLISP (.lsp / .mnl) and DCL (.dcl) extractors for graphify-lang.

One purpose-built walker over the tree-sitter-commonlisp parse (plan 02 §3):
nodes are the file, each ``defun`` (``function`` / ``command``), each top-level
``*global*`` and each ``@module``; every one hangs off the file by ``contains``.
Calls whose target is defined in the same file become ``calls`` edges here;
everything that needs the whole corpus (cross-file calls, dialogs, ``@depends``,
``@sidecar``) is left on the result as ``autolisp_refs`` for ``resolve.py``.
"""
from __future__ import annotations

import os
import re
import warnings
from functools import lru_cache
from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id

_BUILTINS_FILE = Path(__file__).parent / "data" / "builtins.txt"
_COM_PREFIXES = ("vla-", "vlax-", "vlr-")  # A1
_DEFUN_RE = re.compile(r"^[ \t]*\(defun[ \t]+([^\s()]+)", re.M | re.I)
_HEADER_RE = re.compile(r"^[ \t]*;+[ \t]*@(module|depends|sidecar)[ \t]+(.+?)[ \t]*$", re.M)
_DIALOG_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*dialog\s*\{")
_DCL_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_GLOBAL_RE = re.compile(r"^\*[^*\s]+\*$")
_TOP_SETQ_RE = re.compile(r"^\(setq[ \t]+(\*[^*\s]+\*)", re.M | re.I)
_SYMBOLS = ("sym_lit", "package_lit")
_COMMENTS = ("comment", "block_comment")


@lru_cache(maxsize=1)
def _builtins() -> frozenset[str]:
    lines = _BUILTINS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(s.strip().casefold() for s in lines if s.strip() and not s.startswith(";"))


def is_builtin(name: str) -> bool:
    """A5 / A1: AutoLISP built-ins and COM calls never become call edges."""
    folded = name.casefold()
    return folded in _builtins() or folded.startswith(_COM_PREFIXES)


@lru_cache(maxsize=1)
def _parser():
    import tree_sitter_commonlisp as tscl
    from tree_sitter import Language, Parser

    with warnings.catch_warnings():
        # tree-sitter-commonlisp 0.4.1 returns an int pointer (see commonlisp.py).
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return Parser(Language(tscl.language()))


class _Out:
    """Node / edge sink for one file: ids, collisions, contains, de-dup."""

    def __init__(self, path: Path) -> None:
        self.sf = str(path)
        self.stem = _make_id(_file_stem(path))
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.refs: list[dict] = []
        self._ids: set[str] = set()
        self._edge_keys: set[tuple] = set()
        self.file_nid = self._add(self.stem, path.name, "file", 1)

    def _add(self, nid: str, label: str, kind: str, line: int, confidence: str | None = None) -> str:
        if nid in self._ids:
            nid = f"{nid}_l{line}"
        self._ids.add(nid)
        node = {"id": nid, "label": label, "file_type": "code", "node_kind": kind,
                "source_file": self.sf, "source_location": f"L{line}"}
        if confidence:
            node["confidence"] = confidence
        self.nodes.append(node)
        return nid

    def node(self, kind: str, label: str, line: int, confidence: str | None = None) -> str:
        nid = self._add(_make_id(self.stem, label.casefold()), label, kind, line, confidence)
        self.edge(self.file_nid, nid, "contains", line)
        return nid

    def edge(self, src: str, tgt: str, relation: str, line: int, confidence: str = "EXTRACTED") -> None:
        if (src, tgt, relation) in self._edge_keys:
            return
        self._edge_keys.add((src, tgt, relation))
        self.edges.append({"source": src, "target": tgt, "relation": relation,
                           "confidence": confidence, "source_file": self.sf,
                           "source_location": f"L{line}", "weight": 1.0})

    def ref(self, kind: str, source: str, name: str, line: int, **extra) -> None:
        self.refs.append({"kind": kind, "source": source, "name": name, "line": line,
                          "source_file": self.sf, **extra})

    def result(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges, "autolisp_refs": self.refs}


def _line(node) -> int:
    return node.start_point[0] + 1


def _kids(node) -> list:
    return [c for c in node.named_children if c.type not in _COMMENTS]


class _Walker:
    """Collects defuns, top-level globals, calls, dialog refs and action_tile strings."""

    def __init__(self, source: bytes) -> None:
        self.src = source
        self.defuns: list[tuple[str, int]] = []          # (name, line), in order
        self.globals: list[tuple[str, int]] = []         # top-level *x* setq targets
        self.calls: list[tuple[int, str, int]] = []      # (defun index, callee, line)
        self.dialogs: list[tuple[int, str, int, str]] = []  # (defun index, name, line, confidence)
        self.actions: list[tuple[int, str, str, int]] = []  # (defun index, key, action source, line)

    def text(self, node) -> str:
        return self.src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def string(self, node) -> str:
        return self.text(node)[1:-1]

    def define(self, name: str, line: int) -> int:
        self.defuns.append((name, line))
        return len(self.defuns) - 1

    def defun_name(self, header) -> str | None:
        """Name as written: from after the keyword to the lambda list (keeps ``C:a:b``)."""
        keyword = header.child_by_field_name("keyword")
        params = header.child_by_field_name("lambda_list")
        start = keyword.end_byte if keyword else header.start_byte
        end = params.start_byte if params else header.end_byte
        name = self.src[start:end].decode("utf-8", errors="replace").strip()
        return name or None

    def walk(self, node, owner: int | None, top: bool = False) -> None:
        kind = node.type
        if kind == "defun":
            header = next((c for c in node.children if c.type == "defun_header"), None)
            if header is not None:
                keyword = header.child_by_field_name("keyword")
                if keyword is not None and self.text(keyword).casefold() in ("defun", "defun-q"):
                    name = self.defun_name(header)
                    if name:
                        owner = self.define(name, _line(node))
            for child in _kids(node):
                if child is not header and child.type != "defun_header":
                    self.walk(child, owner)
            return
        if kind == "list_lit":
            self.walk_list(node, owner, top)
            return
        if kind in ("quoting_lit", "var_quoting_lit"):
            value = _kids(node)
            if not value:
                return
            value = value[-1]
            if value.type in _SYMBOLS:
                self.call(owner, value)
            elif value.type == "list_lit" and any(c.type == "defun" for c in value.children):
                self.walk(value, owner)  # quoted lambda is code; other quoted lists are data
            return
        for child in _kids(node):
            self.walk(child, owner)

    def call(self, owner: int | None, node) -> None:
        if owner is not None:
            name = self.text(node)
            if not is_builtin(name):
                self.calls.append((owner, name, _line(node)))

    def walk_list(self, node, owner: int | None, top: bool) -> None:
        kids = _kids(node)
        if not kids:
            return
        head = kids[0]
        if head.type not in _SYMBOLS:
            for child in kids:
                self.walk(child, owner)
            return
        verb = self.text(head).casefold()
        args = kids[1:]
        if verb == "defun-q" and args:  # the grammar leaves defun-q a plain list
            inner = self.define(self.text(args[0]), _line(node))
            for child in args[2:]:
                self.walk(child, inner)
            return
        if verb == "setq":
            if top:
                for target in args[0::2]:
                    name = self.text(target)
                    if target.type in _SYMBOLS and _GLOBAL_RE.match(name):
                        self.globals.append((name, _line(target)))
            for value in args[1::2]:
                self.walk(value, owner)
            return
        if verb == "cond":  # a clause head is a test value, not a call (plan 01 S007 task 3)
            for clause in args:
                for child in _kids(clause) if clause.type == "list_lit" else [clause]:
                    self.walk(child, owner)
            return
        if verb in ("quote", "function"):
            if args and args[0].type in _SYMBOLS:
                self.call(owner, args[0])
            return
        self.call(owner, head)
        if owner is not None:
            strings = [a for a in args if a.type == "str_lit"]
            if verb == "new_dialog" and args and args[0].type == "str_lit":
                self.dialogs.append((owner, self.string(args[0]), _line(node), "EXTRACTED"))
            elif verb == "action_tile" and len(args) >= 2 and args[0].type == args[1].type == "str_lit":
                self.actions.append((owner, self.string(args[0]), self.string(args[1]), _line(node)))
            else:
                # A dialog name passed to a wrapper (dtk:dcl-exec ... "lithp_mgr").
                for s in strings:
                    value = self.string(s)
                    if _IDENT_RE.match(value):
                        self.dialogs.append((owner, value, _line(s), "INFERRED"))
        for child in args:
            self.walk(child, owner)


def action_callees(action: str) -> list[str]:
    """Non-builtin list heads in an ``action_tile`` string, parsed as AutoLISP."""
    walker = _Walker(action.encode("utf-8"))
    root = _parser().parse(walker.src).root_node
    owner = walker.define("", 1)
    for child in _kids(root):
        walker.walk(child, owner)
    return [name for _, name, _ in walker.calls]


def _headers(out: _Out, text: str, path: Path) -> None:
    module_nid = None
    depends: list[tuple[str, int]] = []
    for m in _HEADER_RE.finditer(text):
        tag, value = m.group(1), m.group(2)
        line = text.count("\n", 0, m.start()) + 1
        if tag == "module" and module_nid is None:
            module_nid = out.node("module", value.split()[0], line)
        elif tag == "depends":
            depends += [(name, line) for name in re.split(r"[,\s]+", value) if name]
        elif tag == "sidecar":
            target = os.path.normpath(path.parent / value.split()[0])
            out.ref("sidecar", out.file_nid, target, line)
    for name, line in depends:
        out.ref("depends", module_nid or out.file_nid, name, line)


def extract_autolisp(path: Path) -> dict:
    """Extract one AutoLISP file (plan 02 §3)."""
    try:
        source = path.read_bytes()
        root = _parser().parse(source).root_node
    except Exception as exc:  # unreadable file or missing grammar
        return {"nodes": [], "edges": [], "error": str(exc)}
    text = source.decode("utf-8", errors="replace")
    out = _Out(path)
    _headers(out, text, path)

    walker = _Walker(source)
    for child in _kids(root):
        walker.walk(child, None, top=True)

    seen_globals: set[str] = set()
    for name, line in walker.globals:
        if name.casefold() not in seen_globals:
            seen_globals.add(name.casefold())
            out.node("global", name, line)

    nids: list[str] = []
    local: dict[str, list[str]] = {}
    for name, line in walker.defuns:
        kind = "command" if name.casefold().startswith("c:") else "function"
        nid = out.node(kind, name, line)
        nids.append(nid)
        local.setdefault(name.casefold(), []).append(nid)

    if root.has_error:  # A2: defuns tree-sitter lost after an ERROR node
        for m in _DEFUN_RE.finditer(text):
            name = m.group(1)
            if name.casefold() not in local:
                kind = "command" if name.casefold().startswith("c:") else "function"
                line = text.count("\n", 0, m.start()) + 1
                local[name.casefold()] = [out.node(kind, name, line, confidence="INFERRED")]
        for m in _TOP_SETQ_RE.finditer(text):
            name = m.group(1)
            if name.casefold() not in seen_globals:
                seen_globals.add(name.casefold())
                out.node("global", name, text.count("\n", 0, m.start()) + 1, confidence="INFERRED")

    for owner, name, line in walker.calls:
        caller = nids[owner]
        targets = local.get(name.casefold())
        if targets is None:
            out.ref("call", caller, name, line)
        elif len(targets) == 1 and targets[0] != caller:
            out.edge(caller, targets[0], "calls", line)
    for owner, name, line, confidence in walker.dialogs:
        out.ref("dialog", nids[owner], name, line, confidence=confidence)
    for owner, key, action, line in walker.actions:
        for callee in action_callees(action):
            out.ref("action", nids[owner], callee, line, key=key)
    return out.result()


def extract_dcl(path: Path) -> dict:
    """Extract one DCL file: the file node and a ``dialog`` node per ``name : dialog {``."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    # Blank comments but keep their newlines so line numbers hold.
    text = _DCL_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    out = _Out(path)
    for m in _DIALOG_RE.finditer(text):
        out.node("dialog", m.group(1), text.count("\n", 0, m.start()) + 1)
    return out.result()
