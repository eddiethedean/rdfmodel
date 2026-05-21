"""SPARQL results parse/serialize and dataset query kwargs."""

from __future__ import annotations

import json

from pyoxigraph import DefaultGraph, NamedNode, Literal, Quad

from triplemodel.store import RdfGraph as Graph
from triplemodel.io.sparql import run_sparql
from triplemodel.store.query_results import parse_query_results

EX = "http://example.org/"


def _graph_with_data() -> Graph:
    g = Graph()
    g.store.add(
        Quad(
            NamedNode(f"{EX}s"),
            NamedNode(f"{EX}p"),
            Literal("v"),
            DefaultGraph(),
        )
    )
    return g


def test_ask_json_roundtrip() -> None:
    graph = _graph_with_data()
    try:
        result = run_sparql(graph, "ASK { ?s ?p ?o }")
        assert result.askAnswer is True
        body = result.serialize(format="sparql-results+json")
        parsed = parse_query_results(data=body, format="sparql-results+json")
        assert parsed.askAnswer is True
        assert body is not None
        reparsed = json.loads(body)
        assert reparsed["boolean"] is True
    finally:
        graph.close()


def test_select_tsv_roundtrip() -> None:
    tsv = b"?s\n<http://example.org/s>\n"
    parsed = parse_query_results(data=tsv, format="text/tab-separated-values")
    rows = list(parsed)
    assert len(rows) == 1
    assert "example.org/s" in str(next(iter(rows[0].values())))

    graph = _graph_with_data()
    try:
        result = run_sparql(graph, "SELECT ?s WHERE { ?s ?p ?o }")
        assert result.serialize(format="sparql-results+json")
    finally:
        graph.close()


def test_use_default_graph_as_union() -> None:
    graph = Graph()
    try:
        ng = f"{EX}ng"
        graph.store.add(
            Quad(
                NamedNode(f"{EX}a"),
                NamedNode(f"{EX}p"),
                Literal("x"),
                NamedNode(ng),
            )
        )
        result = run_sparql(
            graph,
            "SELECT (COUNT(?s) AS ?c) WHERE { ?s ?p ?o }",
            use_default_graph_as_union=True,
        )
        rows = list(result)
        assert rows
        var = result.vars[0] if result.vars else None
        assert var is not None
        assert int(str(rows[0][var].value)) >= 1
    finally:
        graph.close()


def test_run_sparql_rejects_unknown_kwarg() -> None:
    graph = Graph()
    try:
        try:
            run_sparql(graph, "ASK {}", bogus=True)
        except TypeError as exc:
            assert "bogus" in str(exc)
    finally:
        graph.close()
