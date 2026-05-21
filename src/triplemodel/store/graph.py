"""In-memory RDF graph backed by :class:`~pyoxigraph.Store`."""

from __future__ import annotations

import io
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any, overload

from typing_extensions import Self
from pyoxigraph import (
    DefaultGraph,
    NamedNode,
    Quad,
    Store as OxigraphStore,
)
from pyoxigraph import parse as ox_parse
from pyoxigraph import serialize as ox_serialize

from triplemodel.store.formats import to_rdf_format
from triplemodel.store.io_warnings import (
    warn_ignored_parse_kwargs,
    warn_ignored_serialize_kwargs,
)
from triplemodel.store.parse_source import ox_parse_from_source
from triplemodel.store.terms import (
    OxTerm,
    QuadPredicate,
    QuadSubject,
    RdfTerm,
    as_quad_object,
    as_quad_predicate,
    as_quad_subject,
    pattern_object,
    pattern_predicate,
    pattern_subject,
    term_str,
)

GraphName = DefaultGraph | NamedNode


def _graph_name(graph: GraphName | str | None) -> GraphName:
    if graph is None:
        return DefaultGraph()
    if isinstance(graph, (DefaultGraph, NamedNode)):
        return graph
    return NamedNode(graph)


class RdfGraph:
    """RDF graph (default graph of a :class:`~pyoxigraph.Store`)."""

    __slots__ = (
        "_store",
        "_graph",
        "_prefixes",
        "_ephemeral_store_path",
        "_disk_store_path",
    )

    def __init__(
        self,
        store: OxigraphStore | None = None,
        *,
        graph: GraphName | str | None = None,
        ephemeral_store_path: str | None = None,
        disk_store_path: str | None = None,
    ) -> None:
        self._store = store if store is not None else OxigraphStore()
        self._graph = _graph_name(graph)
        self._prefixes: dict[str, str] = {}
        self._ephemeral_store_path = ephemeral_store_path
        self._disk_store_path = disk_store_path

    @property
    def store(self) -> OxigraphStore:
        """Underlying pyoxigraph store (shared by dataset views)."""
        return self._store

    @property
    def graph_name(self) -> GraphName:
        return self._graph

    @property
    def identifier(self) -> str | None:
        """Named graph IRI for this view, or ``None`` for the default graph."""
        if isinstance(self._graph, NamedNode):
            return str(self._graph.value)
        return None

    @property
    def ephemeral_store_path(self) -> str | None:
        """On-disk temp directory to remove when :meth:`close` is called (if any)."""
        return self._ephemeral_store_path

    @property
    def disk_store_path(self) -> str | None:
        """Persistent on-disk store directory when opened with ``open_graph('disk', path)``."""
        return self._disk_store_path

    def close(self) -> None:
        """Close the underlying store and remove an ephemeral on-disk directory.

        pyoxigraph releases on-disk locks when the ``Store`` object is dropped; there is
        no explicit ``close()`` on :class:`~pyoxigraph.Store`.
        """
        import gc

        from triplemodel.store.ops import store_flush

        try:
            store_flush(self)
        except Exception as exc:
            warnings.warn(
                f"Failed to flush store before close: {exc}",
                ResourceWarning,
                stacklevel=2,
            )
        ephemeral = self._ephemeral_store_path
        self._ephemeral_store_path = None
        self._store = OxigraphStore()
        gc.collect()
        if ephemeral is not None:
            from triplemodel.io.stores import cleanup_ephemeral_store_path

            cleanup_ephemeral_store_path(ephemeral)

    def bind(self, prefix: str, namespace: str | object) -> None:
        """Record a prefix for serialization (pyoxigraph has no Graph.bind)."""
        self._prefixes[prefix] = str(namespace)

    def namespaces(self) -> Iterator[tuple[str, str]]:
        yield from self._prefixes.items()

    def add(
        self,
        triple: tuple[
            RdfTerm | QuadSubject | str,
            RdfTerm | QuadPredicate | str,
            RdfTerm | OxTerm | str,
        ],
    ) -> None:
        s, p, o = triple
        self._store.add(
            Quad(
                as_quad_subject(s),
                as_quad_predicate(p),
                as_quad_object(o),
                self._graph,
            )
        )

    def remove(
        self,
        triple: tuple[
            RdfTerm | QuadSubject | str,
            RdfTerm | QuadPredicate | str,
            RdfTerm | OxTerm | str,
        ],
    ) -> None:
        s, p, o = triple
        self._store.remove(
            Quad(
                as_quad_subject(s),
                as_quad_predicate(p),
                as_quad_object(o),
                self._graph,
            )
        )

    def objects(
        self,
        subject: RdfTerm | QuadSubject | str | None,
        predicate: RdfTerm | str | None,
    ) -> Iterator[OxTerm]:
        subj = pattern_subject(subject)
        pred = pattern_predicate(predicate)
        for quad in self._store.quads_for_pattern(subj, pred, None, self._graph):
            yield quad.object

    def subject_objects(
        self, predicate: RdfTerm | str
    ) -> Iterator[tuple[QuadSubject, OxTerm]]:
        """Yield ``(subject, object)`` pairs for ``predicate``."""
        pred = pattern_predicate(predicate)
        for quad in self._store.quads_for_pattern(None, pred, None, self._graph):
            yield quad.subject, quad.object

    def subjects(
        self,
        predicate: RdfTerm | str | None = None,
        object_: RdfTerm | OxTerm | str | None = None,
    ) -> Iterator[QuadSubject]:
        pred = pattern_predicate(predicate)
        obj = pattern_object(object_)
        for quad in self._store.quads_for_pattern(None, pred, obj, self._graph):
            yield quad.subject

    def triples(
        self,
        pattern: tuple[
            RdfTerm | str | None,
            RdfTerm | str | None,
            RdfTerm | str | None,
        ],
    ) -> Iterator[tuple[QuadSubject, QuadPredicate, OxTerm]]:
        s, p, o = pattern
        for quad in self._store.quads_for_pattern(
            pattern_subject(s),
            pattern_predicate(p),
            pattern_object(o),
            self._graph,
        ):
            yield (quad.subject, quad.predicate, quad.object)

    def __iter__(self) -> Iterator[tuple[QuadSubject, QuadPredicate, OxTerm]]:
        return self.triples((None, None, None))

    def __len__(self) -> int:
        return sum(1 for _ in self.triples((None, None, None)))

    def __contains__(
        self,
        triple: tuple[
            RdfTerm | QuadSubject | str,
            RdfTerm | QuadPredicate | str,
            RdfTerm | OxTerm | str,
        ],
    ) -> bool:
        s, p, o = triple
        for _ in self._store.quads_for_pattern(
            as_quad_subject(s),
            as_quad_predicate(p),
            as_quad_object(o),
            self._graph,
        ):
            return True
        return False

    def query(self, query: str, **kwargs: Any) -> Any:
        from triplemodel.io.sparql import detect_query_form
        from triplemodel.store.sparql_result import SparqlResult

        prefixes = kwargs.pop("prefixes", None)
        if prefixes is None and self._prefixes:
            prefixes = dict(self._prefixes)
        elif prefixes is not None and self._prefixes:
            prefixes = {**self._prefixes, **dict(prefixes)}
        raw = self._store.query(query, prefixes=prefixes, **kwargs)
        return SparqlResult.from_pyoxigraph(raw, form=detect_query_form(query))

    def update(self, update: str, **kwargs: Any) -> None:
        self._store.update(update, **kwargs)

    def parse(
        self,
        source: str | Path | None = None,
        *,
        data: str | bytes | None = None,
        format: str | None = None,
        base_iri: str | None = None,
        **kwargs: Any,
    ) -> Self:
        ox_kwargs = warn_ignored_parse_kwargs(kwargs, stacklevel=3)
        if format is None:
            raise ValueError("parse() requires format=")
        rdf_format = to_rdf_format(format)
        base = base_iri
        if data is not None:
            payload: str | bytes | io.IOBase
            if isinstance(data, str):
                payload = data.encode("utf-8")
            else:
                payload = data
            quads = ox_parse(payload, format=rdf_format, base_iri=base, **ox_kwargs)
        elif source is not None:
            quads = ox_parse_from_source(source, format=rdf_format, base_iri=base)
        else:
            raise ValueError("parse() requires source= or data=")
        self._store.bulk_extend(quads)
        return self

    @overload
    def serialize(
        self,
        destination: None = None,
        *,
        format: str = "turtle",
        **kwargs: Any,
    ) -> str: ...

    @overload
    def serialize(
        self,
        destination: str | Path | io.IOBase,
        *,
        format: str = "turtle",
        **kwargs: Any,
    ) -> None: ...

    def serialize(
        self,
        destination: str | Path | io.IOBase | None = None,
        *,
        format: str = "turtle",
        **kwargs: Any,
    ) -> str | None:
        ox_kwargs = warn_ignored_serialize_kwargs(kwargs, stacklevel=3)
        rdf_format = to_rdf_format(format)
        prefixes = self._prefixes or None
        payload = (
            ox_serialize(
                self._store,
                format=rdf_format,
                prefixes=prefixes,
                **ox_kwargs,
            )
            or b""
        )
        if destination is None:
            return payload.decode("utf-8")
        if isinstance(destination, (str, Path)):
            Path(destination).write_bytes(payload)
            return None
        destination.write(payload)
        return None

    def transitive_objects(
        self,
        subject: RdfTerm | QuadSubject | str,
        predicate: RdfTerm | str,
    ) -> list[OxTerm]:
        """Follow ``predicate`` transitively from ``subject`` (objects as next subjects)."""
        from triplemodel.store.terms import term_key

        start = as_quad_subject(subject)
        pred = pattern_predicate(predicate)
        assert pred is not None
        visited: set[str] = set()
        frontier: list[QuadSubject] = [start]
        results: list[OxTerm] = []
        while frontier:
            current = frontier.pop()
            key = term_key(current)
            if key in visited:
                continue
            visited.add(key)
            for obj in self.objects(current, pred):
                results.append(obj)
                if isinstance(obj, NamedNode):
                    frontier.append(obj)
        return results

    def transitive_subjects(
        self,
        predicate: RdfTerm | str,
        obj: RdfTerm | OxTerm | str,
    ) -> list[QuadSubject]:
        """Follow ``predicate`` transitively backward to subjects."""
        from triplemodel.store.terms import term_key

        start = as_quad_object(obj)
        pred = pattern_predicate(predicate)
        assert pred is not None
        visited: set[str] = set()
        frontier: list[OxTerm] = [start]
        results: list[QuadSubject] = []
        while frontier:
            current = frontier.pop()
            key = term_key(current)
            if key in visited:
                continue
            visited.add(key)
            for subj in self.subjects(pred, current):
                results.append(subj)
                if isinstance(subj, NamedNode):
                    frontier.append(subj)
        return results

    def skolemize(self, *, new_graph: RdfGraph | None = None) -> RdfGraph:
        from triplemodel.store.skolem import skolemize_graph

        _ = new_graph
        return skolemize_graph(self)

    def de_skolemize(self) -> RdfGraph:
        from triplemodel.store.skolem import de_skolemize_graph

        return de_skolemize_graph(self)

    def cbd(
        self,
        subject: RdfTerm | str,
        *,
        target_graph: RdfGraph | None = None,
        include_reifications: bool = True,
    ) -> RdfGraph:
        from triplemodel.store.cbd import cbd_subgraph

        return cbd_subgraph(
            self,
            subject,
            target_graph=target_graph,
            include_reifications=include_reifications,
        )

    def isomorphic(self, other: RdfGraph) -> bool:
        a = frozenset((term_str(s), term_str(p), term_str(o)) for s, p, o in self)
        b = frozenset((term_str(s), term_str(p), term_str(o)) for s, p, o in other)
        return a == b

    def __add__(self, other: RdfGraph) -> RdfGraph:
        merged = RdfGraph()
        for quad in self._store:
            merged._store.add(quad)
        for quad in other._store:
            merged._store.add(quad)
        merged._prefixes = {**self._prefixes, **other._prefixes}
        return merged
