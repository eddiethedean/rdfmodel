"""SPARQL result wrappers compatible with former rdflib ``Result`` usage."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any, Literal

from pyoxigraph import QueryBoolean, QuerySolutions, QueryTriples

from triplemodel.store.graph import RdfGraph

SparqlResultKind = Literal[
    "bindings",
    "boolean",
    "graph",
    "json",
    "ASK",
    "SELECT",
    "CONSTRUCT",
    "DESCRIBE",
]


class Variable:
    """Minimal SPARQL variable (rdflib-compatible ``Variable('x')``)."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = str(name).lstrip("?")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Variable) and self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __str__(self) -> str:
        return self._name


class SparqlResult:
    """Adapter over pyoxigraph query results."""

    def __init__(
        self,
        *,
        result_type: SparqlResultKind,
        ask_answer: bool | None = None,
        vars_: list[Variable] | None = None,
        rows: list[Mapping[Variable, Any]] | None = None,
        graph: RdfGraph | None = None,
    ) -> None:
        self.type = result_type
        self.askAnswer = ask_answer
        self.vars = vars_
        self.graph = graph
        self._rows = rows or []

    def __iter__(self) -> Iterator[Mapping[Variable, Any]]:
        return iter(self._rows)

    @classmethod
    def from_pyoxigraph(
        cls,
        raw: QueryBoolean | QuerySolutions | QueryTriples,
        *,
        form: str,
    ) -> SparqlResult:
        if isinstance(raw, QueryBoolean):
            return cls(result_type="ASK", ask_answer=bool(raw))
        if isinstance(raw, QuerySolutions):
            ox_vars = list(raw.variables)
            vars_ = [Variable(str(v.value)) for v in ox_vars]
            rows: list[Mapping[Variable, Any]] = []
            for solution in raw:
                row = {Variable(str(v.value)): solution[str(v.value)] for v in ox_vars}
                rows.append(row)
            return cls(result_type="SELECT", vars_=vars_, rows=rows)
        graph = RdfGraph()
        for triple in raw:
            graph.add((triple.subject, triple.predicate, triple.object))
        kind: SparqlResultKind = "CONSTRUCT" if form == "construct" else "DESCRIBE"
        return cls(result_type=kind, graph=graph)


def bindings_to_substitutions(
    bindings: Mapping[Variable, Any] | None,
) -> dict[Any, Any] | None:
    if not bindings:
        return None
    from pyoxigraph import Variable as OxVariable

    out: dict[Any, Any] = {}
    for var, term in bindings.items():
        out[OxVariable(str(var))] = term
    return out
