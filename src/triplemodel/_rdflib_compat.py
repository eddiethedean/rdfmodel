"""rdflib version compatibility (supports rdflib 7.0.x through 7.x)."""

from __future__ import annotations

import inspect
from typing import Any

from rdflib import Graph
from rdflib.graph import Dataset

_CBD_SUPPORTS_REIFICATIONS = (
    "include_reifications" in inspect.signature(Graph.cbd).parameters
)


def dataset_default_graph(dataset: Dataset) -> Graph:
    """Return the dataset default graph (``default_graph`` or legacy ``default_context``)."""
    default = getattr(dataset, "default_graph", None)
    if default is not None:
        return default
    return dataset.default_context


def graph_cbd(
    graph: Graph,
    subject: Any,
    *,
    target_graph: Graph | None = None,
    include_reifications: bool = True,
) -> Graph:
    """Call ``Graph.cbd`` with kwargs supported by the installed rdflib."""
    kwargs: dict[str, Any] = {}
    if target_graph is not None:
        kwargs["target_graph"] = target_graph
    if _CBD_SUPPORTS_REIFICATIONS:
        kwargs["include_reifications"] = include_reifications
    return graph.cbd(subject, **kwargs)
