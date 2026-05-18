"""Parse OWL/RDFS ontologies into rdflib graphs."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

_ONTOLOGY_SUFFIXES = (".ttl", ".turtle", ".owl", ".rdf", ".xml", ".nt", ".nq")


def ontology_graph(source: str | Path, *, format: str | None = None) -> Graph:
    """Load an ontology file into a graph."""
    graph = Graph()
    path = Path(source)
    if path.is_file():
        graph.parse(source=str(path), format=format)
    elif path.exists():
        raise FileNotFoundError(f"Ontology path is not a file: {path}")
    elif path.suffix.lower() in _ONTOLOGY_SUFFIXES:
        raise FileNotFoundError(f"Ontology file not found: {path}")
    else:
        graph.parse(data=str(source), format=format or "turtle")
    return graph
