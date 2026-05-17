"""Remove stale nested IRI child subgraphs during sync."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel
from rdflib import BNode, Graph, URIRef

from triplemodel.config import RdfConfig, get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.io.sync.predicate_ops import remove_owned_triples
from triplemodel.metadata.cardinality import field_cardinality, nested_model_type
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.bnode import (
    nested_bnode_key,
    remove_bnode_subgraph,
    stable_bnode,
)
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


def clear_stale_nested_bnode_children(
    model: BaseModel,
    graph: Graph,
    parent_uri: str,
    *,
    config: RdfConfig,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove blank-node subgraphs for nested children no longer linked."""
    if config.embed != "bnode":
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
        pred_ref = URIRef(pred)
        in_graph = {
            obj for obj in graph.objects(parent_ref, pred_ref) if isinstance(obj, BNode)
        }
        value = getattr(model, name)
        if value is None:
            keep: set[BNode] = set()
        elif config.blank_node_policy == "stable":
            keep = {stable_bnode(nested_bnode_key(parent_uri, pred, value))}
        else:
            keep = set()
        for stale in in_graph - keep:
            remove_bnode_subgraph(graph, stale)


def clear_nested_bnode_children(
    model: BaseModel,
    graph: Graph,
    parent_uri: str,
    *,
    config: RdfConfig,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove current nested blank-node subgraphs before parent replace."""
    if config.embed != "bnode":
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
        pred_ref = URIRef(pred)
        for bnode in graph.objects(parent_ref, pred_ref):
            if isinstance(bnode, BNode):
                remove_bnode_subgraph(graph, bnode)
