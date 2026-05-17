"""Discover RDF subject URIs in a graph."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from rdflib import Graph, URIRef

from triplemodel.config import RDF_TYPE, RdfConfig
from triplemodel.fields.resolver import default_resolver
from triplemodel.protocols import PredicateResolver

T = TypeVar("T", bound=BaseModel)


def discover_subject_uris(
    graph: Graph,
    model_cls: type[T],
    cfg: RdfConfig,
    *,
    resolver: PredicateResolver | None = None,
) -> list[str]:
    """URIRef subjects with at least one owned predicate triple (excluding ``rdf:type``)."""
    r = resolver or default_resolver
    owned = r.owned_predicates(model_cls, cfg)
    predicates = {p for p in owned if p != RDF_TYPE}
    if not predicates:
        return []
    subjects: set[str] = set()
    for pred in predicates:
        for subj in graph.subjects(predicate=URIRef(pred)):
            if isinstance(subj, URIRef):
                subjects.add(str(subj))
    return sorted(subjects)
