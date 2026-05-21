"""pyoxigraph Store operations (bulk load, backup, named graphs, patterns)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pyoxigraph import BlankNode, DefaultGraph, NamedNode, Quad, Store as OxigraphStore

from triplemodel.store import RdfGraph as Graph
from triplemodel.store.formats import to_rdf_format
from triplemodel.store.graph import GraphName, _graph_name


def _resolve_store(graph: Graph | None, store_path: str | Path | None) -> OxigraphStore:
    if graph is not None:
        return graph.store
    if store_path is None:
        raise ValueError("Pass graph= or store_path= for this operation.")
    return OxigraphStore(str(store_path))


def _resolve_disk_path(graph: Graph | None, store_path: str | Path | None) -> Path:
    if store_path is not None:
        return Path(store_path)
    if graph is None:
        raise ValueError("Pass graph= or store_path= for disk store operations.")
    path = graph.disk_store_path or graph.ephemeral_store_path
    if path is None:
        raise ValueError(
            "Disk store operations require open_graph('disk', path) or parse_into_store_graph; "
            "pass store_path= explicitly for a pyoxigraph on-disk directory."
        )
    return Path(path)


def _coerce_graph_name(
    graph: Graph | None,
    to_graph: str | NamedNode | DefaultGraph | None,
) -> NamedNode | DefaultGraph | None:
    if to_graph is None:
        if graph is not None:
            return graph.graph_name
        return None
    return _graph_name(to_graph)


def bulk_load_into_graph(
    graph: Graph,
    source: str | Path | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    base_iri: str | None = None,
    to_graph: str | NamedNode | DefaultGraph | None = None,
    lenient: bool = False,
) -> None:
    """Load RDF from a file or bytes into ``graph.store`` via :meth:`pyoxigraph.Store.bulk_load`."""
    from triplemodel.io.files import infer_format

    if data is not None and source is not None:
        raise ValueError("Pass source= or data=, not both.")
    if data is None and source is None:
        raise ValueError("bulk_load_into_graph requires source= or data=.")
    hint: str | Path | None = source if data is None else None
    fmt = infer_format(hint, format)
    rdf_format = to_rdf_format(fmt)
    target = _coerce_graph_name(graph, to_graph)
    if data is not None:
        payload: str | bytes = data.encode("utf-8") if isinstance(data, str) else data
        graph.store.bulk_load(
            payload,
            format=rdf_format,
            base_iri=base_iri,
            to_graph=target,
            lenient=lenient,
        )
    elif source is not None:
        graph.store.bulk_load(
            format=rdf_format,
            path=str(source),
            base_iri=base_iri,
            to_graph=target,
            lenient=lenient,
        )


def dump_store(
    output: str | Path,
    *,
    graph: Graph | None = None,
    store_path: str | Path | None = None,
    format: str = "nquads",
    from_graph: str | NamedNode | DefaultGraph | None = None,
    prefixes: dict[str, str] | None = None,
    base_iri: str | None = None,
) -> None:
    """Dump an on-disk store to a file (default N-Quads)."""
    store = _resolve_store(graph, store_path)
    rdf_format = to_rdf_format(format)
    graph_name = (
        _coerce_graph_name(graph, from_graph) if from_graph is not None else None
    )
    if graph is not None and from_graph is None:
        graph_name = graph.graph_name
    prefix_map = prefixes
    if prefix_map is None and graph is not None:
        prefix_map = dict(graph._prefixes) or None
    store.dump(
        str(output),
        format=rdf_format,
        from_graph=graph_name,
        prefixes=prefix_map,
        base_iri=base_iri,
    )


def load_store(
    graph: Graph,
    source: str | Path | None = None,
    *,
    data: str | bytes | None = None,
    format: str = "nquads",
    base_iri: str | None = None,
    to_graph: str | NamedNode | DefaultGraph | None = None,
    lenient: bool = False,
) -> None:
    """Load a dump file into an on-disk store backing ``graph``."""
    from triplemodel.io.files import infer_format

    if data is not None and source is not None:
        raise ValueError("Pass source= or data=, not both.")
    hint: str | Path | None = source if data is None else None
    fmt = infer_format(hint, format)
    rdf_format = to_rdf_format(fmt)
    target = _coerce_graph_name(graph, to_graph)
    if data is not None:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        graph.store.load(
            payload,
            format=rdf_format,
            base_iri=base_iri,
            to_graph=target,
            lenient=lenient,
        )
    elif source is not None:
        graph.store.load(
            format=rdf_format,
            path=str(source),
            base_iri=base_iri,
            to_graph=target,
            lenient=lenient,
        )
    else:
        raise ValueError("load_store requires source= or data=.")


def backup_store(
    target_directory: str | Path,
    *,
    graph: Graph | None = None,
    store_path: str | Path | None = None,
) -> None:
    """Create a backup of an on-disk pyoxigraph store directory."""
    if graph is not None:
        graph.store.backup(str(target_directory))
        return
    path = _resolve_disk_path(None, store_path)
    OxigraphStore(str(path)).backup(str(target_directory))


def optimize_store(
    *,
    graph: Graph | None = None,
    store_path: str | Path | None = None,
) -> None:
    """Optimize an on-disk store after bulk import or heavy updates."""
    if graph is not None:
        graph.store.optimize()
        return
    path = _resolve_disk_path(None, store_path)
    OxigraphStore(str(path)).optimize()


def store_flush(graph: Graph) -> None:
    """Flush pending writes on an on-disk store (no-op if unsupported)."""
    flush = getattr(graph.store, "flush", None)
    if callable(flush):
        flush()


def list_named_graphs(graph: Graph) -> list[str]:
    """Return IRIs of all named graphs in ``graph.store``."""
    out: list[str] = []
    for name in graph.store.named_graphs():
        if isinstance(name, NamedNode):
            out.append(str(name.value))
        elif isinstance(name, BlankNode):
            out.append(str(name))
    return out


def ensure_named_graph(graph: Graph, graph_iri: str) -> None:
    """Ensure a named graph exists in the store."""
    graph.store.add_graph(NamedNode(graph_iri))


def clear_named_graph(graph: Graph, graph_iri: str) -> None:
    """Remove all quads from a named graph."""
    graph.store.clear_graph(NamedNode(graph_iri))


def remove_named_graph(graph: Graph, graph_iri: str) -> None:
    """Remove a named graph and its quads from the store."""
    graph.store.remove_graph(NamedNode(graph_iri))


def iter_quads_for_pattern(
    graph: Graph,
    subject: Any = None,
    predicate: Any = None,
    obj: Any = None,
    *,
    graph_iri: str | NamedNode | DefaultGraph | None = None,
) -> Iterator[Quad]:
    """Iterate quads matching an optional ``(s, p, o, graph)`` pattern on ``graph.store``."""
    from triplemodel.store.terms import (
        pattern_object,
        pattern_predicate,
        pattern_subject,
    )

    s = pattern_subject(subject)
    p = pattern_predicate(predicate)
    o = pattern_object(obj)
    if graph_iri is None:
        graph_name: GraphName = graph.graph_name
    else:
        graph_name = _graph_name(graph_iri)
    yield from graph.store.quads_for_pattern(s, p, o, graph_name)


__all__ = [
    "backup_store",
    "bulk_load_into_graph",
    "clear_named_graph",
    "dump_store",
    "ensure_named_graph",
    "iter_quads_for_pattern",
    "list_named_graphs",
    "load_store",
    "optimize_store",
    "remove_named_graph",
    "store_flush",
]
