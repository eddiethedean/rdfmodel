"""Export/import RDF list fields on models."""

from __future__ import annotations

from pydantic import BaseModel
from rdflib import Graph
from rdflib.term import Node

from triplemodel.config import RdfConfig, get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.cardinality import field_cardinality
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.collection import remove_rdf_list, write_rdf_list
from triplemodel.terms.iri import subject_ref
from triplemodel.terms.registry import LiteralRegistry, default_registry


def export_model_rdf_lists(
    graph: Graph,
    model: BaseModel,
    *,
    subject: str | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Write ``list[T]`` fields as ``rdf:List`` structures."""
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    r = resolver or default_resolver
    prefixes = cfg.prefixes_dict
    subj = subject or cfg.subject_uri(model)
    subj_node = subject_ref(subj)
    id_field = cfg.id_field
    for name, field_info in cls.model_fields.items():
        if id_field and name == id_field:
            continue
        if field_cardinality(field_info) != "list":
            continue
        predicate = r.resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        value = getattr(model, name)
        if value is None or value == []:
            continue
        write_rdf_list(graph, subj_node, predicate, list(value), registry=registry)


def clear_model_rdf_lists(
    graph: Graph,
    model_cls: type[BaseModel],
    subject: str | Node,
    *,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove all ``rdf:List`` heads for list-shaped fields on ``model_cls``."""
    cfg = config or get_rdf_config(model_cls)
    r = resolver or default_resolver
    prefixes = cfg.prefixes_dict
    subj = subject if isinstance(subject, Node) else subject_ref(subject)
    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        if field_cardinality(field_info) != "list":
            continue
        predicate = r.resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        remove_rdf_list(graph, subj, predicate)
