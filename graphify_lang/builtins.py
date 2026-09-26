"""Builtins filter for reference names (S005 F9).

``[extract] builtins_file`` (one name per line, relative to the manifest; a
line starting with ``;``, or with ``#`` then a space or the line end, is a
comment, so a name such as AutoLISP's ``#&/`` is kept: S3-N1) plus ``builtins_prefixes``, case-folded when
``case_insensitive = true``. Applied to ``@reference`` captures and regex
``edge`` rules inside the plugin only, never to the shared
``_LANGUAGE_BUILTIN_GLOBALS``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _comment(line: str) -> bool:
    return line.startswith(";") or line == "#" or line.startswith(("# ", "#\t"))


class Builtins:
    def __init__(self, names: set[str] = frozenset(), prefixes: tuple[str, ...] = (),
                 case_insensitive: bool = False) -> None:
        self.case_insensitive = case_insensitive
        self.names = {self.fold(n) for n in names}
        self.prefixes = tuple(self.fold(p) for p in prefixes)

    @classmethod
    def from_manifest(cls, manifest_path: Path, manifest: dict[str, Any]) -> Builtins:
        cfg = manifest.get("extract", {})
        ci = manifest.get("language", {}).get("case_insensitive",
                                              manifest.get("case_insensitive", False))
        names: set[str] = set()
        if cfg.get("builtins_file"):
            path = manifest_path.parent / cfg["builtins_file"]
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise RuntimeError(f"builtins_file failed to load: {exc}") from exc
            names = {s for line in text.splitlines()
                     if (s := line.strip()) and not _comment(s)}
        px = cfg.get("builtins_prefixes", ())
        return cls(names, (px,) if isinstance(px, str) else tuple(px), bool(ci))

    def fold(self, name: str) -> str:
        return name.casefold() if self.case_insensitive else name

    def is_builtin(self, name: str) -> bool:
        name = self.fold(name)
        return name in self.names or name.startswith(self.prefixes)
