"""Concise bounded description (CBD) helpers."""

from __future__ import annotations

from typing import TypeVar, cast

from pydantic import BaseModel
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel.store.cbd import cbd_subgraph as graph_cbd
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)


def cbd_graph(
    graph: Graph,
    subject: str | Node,
    *,
    target_graph: Graph | None = None,
    include_reifications: bool = True,
) -> Graph:
    """Return the concise bounded description of ``subject`` in ``graph``."""
    subj = subject if isinstance(subject, Node) else NamedNode(subject)
    return graph_cbd(
        graph,
        subj,
        target_graph=target_graph,
        include_reifications=include_reifications,
    )


def cbd_model(
    model_cls: type[T],
    graph: Graph,
    uri: str | Node,
    *,
    dispatch: bool = False,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    include_reifications: bool = True,
) -> T:
    """Load a model instance from the CBD subgraph around ``uri``."""
    sub = uri if isinstance(uri, Node) else NamedNode(uri)
    sub_graph = cbd_graph(graph, sub, include_reifications=include_reifications)
    if dispatch:
        from triplemodel.io.dispatch import graph_to_model_dispatch

        return cast(
            T,
            graph_to_model_dispatch(
                sub_graph,
                sub,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            ),
        )
    return graph_to_model(
        sub_graph,
        model_cls,
        sub,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


__all__ = ["cbd_graph", "cbd_model"]
