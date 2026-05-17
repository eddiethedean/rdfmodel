"""Predicate-level graph removal for sync."""

from __future__ import annotations

from pydantic import BaseModel
from rdflib import Graph
from rdflib.term import Node

from triplemodel.config import RdfConfig
from triplemodel.fields.resolver import default_resolver
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.collection import remove_rdf_list
from triplemodel.terms.iri import subject_ref


def remove_triples_for_predicates(
    graph: Graph,
    subject: Node,
    predicates: set[str],
) -> None:
    """Remove triples for ``(subject, predicate)`` including RDF lists and embed bnodes."""
    for pred in predicates:
        remove_rdf_list(graph, subject, pred)


def remove_owned_triples(
    graph: Graph,
    uri: str,
    model_cls: type[BaseModel],
    *,
    config: RdfConfig | None = None,
    predicates: frozenset[str] | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove triples for ``uri`` owned by ``model_cls``."""
    r = resolver or default_resolver
    preds = (
        predicates if predicates is not None else r.owned_predicates(model_cls, config)
    )
    remove_triples_for_predicates(graph, subject_ref(uri), set(preds))
