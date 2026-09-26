"""VBA (.bas / .cls / .frm) extractor for graphify-lang (plan 04 §3.4, D7).

A line scanner, no grammar. Physical lines are joined on `` _`` continuations,
string literals are blanked and comments (``'`` and ``Rem``) cut before any
pattern runs. Nodes: the file, one module / class / form (``Attribute
VB_Name``, else the file stem), and its ``Sub`` / ``Function`` / ``Property``,
``Declare``, ``Type`` and ``Enum`` members; the file contains the module, the
module contains its members. Same-module calls and type uses become edges
here; cross-module calls, ``Implements`` and uses of other modules' types are
left on the result as ``vba_refs`` for ``resolve.py``.
"""
from __future__ import annotations

import codecs
import re
from functools import lru_cache
from pathlib import Path

from graphify_lang._common import Sink, _make_id, load_builtins


_MODULE_KIND = {".bas": "module", ".cls": "class", ".frm": "form"}

_NAME_RE = re.compile(r'^attribute\s+vb_name\s*=\s*"([^"]+)"', re.I)
_PROC_RE = re.compile(r"^(?:(public|private|friend|global)\s+)?(?:static\s+)?"
                      r"(sub|function|property\s+(get|let|set))\s+(\w+)(.*)$", re.I)
_DECLARE_RE = re.compile(r"^(?:(public|private)\s+)?declare\s+(?:ptrsafe\s+)?"
                         r"(?:sub|function)\s+(\w+)", re.I)
_BLOCK_RE = re.compile(r"^(?:(public|private)\s+)?(type|enum)\s+(\w+)\s*$", re.I)
_END_RE = re.compile(r"^end\s+(sub|function|property|type|enum)\b", re.I)
_IMPLEMENTS_RE = re.compile(r"^implements\s+(\w+)\s*$", re.I)
_DECL_RE = re.compile(r"^(?:dim|static|redim(?:\s+preserve)?|const|private|public|global)\s+"
                      r"(?:withevents\s+|const\s+)?(.*)$", re.I)
_VAR_RE = re.compile(r"^(?:(?:optional|byval|byref|paramarray)\s+)*(\w+)[$%&!#@]?"
                     r"(?:\s+as\s+(?:new\s+)?([\w.]+))?", re.I)
_TYPE_REF_RE = re.compile(r"\b(?:as\s+(?:new\s+)?|new\s+)([A-Za-z]\w*(?:\.\w+)?)", re.I)
_CHAIN_RE = re.compile(r"(?<![\w.$%&!#@])([A-Za-z]\w*(?:[ \t]*\.[ \t]*[A-Za-z]\w*)?)")
_STRING_RE = re.compile(r'"[^"]*"')
_PARENS_RE = re.compile(r"\([^()]*\)")


@lru_cache(maxsize=1)
def _builtins():
    """The manifest's builtins filter (``builtins_file``, ``case_insensitive``)."""
    return load_builtins(__file__, "graphify-lang.toml")


def is_builtin(name: str) -> bool:
    """VBA keywords, intrinsic types and VBA-library routines never become refs."""
    return _builtins().is_builtin(name)


def decode(raw: bytes) -> str:
    """UTF-8 (BOM stripped) when it decodes, else Windows-1252; never raises."""
    raw = raw.removeprefix(codecs.BOM_UTF8)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _code(line: str) -> str:
    """A logical line with string contents blanked and the comment cut."""
    line = _STRING_RE.sub('""', line)
    cut = line.find("'")
    if cut >= 0:
        line = line[:cut]
    if line.lstrip()[:4].casefold() in ("rem", "rem ", "rem\t"):
        return ""
    return line.strip()


def statements(text: str) -> list[tuple[int, str]]:
    """(first physical line, code) per statement: `` _`` joined, ``:`` split."""
    out: list[tuple[int, str]] = []
    buf, start = "", 0
    for i, physical in enumerate(text.splitlines(), 1):
        if not buf:
            start = i
        stripped = physical.rstrip()
        if stripped == "_" or stripped.endswith((" _", "\t_")):
            buf += stripped[:-1] + " "
            continue
        code = _code(buf + physical)
        buf = ""
        for stmt in re.split(r":(?!=)", code):  # strings already blanked
            if stmt.strip():
                out.append((start, stmt.strip()))
    return out


def _params(rest: str) -> str:
    """The parameter list of a procedure header's tail ``(a As X, b() As Y) As Z``."""
    rest = rest.strip()
    if not rest.startswith("("):
        return ""
    depth = 0
    for i, ch in enumerate(rest):
        depth += (ch == "(") - (ch == ")")
        if depth == 0:
            return rest[1:i]
    return rest[1:]


