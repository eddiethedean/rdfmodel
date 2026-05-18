"""Sync model state into graphs with add / replace / patch semantics."""

from __future__ import annotations

from pydantic import BaseModel
from rdflib import Graph

from triplemodel.config import (
    GraphMode,
    RdfConfig,
    effective_graph_mode,
    get_rdf_config,
)
from triplemodel.io.sync.modes import (
    AddGraphMode,
    PatchGraphMode,
    ReplaceGraphMode,
    predicates_to_patch,
)
from triplemodel.io.sync.nested_cleanup import (
    clear_nested_iri_children,
    clear_stale_nested_iri_children,
)
from triplemodel.io.sync.predicate_ops import remove_owned_triples
from triplemodel.namespaces import bind_namespaces
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry, default_registry

__all__ = [
    "clear_nested_iri_children",
    "clear_stale_nested_iri_children",
    "predicates_to_patch",
    "remove_owned_triples",
    "sync_to_graph",
]


def sync_to_graph(
    model: BaseModel,
    graph: Graph | None = None,
    *,
    uri: str | None = None,
    mode: GraphMode | None = None,
    config: RdfConfig | None = None,
    bind: bool = True,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    skolemize: bool | None = None,
) -> Graph:
    """Write ``model`` into ``graph`` using ``mode`` sync semantics."""
    g = Graph() if graph is None else graph
    cfg = config or get_rdf_config(type(model))
    resolved_mode = effective_graph_mode(mode, cfg, sync=True)

    if bind and cfg.prefixes:
        bind_namespaces(g, cfg.prefixes_dict)

    if resolved_mode == "add":
        return AddGraphMode().apply(
            g,
            model,
            uri=uri,
            config=cfg,
            bind=False,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )

    if resolved_mode == "replace":
        return ReplaceGraphMode().apply(
            g,
            model,
            uri=uri,
            config=cfg,
            bind=False,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )

    return PatchGraphMode().apply(
        g,
        model,
        uri=uri,
        config=cfg,
        bind=False,
        resolver=resolver,
        registry=registry,
        skolemize=skolemize,
    )
