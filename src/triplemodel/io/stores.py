"""pyoxigraph store factories and lifecycle helpers."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pyoxigraph import Store as OxigraphStore

from triplemodel.store import RdfGraph as Graph

_STORE_ALIASES: dict[str, str] = {
    "memory": "memory",
    "default": "memory",
    "disk": "disk",
}


def _normalize_store_name(store: str) -> str:
    key = store.strip().lower()
    if key in ("sqlalchemy", "berkeleydb", "sparql"):
        raise ValueError(
            f"Store {store!r} is not supported in TripleModel 0.10 (pyoxigraph). "
            "Use store='memory' or store='disk' with a filesystem path as identifier."
        )
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
    """Open an in-memory or on-disk graph backed by pyoxigraph.

    ``store`` may be ``memory`` / ``default`` or ``disk``. For ``disk``, ``identifier``
    is a directory path passed to :class:`pyoxigraph.Store`.
    """
    _ = create, read_only, kwargs
    normalized = _normalize_store_name(store)
    if normalized == "memory":
        return Graph()
    path = Path(identifier)
    if not identifier:
        raise ValueError("disk store requires a non-empty identifier path.")
    return Graph(store=OxigraphStore(str(path)))


@contextlib.contextmanager
def graph_store_session(graph: Graph) -> Iterator[Graph]:
    """Yield ``graph`` (pyoxigraph handles persistence for on-disk stores)."""
    yield graph


def store_commit(graph: Graph) -> None:
    """Flush an on-disk store when supported."""
    flush = getattr(graph.store, "flush", None)
    if callable(flush):
        flush()


def store_rollback(graph: Graph) -> None:
    """No-op for pyoxigraph (transactions are not exposed on ``Store``)."""
    _ = graph


def destroy_store(
    identifier: str,
    *,
    store: str = "disk",
    **kwargs: Any,
) -> None:
    """Remove an on-disk store directory."""
    _ = kwargs
    normalized = _normalize_store_name(store)
    if normalized != "disk":
        raise ValueError("destroy_store only applies to disk stores.")
    import shutil

    path = Path(identifier)
    if path.exists():
        shutil.rmtree(path)


__all__ = [
    "destroy_store",
    "graph_store_session",
    "open_graph",
    "store_commit",
    "store_rollback",
]
