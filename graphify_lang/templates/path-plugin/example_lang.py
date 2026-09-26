"""Path-plugin template runtime: one node per file, one per ``item <name>`` line."""
from __future__ import annotations

from pathlib import Path


def extract(path: Path) -> dict:
    path = Path(path)
    page = {"id": f"example_{path.stem}", "label": path.name, "file_type": "code",
            "source_file": str(path), "source_location": "L1"}
    nodes, edges = [page], []
    for no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if line.startswith("item "):
            name = line[5:].strip()
            nodes.append({"id": f"example_{path.stem}_{name}", "label": name, "file_type": "code",
                          "source_file": str(path), "source_location": f"L{no}"})
            edges.append({"source": page["id"], "target": nodes[-1]["id"], "relation": "contains",
                          "confidence": "EXTRACTED", "source_file": str(path),
                          "source_location": f"L{no}"})
    return {"nodes": nodes, "edges": edges}
