"""Skolemization helpers for RDF graphs."""

from __future__ import annotations

from triplemodel.store.graph import RdfGraph


def apply_skolemize(graph: RdfGraph, *, skolemize: bool = False) -> RdfGraph:
    """Return ``graph.skolemize()`` when ``skolemize`` is true."""
    if skolemize:
        return graph.skolemize()
    return graph


def apply_de_skolemize(graph: RdfGraph, *, de_skolemize: bool = False) -> RdfGraph:
    """Return ``graph.de_skolemize()`` when ``de_skolemize`` is true."""
    if de_skolemize:
        return graph.de_skolemize()
    return graph
