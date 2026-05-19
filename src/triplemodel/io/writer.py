"""Write triple rows into RDF graphs."""

from __future__ import annotations

from pyoxigraph import NamedNode

from triplemodel._typing import TripleRow
from triplemodel.store.graph import RdfGraph
from triplemodel.store.terms import RdfTerm
from triplemodel.terms.convert import python_to_term
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry


def apply_triple_rows(
    graph: RdfGraph,
    rows: list[TripleRow],
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Add ``rows`` to ``graph`` (subject, predicate, object)."""
    for subj, pred, obj in rows:
        subj_node: RdfTerm = subj if not isinstance(subj, str) else subject_node(subj)
        graph.add((subj_node, NamedNode(pred), python_to_term(obj, registry=registry)))
