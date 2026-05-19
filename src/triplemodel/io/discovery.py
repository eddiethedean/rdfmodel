"""Discover RDF subject URIs in a graph."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import term_str

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
        for subj in graph.subjects(predicate=NamedNode(pred)):
            if isinstance(subj, NamedNode):
                subjects.add(term_str(subj))
    return sorted(subjects)


def discover_subjects_by_instance_of(
    graph: Graph,
    cfg: RdfConfig,
) -> list[str]:
    """Subjects with ``(subject, instance_of, type)`` per :attr:`RdfConfig.instance_of`."""
    preds = cfg.instance_of_predicates
    if not preds:
        return []
    prefixes = cfg.prefixes_dict
    type_uris = cfg.instance_type_uris
    subjects: set[str] = set()
    for pred_raw in preds:
        pred_uri = NamedNode(resolve_predicate(pred_raw, prefixes))
        if type_uris:
            for type_raw in type_uris:
                type_uri = NamedNode(resolve_predicate(type_raw, prefixes))
                for subj in graph.subjects(pred_uri, type_uri):
                    if isinstance(subj, NamedNode):
                        subjects.add(term_str(subj))
        else:
            for subj in graph.subjects(pred_uri, None):
                if isinstance(subj, NamedNode):
                    subjects.add(term_str(subj))
    return sorted(subjects)
