"""Rules runtime for language manifests.

This module implements the declarative rules system for extracting
nodes and edges from source files using tree-sitter queries and regex rules.

The build() function returns (extract, resolver) callables that the
registry uses to dispatch language extraction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from graphify_lang.builtins import Builtins
from graphify_lang.queries import QueryRules
from graphify_lang.regex_rules import RegexRules


def build(manifest_path: Path, manifest: dict[str, Any]) -> tuple[Callable[[Path], dict], Callable[[Path, str], list[str]] | None]:
    """Build the extract and resolver callables from a manifest.

    Args:
        manifest_path: Path to the manifest TOML file.
        manifest: Parsed manifest dictionary.

    Returns:
        A tuple of (extract, resolver) where:
        - extract is a Callable[[Path], dict] that extracts nodes/edges
        - resolver is a Callable[[Path, str], list[str]] or None for cross-file resolution
    """
    # Load rule tiers
    queries = QueryRules.from_manifest(manifest_path, manifest)
    # Set the grammar from the manifest
    queries._grammar = manifest.get("grammar", manifest.get("grammar", None))
    regex = RegexRules.from_manifest(manifest_path, manifest)
    builtins = Builtins.from_manifest(manifest_path, manifest)

    def extract(path: Path) -> dict:
        """Extract nodes and edges from a file path."""
        # Read source
        try:
            source = path.read_bytes()
        except OSError as e:
            return {"nodes": [], "edges": [], "error": f"failed to read file: {e}"}

        # Run query rules
        query_results = queries.apply(source, str(path))

        # Run regex rules
        regex_results = regex.apply(source, str(path))

        # Apply builtins (case-folding if needed)
        query_results = builtins.apply_to_results(query_results)
        regex_results = builtins.apply_to_results(regex_results)

        # Merge results
        nodes = query_results.get("nodes", []) + regex_results.get("nodes", [])
        edges = query_results.get("edges", []) + regex_results.get("edges", [])

        # Apply Python hooks if configured
        # Check for post_file in extract section first (AutoLISP style), then in python sub-section
        post_file_cfg = manifest.get("extract", {}).get("post_file")
        if post_file_cfg is None:
            post_file_cfg = manifest.get("extract", {}).get("python", {}).get("post_file")
        
        if post_file_cfg:
            module, fn = post_file_cfg.split(":")
            try:
                import importlib
                mod = importlib.import_module(module)
                hook = getattr(mod, fn)
                result = hook(path, None, nodes, edges, manifest)
                if result is not None:
                    if isinstance(result, dict):
                        nodes = result.get("nodes", nodes)
                        edges = result.get("edges", edges)
                    elif isinstance(result, (tuple, list)) and len(result) == 2:
                        nodes = result[0]
                        edges = result[1]
            except (ImportError, AttributeError) as e:
                return {"nodes": [], "edges": [], "error": f"failed to load python hook: {e}"}
        
        return {"nodes": nodes, "edges": edges}

    # Resolver is None for now; AutoLISP resolver will be implemented in S007
    resolver: Callable[[Path, str], list[str]] | None = None

    return extract, resolver
