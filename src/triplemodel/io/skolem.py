"""Skolemization helpers for rdflib graphs."""

from __future__ import annotations

from rdflib import Graph


def apply_skolemize(graph: Graph, *, skolemize: bool = False) -> Graph:
    """Return ``graph.skolemize()`` when ``skolemize`` is true."""
    if skolemize:
        return graph.skolemize()
    return graph


def apply_de_skolemize(graph: Graph, *, de_skolemize: bool = False) -> Graph:
    """Return ``graph.de_skolemize()`` when ``de_skolemize`` is true."""
    if de_skolemize:
        return graph.de_skolemize()
    return graph
