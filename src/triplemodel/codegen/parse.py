"""Parse OWL/RDFS ontologies into pyoxigraph-backed graphs."""

from __future__ import annotations

from pathlib import Path

from triplemodel.store import RdfGraph as Graph

_ONTOLOGY_SUFFIXES = (".ttl", ".turtle", ".owl", ".rdf", ".xml", ".nt", ".nq")

_SUFFIX_FORMAT: dict[str, str] = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".owl": "xml",
    ".rdf": "xml",
    ".xml": "xml",
    ".nt": "nt",
    ".nq": "nq",
}


def _format_for_path(path: Path, fmt: str | None) -> str:
    if fmt is not None:
        return fmt
    inferred = _SUFFIX_FORMAT.get(path.suffix.lower())
    if inferred is None:
        raise ValueError("parse() requires format=")
    return inferred


def ontology_graph(source: str | Path, *, format: str | None = None) -> Graph:
    """Load an ontology file into a graph."""
    graph = Graph()
    path = Path(source)
    if path.is_file():
        graph.parse(source=str(path), format=_format_for_path(path, format))
    elif path.exists():
        raise FileNotFoundError(f"Ontology path is not a file: {path}")
    elif path.suffix.lower() in _ONTOLOGY_SUFFIXES:
        raise FileNotFoundError(f"Ontology file not found: {path}")
    else:
        graph.parse(data=str(source), format=format or "turtle")
    return graph
