"""Remove inverse-predicate triples on remote subjects when fields are cleared."""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel
from rdflib import Graph, URIRef
from rdflib.term import Node

from triplemodel.config import RdfConfig, get_rdf_config
from triplemodel.fields.metadata import inverse_for_field
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.cardinality import field_cardinality
from triplemodel.namespaces import resolve_predicate
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.iri import subject_ref


def _field_clears_inverse(value: object, card: str) -> bool:
    if value is None:
        return True
    if card == "list":
        if not isinstance(value, list):
            return False
        return value == [] or all(v is None for v in value)
    if card == "set":
        return value in (set(), frozenset())
    return False


def _walk_embed_instances(
    model: BaseModel,
    subject: Node,
    cfg: RdfConfig,
    graph: Graph,
    resolver: PredicateResolverProtocol,
) -> Iterator[tuple[BaseModel, Node, RdfConfig]]:
    """Yield root and nested embed instances without traversing ``list`` embed exports."""
    yield model, subject, cfg
    prefixes = cfg.prefixes_dict
    for name, field_info in type(model).model_fields.items():
        if field_cardinality(field_info) != "nested":
            continue
        nested = getattr(model, name)
        if nested is None:
            continue
        predicate = resolver.resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        nested_cfg = get_rdf_config(type(nested))
        if cfg.embed == "iri":
            nested_subj: Node = subject_ref(nested_cfg.subject_uri(nested))
            yield from _walk_embed_instances(
                nested, nested_subj, nested_cfg, graph, resolver
            )
        else:
            pred_ref = URIRef(predicate)
            for obj in graph.objects(subject, pred_ref):
                yield from _walk_embed_instances(
                    nested, obj, nested_cfg, graph, resolver
                )


def clear_inverse_links_to_subject(
    graph: Graph,
    subject: str | Node,
    model_cls: type[BaseModel],
    *,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove all ``(?, inverse_predicate, subject)`` for inverse fields on ``model_cls``."""
    cfg = config or get_rdf_config(model_cls)
    subj_node = subject if isinstance(subject, Node) else subject_ref(subject)
    prefixes = cfg.prefixes_dict
    id_field = cfg.id_field
    for name, field_info in model_cls.model_fields.items():
        if id_field and name == id_field:
            continue
        inv_raw = inverse_for_field(field_info)
        if inv_raw is None:
            continue
        inv_pred = URIRef(resolve_predicate(inv_raw, prefixes))
        for remote in list(graph.subjects(inv_pred, subj_node)):
            graph.remove((remote, inv_pred, subj_node))


def clear_inverse_links(
    graph: Graph,
    model: BaseModel,
    *,
    subject: str | Node | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> None:
    """Remove ``(?, inverse_predicate, subject)`` when mapped fields are empty."""
    r = resolver or default_resolver
    cfg = config or get_rdf_config(type(model))
    subj = subject or cfg.subject_uri(model)
    subj_node = subj if isinstance(subj, Node) else subject_ref(subj)
    for inst, node, inst_cfg in _walk_embed_instances(model, subj_node, cfg, graph, r):
        prefixes = inst_cfg.prefixes_dict
        id_field = inst_cfg.id_field
        for name, field_info in type(inst).model_fields.items():
            if id_field and name == id_field:
                continue
            inv_raw = inverse_for_field(field_info)
            if inv_raw is None:
                continue
            card = field_cardinality(field_info)
            value = getattr(inst, name)
            if not _field_clears_inverse(value, card):
                continue
            inv_pred = URIRef(resolve_predicate(inv_raw, prefixes))
            for remote in list(graph.subjects(inv_pred, node)):
                graph.remove((remote, inv_pred, node))
