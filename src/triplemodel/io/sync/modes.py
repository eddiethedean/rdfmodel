"""Graph write mode strategies (add / replace / patch)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel._typing import TripleObject
from triplemodel.config import GraphMode, RdfConfig
from triplemodel.io.export import model_to_triples
from triplemodel.io.graph import write_model_add
from triplemodel.io.list_fields import (
    collect_patch_clear_predicates,
    export_all_rdf_lists,
    predicates_to_patch_for_model,
)
from triplemodel.io.skolem import apply_skolemize
from triplemodel.io.ops import graph_set_many
from triplemodel.io.sync.nested_cleanup import (
    clear_nested_bnode_children,
    clear_nested_iri_children,
    clear_stale_nested_bnode_children,
    clear_stale_nested_iri_children,
)
from triplemodel.io.sync.inverse_ops import clear_inverse_links
from triplemodel.io.sync.predicate_ops import (
    remove_owned_triples,
    remove_triples_for_predicates,
)
from triplemodel.protocols import (
    GraphWriteMode,
    PredicateResolver as PredicateResolverProtocol,
)
from triplemodel.namespaces import bind_namespaces
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry


def predicates_to_patch(
    model: BaseModel,
    *,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> set[str]:
    """Predicates that should be cleared on the root model (field empty or None)."""
    return predicates_to_patch_for_model(model, config=config, resolver=resolver)


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
        subject = uri or config.subject_uri(model)
        clear_inverse_links(
            graph,
            model,
            subject=subject,
            config=config,
            resolver=resolver,
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
        clear_nested_iri_children(model, graph, config=config, resolver=resolver)
        clear_nested_bnode_children(
            model, graph, subject, config=config, resolver=resolver
        )
        clear_inverse_links(
            graph,
            model,
            subject=subject,
            config=config,
            resolver=resolver,
        )
        remove_owned_triples(graph, subject, cls, config=config, resolver=resolver)
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
        reg = registry or default_registry
        subject = uri or config.subject_uri(model)
        clear_stale_nested_iri_children(
            model, graph, subject, config=config, resolver=resolver
        )
        clear_stale_nested_bnode_children(
            model, graph, subject, config=config, resolver=resolver
        )
        for subj_node, to_clear in collect_patch_clear_predicates(
            model,
            subject=subject,
            config=config,
            resolver=resolver,
            graph=graph,
        ):
            remove_triples_for_predicates(graph, subj_node, to_clear)
        clear_inverse_links(
            graph,
            model,
            subject=subject,
            config=config,
            resolver=resolver,
        )

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

        export_all_rdf_lists(
            graph,
            model,
            subject=subject,
            config=config,
            resolver=resolver,
            registry=reg,
        )
        do_skolem = config.skolemize_export if skolemize is None else skolemize
        return apply_skolemize(graph, skolemize=do_skolem)


GRAPH_WRITE_MODES: dict[GraphMode, GraphWriteMode] = {
    "add": AddGraphMode(),
    "replace": ReplaceGraphMode(),
    "patch": PatchGraphMode(),
}


def get_graph_write_mode(mode: GraphMode) -> GraphWriteMode:
    return GRAPH_WRITE_MODES[mode]
