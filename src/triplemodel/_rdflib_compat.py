"""rdflib version compatibility (supports rdflib 7.0.x through 7.x)."""

from __future__ import annotations

import inspect
from typing import Any

from rdflib import Graph
from rdflib.graph import Dataset

_DEFAULT_DATASET_GRAPH_ATTRS = ("default_graph", "default_context")


def _cbd_parameters() -> dict[str, inspect.Parameter]:
    return dict(inspect.signature(Graph.cbd).parameters)


def dataset_default_graph(dataset: Dataset) -> Graph:
    """Return the dataset default graph (``default_graph`` or legacy ``default_context``)."""
    for name in _DEFAULT_DATASET_GRAPH_ATTRS:
        graph = getattr(dataset, name, None)
        if graph is not None:
            return graph
    msg = "rdflib Dataset has no default_graph or default_context"
    raise RuntimeError(msg)


def graph_cbd(
    graph: Graph,
    subject: Any,
    *,
    target_graph: Graph | None = None,
    include_reifications: bool = True,
) -> Graph:
    """Call ``Graph.cbd`` with kwargs supported by the installed rdflib."""
    params = _cbd_parameters()
    kwargs: dict[str, Any] = {}
    if target_graph is not None and "target_graph" in params:
        kwargs["target_graph"] = target_graph
    if "include_reifications" in params:
        kwargs["include_reifications"] = include_reifications
    return graph.cbd(subject, **kwargs)
