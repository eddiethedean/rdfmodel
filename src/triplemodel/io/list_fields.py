"""Export/import RDF list fields on models."""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel
from pyoxigraph import BlankNode as BNode, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel._typing import TripleRow
from triplemodel.config import RdfConfig, get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.cardinality import (
    field_cardinality,
    nested_model_type,
    scalar_python_type,
)
from triplemodel.terms.lang import MultiLangString
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.bnode import nested_bnode_key, stable_bnode
from triplemodel.terms.collection import remove_rdf_list, write_rdf_list
from triplemodel.terms.iri import subject_ref
from triplemodel.terms.registry import LiteralRegistry, default_registry


def list_subject_from_embed_rows(rows: list[TripleRow]) -> BNode | None:
    """Return the blank node used as subject for nested property triples."""
    for subj, _pred, _obj in rows:
        if isinstance(subj, BNode):
            return subj
    return None


def nested_embed_list_subject(
    nested: BaseModel,
    *,
    parent_subject: str,
    predicate: str,
    parent_config: RdfConfig,
    embed_rows: list[TripleRow] | None = None,
    graph: Graph | None = None,
) -> str | Node:
    """Subject node for ``list[T]`` fields on a nested embedded model."""
    nested_cfg = get_rdf_config(type(nested))
    if parent_config.embed == "iri":
        return nested_cfg.subject_uri(nested)
    if parent_config.blank_node_policy == "stable":
        return stable_bnode(nested_bnode_key(parent_subject, predicate, nested))
    if embed_rows is not None:
        node = list_subject_from_embed_rows(embed_rows)
        if node is not None:
            return node
    if graph is not None:
        pred_ref = NamedNode(predicate)
        parent_ref = subject_ref(parent_subject)
        for obj in graph.objects(parent_ref, pred_ref):
            if isinstance(obj, BNode):
                return obj
    raise ValueError(
        "Cannot resolve blank-node list subject without embed export rows, "
        "a graph with the parent link, or stable blank_node_policy."
    )


def export_model_rdf_lists(
    graph: Graph,
    model: BaseModel,
    *,
    subject: str | Node | None = None,
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
    subj_node = subj if isinstance(subj, Node) else subject_ref(subj)
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


def iter_nested_list_exports(
    model: BaseModel,
    *,
    subject: str | Node,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    embed_rows_by_field: dict[str, list[TripleRow]] | None = None,
    graph: Graph | None = None,
) -> Iterator[tuple[BaseModel, str | Node, RdfConfig]]:
    """Yield ``(nested_model, list_subject, nested_config)`` for embedded children."""
    cfg = config or get_rdf_config(type(model))
    if cfg.embed != "iri" and cfg.embed != "bnode":
        return
    r = resolver or default_resolver
    prefixes = cfg.prefixes_dict
    from triplemodel.store.terms import term_str

    parent_subject = term_str(subject) if isinstance(subject, Node) else subject
    rows_map = embed_rows_by_field or {}
    for name, field_info in type(model).model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        if field_cardinality(field_info) != "nested":
            continue
        nested_cls = nested_model_type(field_info)
        if nested_cls is None:
            continue
        value = getattr(model, name)
        if value is None:
            continue
        pred = r.resolve_field_predicate(field_info, prefixes)
        if pred is None:
            continue
        nested_cfg = get_rdf_config(nested_cls)
        list_subj = nested_embed_list_subject(
            value,
            parent_subject=parent_subject,
            predicate=pred,
            parent_config=cfg,
            embed_rows=rows_map.get(name),
            graph=graph,
        )
        yield value, list_subj, nested_cfg
        yield from iter_nested_list_exports(
            value,
            subject=list_subj,
            config=nested_cfg,
            resolver=r,
            graph=graph,
        )


def export_all_rdf_lists(
    graph: Graph,
    model: BaseModel,
    *,
    subject: str | Node | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    embed_rows_by_field: dict[str, list[TripleRow]] | None = None,
) -> None:
    """Write ``rdf:List`` fields for ``model`` and nested embedded children."""
    for inst, subj_node, cfg in iter_all_embedded_models(
        model,
        subject=subject,
        config=config,
        resolver=resolver,
        embed_rows_by_field=embed_rows_by_field,
        graph=graph,
    ):
        export_model_rdf_lists(
            graph,
            inst,
            subject=subj_node,
            config=cfg,
            resolver=resolver,
            registry=registry,
        )


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


def predicates_to_patch_for_model(
    model: BaseModel,
    *,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> set[str]:
    """Predicates to clear when a field is ``None`` or an empty collection."""
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    r = resolver or default_resolver
    clear: set[str] = set()
    prefixes = cfg.prefixes_dict
    for name, field_info in cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        pred = r.resolve_field_predicate(field_info, prefixes)
        if pred is None:
            continue
        value = getattr(model, name)
        card = field_cardinality(field_info)
        if value is None:
            clear.add(pred)
        elif card == "list" and (value == [] or _list_effectively_empty(value)):
            clear.add(pred)
        elif card == "set" and value in (set(), frozenset()):
            clear.add(pred)
        elif scalar_python_type(field_info) is MultiLangString and not value:
            clear.add(pred)
    return clear


def _list_effectively_empty(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(v is None for v in value)


def iter_all_embedded_models(
    model: BaseModel,
    *,
    subject: str | Node | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    embed_rows_by_field: dict[str, list[TripleRow]] | None = None,
    graph: Graph | None = None,
) -> Iterator[tuple[BaseModel, Node, RdfConfig]]:
    """Yield ``(model, subject_node, config)`` for the root and nested embeds."""
    cfg = config or get_rdf_config(type(model))
    r = resolver or default_resolver
    subj = subject or cfg.subject_uri(model)
    subj_node = subj if isinstance(subj, Node) else subject_ref(subj)
    yield model, subj_node, cfg
    for nested, list_subj, nested_cfg in iter_nested_list_exports(
        model,
        subject=subj_node,
        config=cfg,
        resolver=r,
        embed_rows_by_field=embed_rows_by_field,
        graph=graph,
    ):
        nested_node = (
            list_subj if isinstance(list_subj, Node) else subject_ref(list_subj)
        )
        yield nested, nested_node, nested_cfg


def collect_patch_clear_predicates(
    model: BaseModel,
    *,
    subject: str | Node | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    embed_rows_by_field: dict[str, list[TripleRow]] | None = None,
    graph: Graph | None = None,
) -> list[tuple[Node, set[str]]]:
    """Return ``(subject_node, predicates)`` pairs to clear during patch sync."""
    r = resolver or default_resolver
    out: list[tuple[Node, set[str]]] = []
    for inst, subj_node, cfg in iter_all_embedded_models(
        model,
        subject=subject,
        config=config,
        resolver=r,
        embed_rows_by_field=embed_rows_by_field,
        graph=graph,
    ):
        preds = predicates_to_patch_for_model(inst, config=cfg, resolver=r)
        if preds:
            out.append((subj_node, preds))
    return out