def _variables(decl: str) -> list[tuple[str, str | None]]:
    """(name, type) for each item of a Dim / parameter list."""
    while _PARENS_RE.search(decl):
        decl = _PARENS_RE.sub("", decl)
    out = []
    for item in decl.split(","):
        m = _VAR_RE.match(item.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def extract_vba(path: Path) -> dict:
    """Extract one VBA module, class module or form (plan 04 §3.4)."""
    try:
        text = decode(Path(path).read_bytes())
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    path = Path(path)
    stmts = statements(text)
    out = Sink(path, _builtins())
    name = next((m.group(1) for _, s in stmts if (m := _NAME_RE.match(s))), path.stem)
    module = out.add(_make_id(out.stem, name), name,
                     _MODULE_KIND.get(path.suffix.lower(), "module"), 1)
    out.edge(out.file_nid, module, "contains", 1)

    # Pass 1: members and the module-level variables.
    members: dict[str, list[tuple[str, str]]] = {}  # folded name -> (node id, accessor)
    types: dict[str, str] = {}                    # folded Type / Enum name -> node id
    module_vars: dict[str, str | None] = {}       # folded name -> declared type
    bodies: list[tuple[str, str, str, int, list]] = []  # (nid, name, header rest, line, body)
    owner = None                                  # (nid, kind) of the open block
    for line, s in stmts:
        if owner is not None:
            nid, kind, body = owner
            if (end := _END_RE.match(s)) and end.group(1).casefold() == kind:
                owner = None
            else:
                body.append((line, s))
            continue
        if m := _PROC_RE.match(s):
            vis, word, accessor, pname, rest = m.groups()
            kind = "property" if accessor else word.casefold()
            attrs = {"visibility": (vis or "public").casefold()}
            if accessor:
                attrs["accessor"] = accessor.casefold()
            nid = out.add(_make_id(out.stem, pname.casefold()), pname, kind, line, **attrs)
            out.edge(module, nid, "contains", line)
            members.setdefault(pname.casefold(), []).append((nid, attrs.get("accessor", "")))
            owner = (nid, "property" if accessor else word.casefold(), [])
            bodies.append((nid, pname, rest, line, owner[2]))
        elif m := _DECLARE_RE.match(s):
            nid = out.add(_make_id(out.stem, m.group(2).casefold()), m.group(2), "declare", line,
                          visibility=(m.group(1) or "public").casefold())
            out.edge(module, nid, "contains", line)
            members.setdefault(m.group(2).casefold(), []).append((nid, ""))
        elif m := _BLOCK_RE.match(s):
            kind = m.group(2).casefold()
            nid = out.add(_make_id(out.stem, m.group(3).casefold()), m.group(3), kind, line,
                          visibility=(m.group(1) or "public").casefold())
            out.edge(module, nid, "contains", line)
            types[m.group(3).casefold()] = nid
            owner = (nid, kind, [])
            bodies.append((nid, m.group(3), "", line, owner[2]))
        elif m := _IMPLEMENTS_RE.match(s):
            out.ref("implements", module, line, name=m.group(1))
        elif m := _DECL_RE.match(s):
            for var, vtype in _variables(m.group(1)):
                module_vars[var.casefold()] = vtype
            _uses(out, module, s, line, types)

    # Pass 2: calls and type uses inside each body.
    own = name.casefold()
    for nid, pname, rest, line, body in bodies:
        if nid in types.values():
            for bline, s in body:  # Type fields `x As T`; Enum members have none
                _uses(out, nid, s, bline, types)
            continue
        _uses(out, nid, rest, line, types)
        local = dict(module_vars)
        local.update((v.casefold(), t) for v, t in _variables(_params(rest)))
        local[pname.casefold()] = None  # `Name = x` in Function / Property Name is its result
        for bline, s in body:
            if s[:10].casefold() == "attribute ":
                continue
            if m := _DECL_RE.match(s):
                if not s.casefold().startswith(("private", "public", "global")):
                    local.update((v.casefold(), t) for v, t in _variables(m.group(1)))
            _uses(out, nid, s, bline, types)
            _calls(out, nid, s, bline, own, local, members)
    return out.result("vba_refs")


def _uses(out: Sink, src: str, s: str, line: int, types: dict[str, str]) -> None:
    for m in _TYPE_REF_RE.finditer(s):
        tname = m.group(1)
        if "." in tname or is_builtin(tname):
            continue  # library-qualified (Scripting.Dictionary) or intrinsic
        if tname.casefold() in types:
            out.edge(src, types[tname.casefold()], "uses", line)
        else:
            out.ref("uses", src, line, name=tname)


def accessor_match(found: list[tuple[str, str]], accessor: str) -> list[str]:
    """Node ids a use reaches: a property only through the matching accessor."""
    return [nid for nid, acc in found if not acc or acc == accessor]


def _calls(out: Sink, src: str, s: str, line: int, own: str,
           local: dict[str, str | None], members: dict[str, list[tuple[str, str]]]) -> None:
    skip_after = {"as", "new", "is", "goto", "gosub", "resume"}
    prev = ""
    for m in _CHAIN_RE.finditer(s):
        parts = [p.strip() for p in m.group(1).split(".")]
        after = s[m.end():].lstrip()
        word, prev = prev, parts[0].casefold()
        if word in skip_after or after.startswith(":="):
            continue  # a type name, a label, or a named argument
        head = parts[0].casefold()
        # `x.P = v` / `Set x.P = o` is a Property Let / Set; any other use is a Get.
        lead = s[:m.start()].strip().casefold()
        accessor = "get"
        if after.startswith("=") and lead in ("", "let", "set"):
            accessor = "set" if lead == "set" else "let"
        if len(parts) == 1 or head == "me" or head == own:
            name = parts[-1]
            folded = name.casefold()
            if len(parts) == 1 and folded in local:
                continue
            if folded in members:
                for target in accessor_match(members[folded], accessor):
                    out.edge(src, target, "calls", line)
            elif len(parts) == 1 and not is_builtin(name):
                out.ref("call", src, line, name=name, accessor=accessor)
        elif head in local:
            if local[head] and "." not in local[head]:  # obj.Method, obj declared As Class
                out.ref("call", src, line, name=parts[1], qualifier=local[head], accessor=accessor)
        elif not is_builtin(parts[0]):
            out.ref("call", src, line, name=parts[1], qualifier=parts[0], accessor=accessor)  # Module.Proc
