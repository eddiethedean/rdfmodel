"""Named-graph dataset backed by a single :class:`~pyoxigraph.Store`."""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pyoxigraph import DefaultGraph, NamedNode, Store as OxigraphStore

from triplemodel.store.formats import to_rdf_format
from triplemodel.store.graph import RdfGraph
from pyoxigraph import parse as ox_parse
from pyoxigraph import serialize as ox_serialize


class RdfDataset:
    """Dataset view over one pyoxigraph store (default + named graphs)."""

    __slots__ = ("_store", "_prefixes")

    def __init__(self, store: OxigraphStore | None = None) -> None:
        self._store = store if store is not None else OxigraphStore()
        self._prefixes: dict[str, str] = {}

    @property
    def store(self) -> OxigraphStore:
        return self._store

    @property
    def default_context(self) -> RdfGraph:
        return RdfGraph(self._store, graph=DefaultGraph())

    @property
    def default_graph(self) -> RdfGraph:
        return self.default_context

    def graph(self, graph_iri: NamedNode | str) -> RdfGraph:
        name = graph_iri if isinstance(graph_iri, NamedNode) else NamedNode(graph_iri)
        return RdfGraph(self._store, graph=name)

    def contexts(self) -> Iterator[RdfGraph]:
        yield self.default_context
        for name in self._store.named_graphs():
            if isinstance(name, NamedNode):
                yield RdfGraph(self._store, graph=name)

    @property
    def graphs(self) -> list[RdfGraph]:
        return list(self.contexts())

    def quads(
        self,
        pattern: tuple[Any, Any, Any, Any] | None = None,
    ) -> Iterator[Any]:
        """Iterate quads, optionally filtered by ``(s, p, o, graph)`` (rdflib-compatible)."""
        from pyoxigraph import DefaultGraph

        if pattern is None:
            yield from self._store
            return
        s, p, o, graph = pattern
        if graph is None:
            graph_name: DefaultGraph | NamedNode = DefaultGraph()
        elif isinstance(graph, RdfGraph):
            graph_name = graph.graph_name
        elif isinstance(graph, (DefaultGraph, NamedNode)):
            graph_name = graph
        else:
            graph_name = NamedNode(str(graph))
        for quad in self._store.quads_for_pattern(s, p, o, graph_name):
            yield quad

    def bind(self, prefix: str, namespace: str | object) -> None:
        self._prefixes[prefix] = str(namespace)

    def parse(
        self,
        source: str | Path | None = None,
        *,
        data: str | bytes | None = None,
        format: str | None = None,
        publicID: str | None = None,
        **kwargs: Any,
    ) -> None:
        _ = kwargs
        if format is None:
            raise ValueError("parse() requires format=")
        rdf_format = to_rdf_format(format)
        base = publicID
        if data is not None:
            payload = data.encode("utf-8") if isinstance(data, str) else data
            quads = ox_parse(payload, format=rdf_format, base_iri=base)
        elif source is not None:
            src = Path(source) if not isinstance(source, Path) else source
            quads = ox_parse(src.read_bytes(), format=rdf_format, base_iri=base)
        else:
            raise ValueError("parse() requires source= or data=")
        self._store.bulk_extend(quads)

    def query(self, query: str, **kwargs: Any) -> Any:
        return self._store.query(query, **kwargs)

    def serialize(
        self,
        destination: str | Path | io.IOBase | None = None,
        *,
        format: str = "trig",
        **kwargs: Any,
    ) -> str | None:
        _ = kwargs
        rdf_format = to_rdf_format(format)
        prefixes = self._prefixes or None
        payload = ox_serialize(self._store, format=rdf_format, prefixes=prefixes) or b""
        if destination is None:
            return payload.decode("utf-8")
        if isinstance(destination, (str, Path)):
            Path(destination).write_bytes(payload)
            return None
        destination.write(payload)
        return None
