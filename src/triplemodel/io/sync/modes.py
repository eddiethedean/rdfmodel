"""Graph write mode strategies (add / replace / patch)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel
from rdflib import Graph
from rdflib.term import Node

from triplemodel._typing import TripleObject
from triplemodel.config import GraphMode, RdfConfig, get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.io.export import model_to_triples
from triplemodel.io.graph import write_model_add
from triplemodel.io.skolem import apply_skolemize
from triplemodel.io.ops import graph_set_many
from triplemodel.terms.collection import write_rdf_list
from triplemodel.io.sync.nested_cleanup import (
    clear_nested_bnode_children,
    clear_nested_iri_children,
    clear_stale_nested_bnode_children,
    clear_stale_nested_iri_children,
)
from triplemodel.io.sync.predicate_ops import (
    remove_owned_triples,
    remove_triples_for_predicates,
)
from triplemodel.metadata.cardinality import field_cardinality
from triplemodel.protocols import (
    GraphWriteMode,
    PredicateResolver as PredicateResolverProtocol,
)
from triplemodel.namespaces import bind_namespaces
from triplemodel.terms.iri import subject_node, subject_ref
from triplemodel.terms.registry import LiteralRegistry, default_registry


def predicates_to_patch(
    model: BaseModel,
    *,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> set[str]:
    """Predicates that should be cleared (field is None or empty collection)."""
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
        elif card == "list" and value == []:
            clear.add(pred)
        elif card == "set" and value == set():
            clear.add(pred)
    return clear


@dataclass(frozen=True)
class AddGraphMode:
    """Append owned triples without removing existing graph content."""

    mode: GraphMode = "add"

    def apply(
        self,
        graph: Graph,
        model: BaseModel,
        *,
        uri: str | None = None,
        config: RdfConfig,
        bind: bool,
        resolver: PredicateResolverProtocol | None = None,
        registry: LiteralRegistry | None = None,
        skolemize: bool | None = None,
    ) -> Graph:
        reg = registry or default_registry
        return write_model_add(
            graph,
            model,
            uri=uri,
            config=config,
            bind=bind,
            resolver=resolver,
            registry=reg,
            skolemize=skolemize,
        )


@dataclass(frozen=True)
class ReplaceGraphMode:
    """Remove owned triples for the subject (and nested IRI children), then re-export."""

    mode: GraphMode = "replace"

    def apply(
        self,
        graph: Graph,
        model: BaseModel,
        *,
        uri: str | None = None,
        config: RdfConfig,
        bind: bool,
        resolver: PredicateResolverProtocol | None = None,
        registry: LiteralRegistry | None = None,
        skolemize: bool | None = None,
    ) -> Graph:
        reg = registry or default_registry
        cls = type(model)
        subject = uri or config.subject_uri(model)
        clear_stale_nested_iri_children(
            model, graph, subject, config=config, resolver=resolver
        )
        clear_stale_nested_bnode_children(
            model, graph, subject, config=config, resolver=resolver
        )
        remove_owned_triples(graph, subject, cls, config=config, resolver=resolver)
        clear_nested_iri_children(model, graph, config=config, resolver=resolver)
        clear_nested_bnode_children(
            model, graph, subject, config=config, resolver=resolver
        )
        return write_model_add(
            graph,
            model,
            uri=uri,
            config=config,
            bind=bind,
            resolver=resolver,
            registry=reg,
            skolemize=skolemize,
        )


@dataclass(frozen=True)
class PatchGraphMode:
    """Clear empty fields and replace triples per (subject, predicate)."""

    mode: GraphMode = "patch"

    def apply(
        self,
        graph: Graph,
        model: BaseModel,
        *,
        uri: str | None = None,
        config: RdfConfig,
        bind: bool,
        resolver: PredicateResolverProtocol | None = None,
        registry: LiteralRegistry | None = None,
        skolemize: bool | None = None,
    ) -> Graph:
        if bind and config.prefixes:
            bind_namespaces(graph, config.prefixes_dict)
        do_skolem = config.skolemize_export if skolemize is None else skolemize
        graph = apply_skolemize(graph, skolemize=do_skolem)
        reg = registry or default_registry
        subject = uri or config.subject_uri(model)
        subject_ref_node = subject_ref(subject)
        to_clear = predicates_to_patch(model, config=config, resolver=resolver)
        clear_stale_nested_iri_children(
            model, graph, subject, config=config, resolver=resolver
        )
        clear_stale_nested_bnode_children(
            model, graph, subject, config=config, resolver=resolver
        )
        remove_triples_for_predicates(graph, subject_ref_node, to_clear)

        by_sp: dict[tuple[Node, str], list[TripleObject]] = defaultdict(list)
        for subj, pred, obj in model_to_triples(
            model,
            uri=subject,
            config=config,
            resolver=resolver,
            registry=reg,
        ):
            subj_ref = subj if isinstance(subj, Node) else subject_node(subj)
            by_sp[(subj_ref, pred)].append(obj)

        for (subj_ref, pred), objects in by_sp.items():
            graph_set_many(graph, subj_ref, pred, objects, registry=reg)

        cls = type(model)
        prefixes = config.prefixes_dict
        r = resolver or default_resolver
        for name, field_info in cls.model_fields.items():
            if config.id_field and name == config.id_field:
                continue
            if field_cardinality(field_info) != "list":
                continue
            pred = r.resolve_field_predicate(field_info, prefixes)
            if pred is None:
                continue
            value = getattr(model, name)
            if value is None or value == []:
                continue
            write_rdf_list(
                graph,
                subject_ref_node,
                pred,
                list(value),
                registry=reg,
            )
        return graph


GRAPH_WRITE_MODES: dict[GraphMode, GraphWriteMode] = {
    "add": AddGraphMode(),
    "replace": ReplaceGraphMode(),
    "patch": PatchGraphMode(),
}


def get_graph_write_mode(mode: GraphMode) -> GraphWriteMode:
    return GRAPH_WRITE_MODES[mode]
