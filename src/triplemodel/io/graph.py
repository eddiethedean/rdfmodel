"""High-level graph serialization entrypoints."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel
from triplemodel.store import RdfGraph as Graph

from triplemodel.config import (
    GraphMode,
    RdfConfig,
    effective_graph_mode,
    get_rdf_config,
)
from triplemodel.io.export import model_to_triples
from triplemodel.io.list_fields import export_all_rdf_lists
from triplemodel.io.skolem import apply_skolemize
from triplemodel.io.writer import apply_triple_rows
from triplemodel.namespaces import bind_namespaces
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry, default_registry


def write_model_add(
    graph: Graph,
    model: BaseModel,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
    bind: bool = False,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    skolemize: bool | None = None,
) -> Graph:
    """Append triples for ``model`` to ``graph``."""
    cfg = config or get_rdf_config(type(model))
    do_skolem = cfg.skolemize_export if skolemize is None else skolemize
    graph = apply_skolemize(graph, skolemize=do_skolem)
    if bind and cfg.prefixes:
        bind_namespaces(graph, cfg.prefixes_dict)
    rows = model_to_triples(
        model, uri=uri, config=cfg, resolver=resolver, registry=registry
    )
    apply_triple_rows(graph, rows, registry=registry)
    export_all_rdf_lists(
        graph,
        model,
        subject=uri,
        config=cfg,
        resolver=resolver,
        registry=registry,
    )
    return graph


def model_to_graph(
    model: BaseModel,
    graph: Graph | None = None,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
    mode: GraphMode | None = None,
    bind: bool | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    skolemize: bool | None = None,
) -> Graph:
    """Add triples for ``model`` to ``graph`` (or a new graph) and return it."""
    cfg = config or get_rdf_config(type(model))
    resolved_mode = effective_graph_mode(mode, cfg, sync=False)
    g = Graph() if graph is None else graph
    should_bind = bind if bind is not None else graph is None

    if resolved_mode == "add":
        return write_model_add(
            g,
            model,
            uri=uri,
            config=cfg,
            bind=should_bind,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )

    from triplemodel.io.sync.modes import get_graph_write_mode

    return get_graph_write_mode(resolved_mode).apply(
        g,
        model,
        uri=uri,
        config=cfg,
        bind=should_bind,
        resolver=resolver,
        registry=registry,
        skolemize=skolemize,
    )


def models_to_graph(
    models: Sequence[BaseModel],
    graph: Graph | None = None,
    *,
    mode: GraphMode = "add",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> Graph:
    """Serialize multiple model instances into one graph."""
    g = Graph() if graph is None else graph
    for model in models:
        model_to_graph(
            model,
            g,
            mode=mode,
            bind=False,
            resolver=resolver,
            registry=registry,
        )
    return g
