"""Bentley ECSchema XML extractor for graphify-lang (plan 04 §3.4, S12).

One file node, one ``schema`` node (``ec_version`` 2.0 / 3.x from the XML
namespace), and under it:

- a ``class`` node per class element, ``ec_kind`` = ``entity``, ``struct``,
  ``custom_attribute`` or ``relationship`` (EC 3.x from the element name;
  EC 2.0 ``ECClass`` from ``isStruct`` / ``isCustomAttributeClass``);
- a ``property`` node per property, ``ec_kind`` = ``primitive``, ``struct``,
  ``array``, ``struct_array`` or ``navigation``, ``ec_type`` = its type name
  (a navigation property: its relationship);
- an ``enumeration`` node per ``ECEnumeration``.

Edges in the file: ``contains``; class -> base class ``inherits``;
relationship -> constraint class ``source_constraint`` / ``target_constraint``;
property -> enumeration, struct or relationship ``uses``. A name qualified by
another schema's alias (``bis:Element``) is left on the result as
``ecschema_refs`` for ``resolve.py``, as is each ``ECSchemaReference`` (the
schema node keeps every reference in ``ec_references`` whether it resolves or
not). Custom attribute instances (``ECCustomAttributes``) are skipped.

stdlib expat only. A DOCTYPE is refused (no DTD, no entities, nothing
external is read). XML that does not parse keeps the file node and logs a
warning.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from xml.parsers import expat

_LOG = logging.getLogger(__name__)


def _file_stem(path):
    # Lazy: graphify.extractors at plugin load re-enters graphify.detect (see autolisp).
    from graphify.extractors.base import _file_stem as f
    return f(path)


def _make_id(*parts):
    from graphify.extractors.base import _make_id as f
    return f(*parts)


_CLASS_KINDS = {"ECEntityClass": "entity", "ECStructClass": "struct",
                "ECCustomAttributeClass": "custom_attribute", "ECRelationshipClass": "relationship"}
_PROPERTY_KINDS = {"ECProperty": "primitive", "ECStructProperty": "struct",
                   "ECArrayProperty": "array", "ECStructArrayProperty": "struct_array",
                   "ECNavigationProperty": "navigation"}
_CONSTRAINTS = {"Source": "source_constraint", "Target": "target_constraint"}
_VERSION_RE = re.compile(r"ECXML\.(\d+(?:\.\d+)?)")


class _El:
    __slots__ = ("tag", "ns", "attrs", "line", "children", "text")

    def __init__(self, tag: str, attrs: dict, line: int) -> None:
        self.ns, _, self.tag = tag.rpartition("}")
        self.attrs, self.line, self.children, self.text = attrs, line, [], ""


def _refuse_dtd(*_args) -> None:
    raise ValueError("DOCTYPE refused (no DTD processing)")


def _parse(raw: bytes) -> _El | None:
    """Element tree with line numbers; ``ECCustomAttributes`` bodies are skipped."""
    p = expat.ParserCreate(namespace_separator="}")
    p.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    p.StartDoctypeDeclHandler = _refuse_dtd
    stack: list[_El] = []
    top: list[_El] = []
    skip = 0  # depth inside an ECCustomAttributes element

    def start(tag, attrs):
        nonlocal skip
        if skip:
            skip += 1
            return
        el = _El(tag, attrs, p.CurrentLineNumber)
        (stack[-1].children if stack else top).append(el)
        stack.append(el)
        if el.tag == "ECCustomAttributes":
            skip = 1

    def end(_tag):
        nonlocal skip
        if skip > 1:
            skip -= 1
            return
        skip = 0
        stack.pop()

    def chars(data):
        if not skip and stack:
            stack[-1].text += data

    p.StartElementHandler, p.EndElementHandler, p.CharacterDataHandler = start, end, chars
    p.Parse(raw, True)
    return top[0] if top else None


class _Out:
    """Node / edge / ref sink for one file (the bmake / astgrep plugins' shape)."""

    def __init__(self, path: Path) -> None:
        self.sf = str(path)
        self.stem = _make_id(_file_stem(path))
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.refs: list[dict] = []
        self._ids: set[str] = set()
        self._order: dict[str, int] = {}
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
        if src != tgt and not any(e["source"] == src and e["target"] == tgt
                                  and e["relation"] == relation for e in self.edges):
            self.edges.append({"source": src, "target": tgt, "relation": relation,
                               "confidence": "EXTRACTED", "source_file": self.sf,
                               "source_location": f"L{line}", "weight": 1.0})

    def ref(self, kind: str, source: str, schema: str, line: int, **extra) -> None:
        # The resolver reads the source id back through the node index (ids may be
        # salted apart before resolvers run; see bmake).
        self.refs.append({"kind": kind, "node": self._order[source], "schema": schema,
                          "line": line, "source_file": self.sf, **extra})


def _class_kind(el: _El) -> str:
    if el.tag != "ECClass":
        return _CLASS_KINDS[el.tag]
    flag = {k: el.attrs.get(k, "").lower() == "true" for k in ("isStruct", "isCustomAttributeClass")}
    return "struct" if flag["isStruct"] else "custom_attribute" if flag["isCustomAttributeClass"] else "entity"


def _property_kind(el: _El) -> str:
    if el.tag == "ECArrayProperty" and el.attrs.get("isStruct", "").lower() == "true":
        return "struct_array"  # EC 2.0 struct array
    return _PROPERTY_KINDS[el.tag]


def extract_ecschema(path: Path) -> dict:
    """Extract one ECSchema XML file (plan 04 §3.4)."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}
    out = _Out(path)
    try:
        root = _parse(raw)
    except (expat.ExpatError, ValueError) as exc:  # malformed: keep the file node, never crash
        _LOG.warning("ecschema: %s: XML does not parse: %s", path, exc)
        return {"nodes": out.nodes, "edges": out.edges}
    if root is None or root.tag != "ECSchema":
        return {"nodes": out.nodes, "edges": out.edges}

    name = root.attrs.get("schemaName", path.name)
    alias = root.attrs.get("alias") or root.attrs.get("nameSpacePrefix")
    m = _VERSION_RE.search(root.ns)
    attrs = {k: v for k, v in (("ec_version", m and m.group(1)), ("version", root.attrs.get("version")),
                                ("alias", alias)) if v}
    references = [c for c in root.children if c.tag == "ECSchemaReference"]
    schema = out.add(_make_id(out.stem, "schema", name), name, "schema", root.line,
                     ec_references=[f"{r.attrs.get('name')}.{r.attrs.get('version', '')}".rstrip(".")
                                    for r in references], **attrs)
    out.edge(out.file_nid, schema, "contains", root.line)
    aliases = {alias: name} if alias else {}
    for r in references:
        rname = r.attrs.get("name")
        if not rname:
            continue
        for key in ("alias", "prefix"):
            if r.attrs.get(key):
                aliases[r.attrs[key]] = rname
        out.ref("schema", schema, rname, r.line, version=r.attrs.get("version", ""))

    local: dict[str, str] = {}   # class / enumeration name -> node id
    classes: list[tuple[_El, str]] = []
    for c in root.children:
        cname = c.attrs.get("typeName")
        if not cname:
            continue
        if c.tag in _CLASS_KINDS or c.tag == "ECClass":
            extra = {"modifier": c.attrs["modifier"]} if c.attrs.get("modifier") else {}
            nid = out.add(_make_id(out.stem, cname), cname, "class", c.line,
                          ec_kind=_class_kind(c), ec_schema=name, **extra)
            classes.append((c, nid))
        elif c.tag == "ECEnumeration":
            extra = {"ec_backing_type": c.attrs["backingTypeName"]} if c.attrs.get("backingTypeName") else {}
            nid = out.add(_make_id(out.stem, cname), cname, "enumeration", c.line,
                          ec_schema=name, **extra)
        else:
            continue
        local[cname] = nid
        out.edge(schema, nid, "contains", c.line)

    def link(src: str, target: str, relation: str, line: int) -> None:
        prefix, _, member = target.strip().rpartition(":")
        target_schema = aliases.get(prefix, prefix) if prefix else name
        if target_schema == name:
            if member in local:
                out.edge(src, local[member], relation, line)
        else:
            out.ref("member", src, target_schema, line, name=member, relation=relation)

    for c, nid in classes:
        for child in c.children:
            if child.tag == "BaseClass" and child.text.strip():
                link(nid, child.text, "inherits", child.line)
            elif child.tag in _CONSTRAINTS:
                for k in child.children:
                    if k.tag == "Class" and k.attrs.get("class"):
                        link(nid, k.attrs["class"], _CONSTRAINTS[child.tag], k.line)
            elif child.tag in _PROPERTY_KINDS and child.attrs.get("propertyName"):
                kind = _property_kind(child)
                ptype = child.attrs.get("relationshipName" if kind == "navigation" else "typeName", "")
                pname = child.attrs["propertyName"]
                pid = out.add(_make_id(nid, pname), pname, "property", child.line,
                              ec_kind=kind, **({"ec_type": ptype} if ptype else {}))
                out.edge(nid, pid, "contains", child.line)
                if ptype:
                    link(pid, ptype, "uses", child.line)
    return {"nodes": out.nodes, "edges": out.edges, "ecschema_refs": out.refs}
