"""Write triple rows into rdflib graphs."""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.term import Node

from triplemodel._typing import TripleRow
from triplemodel.terms.convert import python_to_term
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry


def apply_triple_rows(
    graph: Graph,
    rows: list[TripleRow],
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Add ``rows`` to ``graph`` (subject, predicate, object)."""
    for subj, pred, obj in rows:
        subj_node = subj if isinstance(subj, Node) else subject_node(subj)
        graph.add((subj_node, URIRef(pred), python_to_term(obj, registry=registry)))
