"""Discover RDF subject URIs in a graph."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from rdflib import Graph, URIRef

from triplemodel.config import RDF_TYPE, RdfConfig
from triplemodel.fields.metadata import inverse_for_field
from triplemodel.fields.resolver import default_resolver
from triplemodel.namespaces import resolve_predicate
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
    prefixes = cfg.prefixes_dict
    inverse_preds: set[str] = set()
    for field_info in model_cls.model_fields.values():
        inv = inverse_for_field(field_info)
        if inv is not None:
            inverse_preds.add(resolve_predicate(inv, prefixes))
    predicates = {p for p in owned if p != RDF_TYPE and p not in inverse_preds}
    if not predicates:
        return []
    subjects: set[str] = set()
    for pred in predicates:
        for subj in graph.subjects(predicate=URIRef(pred)):
            if isinstance(subj, URIRef):
                subjects.add(str(subj))
    return sorted(subjects)
