"""Sync model state into graphs with add / replace / patch semantics."""

from __future__ import annotations

from collections import defaultdict
from typing import cast

from pydantic import BaseModel
from rdflib import Graph, URIRef
from rdflib.term import Node

from triplemodel._config import (
    GraphMode,
    RdfConfig,
    effective_graph_mode,
    get_rdf_config,
)
from triplemodel._fields import owned_predicates, resolve_field_predicate
from triplemodel._graph_ops import graph_set_many
from triplemodel._namespaces import bind_namespaces


def _subject_ref(uri: str) -> URIRef:
    return URIRef(uri)


def remove_triples_for_predicates(
    graph: Graph,
    subject: URIRef,
    predicates: set[str],
) -> None:
    """Remove all triples with ``subject`` as subject and predicate in ``predicates``."""
    for pred in predicates:
        pred_ref = URIRef(pred)
        for obj in list(graph.objects(subject, pred_ref)):
            graph.remove((subject, pred_ref, obj))


def remove_owned_triples(
    graph: Graph,
    uri: str,
    model_cls: type[BaseModel],
    *,
    config: RdfConfig | None = None,
    predicates: frozenset[str] | None = None,
) -> None:
    """Remove triples for ``uri`` owned by ``model_cls``."""
    preds = (
        predicates if predicates is not None else owned_predicates(model_cls, config)
    )
    remove_triples_for_predicates(graph, _subject_ref(uri), set(preds))


def _clear_stale_nested_iri_children(
    model: BaseModel,
    graph: Graph,
    parent_uri: str,
    *,
    config: RdfConfig,
) -> None:
    """Remove owned triples for nested IRI children no longer linked from the parent."""
    from triplemodel._cardinality import field_cardinality, nested_model_type

    if config.embed != "iri":
        return
    parent_ref = _subject_ref(parent_uri)
    cls = type(model)
    prefixes = config.prefixes_dict
    for name, field_info in cls.model_fields.items():
        if config.id_field and name == config.id_field:
            continue
        if field_cardinality(field_info) != "nested":
            continue
        pred = resolve_field_predicate(field_info, prefixes)
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
            )


def _clear_nested_iri_children(
    model: BaseModel,
    graph: Graph,
    *,
    config: RdfConfig,
) -> None:
    """Remove owned triples for nested IRI-embedded children before parent replace."""
    from triplemodel._cardinality import field_cardinality, nested_model_type

    if config.embed != "iri":
        return
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
        )


def predicates_to_patch(
    model: BaseModel,
    *,
    config: RdfConfig | None = None,
) -> set[str]:
    """Predicates that should be cleared (field is None or empty collection)."""
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    clear: set[str] = set()
    from triplemodel._cardinality import field_cardinality

    prefixes = cfg.prefixes_dict
    for name, field_info in cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        pred = resolve_field_predicate(field_info, prefixes)
        if pred is None:
            continue
        value = getattr(model, name)
        card = field_cardinality(field_info)
        if value is None:
            clear.add(pred)
        elif card == "list" and value == []:
            clear.add(pred)
        elif card == "set" and value == set():
            clear.add(pred)
    return set(clear)


def sync_to_graph(
    model: BaseModel,
    graph: Graph | None = None,
    *,
    uri: str | None = None,
    mode: GraphMode | None = None,
    config: RdfConfig | None = None,
    bind: bool = True,
) -> Graph:
    """Write ``model`` into ``graph`` using ``mode`` sync semantics."""
    from rdflib.term import Node

    from triplemodel._graph import _subject_node, model_to_graph, model_to_triples

    g = Graph() if graph is None else graph
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    mode = effective_graph_mode(mode, cfg, sync=True)
    subject = uri or cfg.subject_uri(model)
    subject_ref = _subject_ref(subject)

    if bind and cfg.prefixes:
        bind_namespaces(g, cfg.prefixes_dict)

    if mode == "add":
        return model_to_graph(model, g, uri=uri, config=cfg, mode="add")

    if mode == "replace":
        _clear_stale_nested_iri_children(model, g, subject, config=cfg)
        remove_owned_triples(g, subject, cls, config=cfg)
        _clear_nested_iri_children(model, g, config=cfg)
        return model_to_graph(model, g, uri=uri, config=cfg, mode="add")

    # patch: clear empty fields, then replace triples per (subject, predicate)
    to_clear = predicates_to_patch(model, config=cfg)
    _clear_stale_nested_iri_children(model, g, subject, config=cfg)
    remove_triples_for_predicates(g, subject_ref, to_clear)

    by_sp: dict[tuple[Node, str], list[object]] = defaultdict(list)
    for subj, pred, obj in model_to_triples(model, uri=subject, config=cfg):
        subj_ref = subj if isinstance(subj, Node) else _subject_node(subj)
        by_sp[(subj_ref, pred)].append(obj)

    for (subj_ref, pred), objects in by_sp.items():
        graph_set_many(g, subj_ref, pred, objects)
    return g
