"""Graph and model comparison helpers for tests and migrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import OxTerm, QuadPredicate, QuadSubject

from triplemodel.io.skolem import apply_skolemize
from triplemodel.store.terms import term_str

T = TypeVar("T", bound=BaseModel)

TripleTuple = tuple[str, str, str]


@dataclass(frozen=True)
class GraphDiff:
    """Structural difference between two RDF graphs."""

    only_in_first: frozenset[TripleTuple]
    only_in_second: frozenset[TripleTuple]

    @property
    def equal(self) -> bool:
        return not self.only_in_first and not self.only_in_second


def _normalize_triple(s: QuadSubject, p: QuadPredicate, o: OxTerm) -> TripleTuple:
    return (term_str(s), term_str(p), term_str(o))


def _triple_set(graph: Graph) -> frozenset[TripleTuple]:
    return frozenset(_normalize_triple(s, p, o) for s, p, o in graph)


def _prepare_for_compare(graph: Graph, *, normalize_bnodes: bool) -> Graph:
    if normalize_bnodes:
        return apply_skolemize(graph, skolemize=True)
    return graph


def graphs_equal(
    graph_a: Graph,
    graph_b: Graph,
    *,
    normalize_bnodes: bool = True,
) -> bool:
    """Return whether ``graph_a`` and ``graph_b`` are isomorphic RDF graphs."""
    a = _prepare_for_compare(graph_a, normalize_bnodes=normalize_bnodes)
    b = _prepare_for_compare(graph_b, normalize_bnodes=normalize_bnodes)
    return bool(a.isomorphic(b))


def graph_diff(
    graph_a: Graph,
    graph_b: Graph,
    *,
    normalize_bnodes: bool = True,
) -> GraphDiff:
    """Compare two graphs by normalized triple sets (after optional skolemization)."""
    a = _triple_set(_prepare_for_compare(graph_a, normalize_bnodes=normalize_bnodes))
    b = _triple_set(_prepare_for_compare(graph_b, normalize_bnodes=normalize_bnodes))
    return GraphDiff(
        only_in_first=a - b,
        only_in_second=b - a,
    )


def model_diff(
    model_a: T,
    model_b: T,
    graph: Graph | None = None,
    *,
    normalize_bnodes: bool = True,
) -> dict[str, Any]:
    """Return field-level differences between two model instances.

    When ``graph`` is provided, also includes ``graph_diff`` between
    ``model_a.to_graph()`` and ``model_b.to_graph()`` merged into the source graph.
    """
    if type(model_a) is not type(model_b):
        raise TypeError(
            f"model_diff requires the same class; got {type(model_a).__name__!r} "
            f"and {type(model_b).__name__!r}."
        )
    from triplemodel.model import TripleModel

    if not isinstance(model_a, TripleModel) or not isinstance(model_b, TripleModel):
        raise TypeError("model_diff requires TripleModel instances.")

    changes: dict[str, Any] = {}
    dump_a = model_a.model_dump()
    dump_b = model_b.model_dump()
    keys = set(dump_a) | set(dump_b)
    field_changes: dict[str, tuple[Any, Any]] = {}
    for key in sorted(keys):
        val_a = dump_a.get(key)
        val_b = dump_b.get(key)
        if val_a != val_b:
            field_changes[key] = (val_a, val_b)
    if field_changes:
        changes["fields"] = field_changes

    if graph is not None:
        g_a = Graph()
        g_b = Graph()
        cast(TripleModel, model_a).to_graph(g_a)
        cast(TripleModel, model_b).to_graph(g_b)
        diff = graph_diff(g_a, g_b, normalize_bnodes=normalize_bnodes)
        if not diff.equal:
            changes["graph"] = {
                "only_in_first": sorted(diff.only_in_first),
                "only_in_second": sorted(diff.only_in_second),
            }
    return changes


__all__ = [
    "GraphDiff",
    "graph_diff",
    "graphs_equal",
    "model_diff",
]
