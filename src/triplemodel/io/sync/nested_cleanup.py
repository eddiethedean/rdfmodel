"""Remove stale nested IRI child subgraphs during sync."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel
from rdflib import Graph, URIRef

from triplemodel.config import RdfConfig, get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.io.sync.predicate_ops import remove_owned_triples
from triplemodel.metadata.cardinality import field_cardinality, nested_model_type
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.iri import subject_ref


def clear_stale_nested_iri_children(
    model: BaseModel,
    graph: Graph,
    parent_uri: str,
    *,
    config: RdfConfig,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove owned triples for nested IRI children no longer linked from the parent."""
    if config.embed != "iri":
        return
    r = resolver or default_resolver
    parent_ref = subject_ref(parent_uri)
    cls = type(model)
    prefixes = config.prefixes_dict
    for name, field_info in cls.model_fields.items():
        if config.id_field and name == config.id_field:
            continue
        if field_cardinality(field_info) != "nested":
            continue
        pred = r.resolve_field_predicate(field_info, prefixes)
        if pred is None:
            continue
        nested_cls = nested_model_type(field_info)
        if nested_cls is None:
            continue
        nested_cfg = get_rdf_config(nested_cls)
        pred_ref = URIRef(pred)
        in_graph = {
            str(obj)
            for obj in graph.objects(parent_ref, pred_ref)
            if isinstance(obj, URIRef)
        }
        value = getattr(model, name)
        keep = {nested_cfg.subject_uri(value)} if value is not None else set()
        for stale_uri in in_graph - keep:
            remove_owned_triples(
                graph,
                stale_uri,
                cast(type[BaseModel], nested_cls),
                config=nested_cfg,
                resolver=r,
            )


def clear_nested_iri_children(
    model: BaseModel,
    graph: Graph,
    *,
    config: RdfConfig,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove owned triples for nested IRI-embedded children before parent replace."""
    if config.embed != "iri":
        return
    r = resolver or default_resolver
    cls = type(model)
    for name, field_info in cls.model_fields.items():
        if config.id_field and name == config.id_field:
            continue
        if field_cardinality(field_info) != "nested":
            continue
        nested_cls = nested_model_type(field_info)
        if nested_cls is None:
            continue
        value = getattr(model, name)
        if value is None:
            continue
        nested_cfg = get_rdf_config(nested_cls)
        child_uri = nested_cfg.subject_uri(value)
        remove_owned_triples(
            graph,
            child_uri,
            cast(type[BaseModel], nested_cls),
            config=nested_cfg,
            resolver=r,
        )
