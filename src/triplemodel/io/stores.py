"""rdflib store factories and lifecycle helpers."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

from rdflib import Graph

_STORE_ALIASES: dict[str, str] = {
    "memory": "default",
    "default": "default",
    "sqlalchemy": "SQLAlchemy",
    "berkeleydb": "BerkeleyDB",
    "sparql": "sparql",
}


def _normalize_store_name(store: str) -> str:
    key = store.strip().lower()
    if key not in _STORE_ALIASES:
        supported = ", ".join(sorted(_STORE_ALIASES))
        raise ValueError(f"Unknown store {store!r}; supported: {supported}.")
    return _STORE_ALIASES[key]


def open_graph(
    store: str,
    identifier: str = "",
    *,
    create: bool = True,
    read_only: bool = False,
    **kwargs: Any,
) -> Graph:
    """Open an rdflib ``Graph`` backed by ``store``.

    ``store`` may be ``memory``, ``sqlalchemy``, ``berkeleydb``, or ``sparql``.
    For ``sparql``, ``identifier`` is the endpoint URL (delegates to
    :func:`triplemodel.io.sparql.open_sparql_graph`).
    """
    normalized = _normalize_store_name(store)
    if normalized == "sparql":
        from triplemodel.io.sparql import open_sparql_graph

        return open_sparql_graph(identifier, read_only=read_only, **kwargs)
    if normalized == "default":
        return Graph(identifier=identifier or None, **kwargs)
    graph = Graph(store=normalized, identifier=identifier, **kwargs)
    opened = getattr(graph.store, "open", None)
    if callable(opened):
        config = identifier if isinstance(identifier, str) else str(identifier)
        opened(config, create=create)
    return graph


@contextlib.contextmanager
def graph_store_session(graph: Graph) -> Iterator[Graph]:
    """Call ``store.open()`` on enter and ``store.close()`` on exit when supported."""
    store = graph.store
    opened = getattr(store, "open", None)
    closed = getattr(store, "close", None)
    if callable(opened):
        opened(graph.identifier)
    try:
        yield graph
    finally:
        if callable(closed):
            closed()


def store_commit(graph: Graph) -> None:
    """Commit the backing store when ``commit`` is available (no-op for memory)."""
    commit = getattr(graph.store, "commit", None)
    if callable(commit):
        commit()


def store_rollback(graph: Graph) -> None:
    """Rollback the backing store when ``rollback`` is available (no-op for memory)."""
    rollback = getattr(graph.store, "rollback", None)
    if callable(rollback):
        rollback()


def destroy_store(
    identifier: str,
    *,
    store: str = "sqlalchemy",
    **kwargs: Any,
) -> None:
    """Destroy an on-disk store when the backend supports ``destroy``."""
    normalized = _normalize_store_name(store)
    if normalized == "default":
        raise ValueError("destroy_store does not apply to in-memory graphs.")
    config = str(identifier)
    graph = Graph(store=normalized, **kwargs)
    backing = graph.store
    destroy = getattr(backing, "destroy", None)
    if destroy is None or not callable(destroy):
        raise ValueError(f"Store {store!r} does not support destroy().")
    opened = getattr(backing, "open", None)
    if callable(opened):
        opened(config, create=False)
    destroy(config)


__all__ = [
    "destroy_store",
    "graph_store_session",
    "open_graph",
    "store_commit",
    "store_rollback",
]
