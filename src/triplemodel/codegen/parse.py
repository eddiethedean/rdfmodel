"""Parse OWL/RDFS ontologies into rdflib graphs."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph


def ontology_graph(source: str | Path, *, format: str | None = None) -> Graph:
    """Load an ontology file into a graph."""
    graph = Graph()
    path = Path(source)
    if path.is_file():
        graph.parse(source=str(path), format=format)
    else:
        graph.parse(data=str(source), format=format or "turtle")
    return graph
