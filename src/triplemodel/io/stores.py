"""pyoxigraph store factories and lifecycle helpers."""

from __future__ import annotations

import contextlib
import warnings
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

_LEGACY_STORE_ALIASES: dict[str, str] = {
    "sqlalchemy": "disk",
    "berkeleydb": "disk",
}


def coerce_store_name(store: str, *, stacklevel: int = 2) -> str:
    """Normalize ``store``; map legacy backend alias names to ``disk``."""
    key = store.strip().lower()
    if key in _LEGACY_STORE_ALIASES:
        warnings.warn(
            f"store={store!r} is deprecated in TripleModel 0.10; "
            "use store='disk' with a directory path (see docs/MIGRATION_0.10.md).",
            DeprecationWarning,
            stacklevel=stacklevel,
        )
        return _LEGACY_STORE_ALIASES[key]
    return store


def _normalize_store_name(store: str) -> str:
    store = coerce_store_name(store, stacklevel=3)
    key = store.strip().lower()
    if key == "sparql":
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
    ephemeral_store_path: str | None = None,
    **kwargs: Any,
) -> Graph:
    """Open an in-memory or on-disk graph backed by pyoxigraph.

    ``store`` may be ``memory`` / ``default`` or ``disk``. For ``disk``, ``identifier``
    is a directory path passed to :class:`pyoxigraph.Store`.

    When ``read_only=True``, opens with :meth:`pyoxigraph.Store.read_only` (undefined
    behavior if another process writes the same path). When ``create=False``, raises
    :exc:`FileNotFoundError` if the directory does not exist.
    """
    if kwargs:
        warnings.warn(
            f"open_graph() ignored unsupported keyword arguments: {sorted(kwargs)}",
            stacklevel=2,
        )
    normalized = _normalize_store_name(store)
    if normalized == "memory":
        if read_only or not create:
            warnings.warn(
                "open_graph(memory): create= and read_only= are ignored for in-memory stores.",
                stacklevel=2,
            )
        return Graph()
    path = Path(identifier)
    if not identifier:
        raise ValueError("disk store requires a non-empty identifier path.")
    if not create and not path.exists():
        raise FileNotFoundError(f"disk store path does not exist: {path}")
    if read_only:
        ox = OxigraphStore.read_only(str(path))
    else:
        ox = OxigraphStore(str(path))
    return Graph(
        store=ox,
        ephemeral_store_path=ephemeral_store_path,
    )


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


def cleanup_ephemeral_store_path(path: str) -> None:
    """Remove a temporary on-disk store directory (non-throwing on failure)."""
    try:
        destroy_store(path, store="disk")
    except Exception as exc:
        warnings.warn(
            f"Failed to remove ephemeral store at {path!r}: {exc}",
            ResourceWarning,
            stacklevel=2,
        )


__all__ = [
    "cleanup_ephemeral_store_path",
    "coerce_store_name",
    "destroy_store",
    "graph_store_session",
    "open_graph",
    "store_commit",
    "store_rollback",
]
