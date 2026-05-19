"""Tests for SPARQL passthrough helpers."""

from __future__ import annotations

from typing import Annotated, Any, cast
from unittest.mock import MagicMock, patch

import pytest
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.vocab import FOAF as FOAF_NS

from triplemodel import IriId, TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.sparql import (
    PreparedModelQuery,
    apply_update,
    ask,
    construct_models,
    detect_query_form,
    graph_from_construct_result,
    init_bindings_from_model,
    init_ns_from_model,
    load_sparql,
    open_sparql_graph,
    prepare_model_query,
    run_sparql,
    select_models,
)

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")
    age: int | None = rdf_field("foaf:age", default=None)


class PersonIriId(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "uri"

    uri: Annotated[str, IriId()]
    name: str = rdf_field("foaf:name")


def _foaf_graph() -> Graph:
    g = Graph()
    g.bind("foaf", FOAF_NS)
    alice = NamedNode(f"{EX}alice")
    g.add((alice, NamedNode(RDF_TYPE), NamedNode(f"{FOAF}Person")))
    g.add((alice, NamedNode(f"{FOAF}name"), Literal("Alice")))
    g.add((alice, NamedNode(f"{FOAF}age"), Literal(30)))
    bob = NamedNode(f"{EX}bob")
    g.add((bob, NamedNode(RDF_TYPE), NamedNode(f"{FOAF}Person")))
    g.add((bob, NamedNode(f"{FOAF}name"), Literal("Bob")))
    return g


def test_detect_query_form():
    assert detect_query_form("SELECT ?s WHERE { ?s a ?o }") == "select"
    assert (
        detect_query_form("  # comment\nCONSTRUCT { ?s ?p ?o } WHERE {}") == "construct"
    )
    assert detect_query_form("DESCRIBE <http://example.org/>") == "describe"
    assert detect_query_form("ASK { ?s a ?o }") == "ask"
    assert detect_query_form("PREFIX x: <http://x/> INSERT {}") == "unknown"


def test_init_ns_from_model():
    ns = init_ns_from_model(Person)
    assert "foaf" in ns
    assert str(ns["foaf"]).startswith("http://xmlns.com/foaf")


def test_init_bindings_from_model():
    p = Person(slug="alice", name="Alice", age=30)
    bindings = init_bindings_from_model(p, {"slug": "slug", "n": "name"})
    assert len(bindings) == 2
    from triplemodel.store.sparql_result import Variable as V

    assert bindings[V("slug")] == NamedNode(f"{EX}alice")
    assert str(bindings[V("n")].value) == "Alice"
    with pytest.raises(ValueError, match="Unknown model field"):
        init_bindings_from_model(p, {"x": "missing"})


def test_ask_true_false():
    g = _foaf_graph()
    assert Person.ask_sparql(
        g,
        "ASK { ?s a <http://xmlns.com/foaf/0.1/Person> }",
    )
    assert not ask(
        g,
        "ASK { ?s a <http://example.org/not-a-type> }",
        model_cls=Person,
    )


def test_ask_wrong_result_type():
    g = _foaf_graph()
    with pytest.raises(TypeError, match="boolean"):
        ask(g, "SELECT ?s WHERE { ?s a ?o } LIMIT 1", model_cls=Person)


def test_construct_models():
    g = _foaf_graph()
    query = """
    CONSTRUCT { ?s ?p ?o }
    WHERE {
      ?s a foaf:Person .
      ?s ?p ?o .
    }
    """
    people = construct_models(Person, g, query)
    assert len(people) == 2
    names = {p.name for p in people}
    assert names == {"Alice", "Bob"}


def test_construct_models_classmethod():
    g = _foaf_graph()
    people = Person.construct_from_sparql(
        g,
        """
        CONSTRUCT { ?s ?p ?o }
        WHERE { ?s a foaf:Person . ?s ?p ?o . }
        """,
    )
    assert len(people) == 2


def test_construct_models_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    g = _foaf_graph()
    seen: list[bool] = []

    def _fake_dispatch(graph: Graph, **kwargs: object) -> list[Person]:
        seen.append(True)
        return Person.all_from_graph(graph)

    monkeypatch.setattr(
        "triplemodel.io.dispatch.all_from_graph_dispatch",
        _fake_dispatch,
    )
    people = construct_models(
        Person,
        g,
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s a foaf:Person . ?s ?p ?o . }",
        dispatch=True,
    )
    assert seen
    assert len(people) == 2


def test_graph_from_construct_result_wrong_type():
    g = _foaf_graph()
    result = g.query("SELECT ?s WHERE { ?s a foaf:Person }")
    with pytest.raises(TypeError, match="graph SPARQL result"):
        graph_from_construct_result(result)


def test_select_models_projection():
    g = _foaf_graph()
    rows = select_models(
        Person,
        g,
        """
        SELECT ?slug ?name WHERE {
          ?s a foaf:Person .
          ?s foaf:name ?name .
          BIND(REPLACE(STR(?s), "http://example.org/people/", "") AS ?slug)
        }
        """,
    )
    assert len(rows) == 2
    assert {r.slug for r in rows} == {"alice", "bob"}


def test_select_models_subject_var():
    g = _foaf_graph()
    rows = select_models(
        Person,
        g,
        "SELECT ?s ?name WHERE { ?s a foaf:Person . ?s foaf:name ?name }",
        subject_var="s",
        field_map={"name": "name"},
    )
    assert len(rows) == 2
    assert {r.slug for r in rows} == {"alice", "bob"}


def test_select_models_iri_id_subject():
    g = _foaf_graph()
    rows = select_models(
        PersonIriId,
        g,
        "SELECT ?s ?name WHERE { ?s a foaf:Person . ?s foaf:name ?name }",
        subject_var="s",
        field_map={"name": "name"},
    )
    assert rows[0].uri.endswith("alice") or rows[0].uri.endswith("bob")


def test_select_models_field_map_error():
    g = _foaf_graph()
    with pytest.raises(ValueError, match="field_map"):
        select_models(
            Person,
            g,
            "SELECT ?name WHERE { ?s foaf:name ?name }",
            field_map={"name": "not_a_field"},
        )


def test_select_models_hydrate():
    g = _foaf_graph()
    people = select_models(
        Person,
        g,
        "SELECT ?s WHERE { ?s a foaf:Person }",
        subject_var="s",
        hydrate=True,
    )
    assert len(people) == 2
    assert Person.select_from_sparql(
        g,
        "SELECT ?s WHERE { ?s a foaf:Person }",
        subject_var="s",
        hydrate=True,
    )


def test_select_models_hydrate_requires_subject_var():
    g = _foaf_graph()
    with pytest.raises(ValueError, match="subject_var"):
        select_models(Person, g, "SELECT ?s WHERE { ?s a ?o }", hydrate=True)


def test_select_models_wrong_result_type():
    g = _foaf_graph()
    with pytest.raises(TypeError, match="bindings"):
        select_models(Person, g, "ASK { ?s a foaf:Person }")


def test_select_models_subject_without_id_field():
    class NoId(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"

        name: str = rdf_field("foaf:name")

    g = _foaf_graph()
    with pytest.raises(ValueError, match="id_field"):
        select_models(
            NoId,
            g,
            "SELECT ?s ?name WHERE { ?s foaf:name ?name }",
            subject_var="s",
            field_map={"name": "name"},
        )


def test_apply_update_insert():
    g = Graph()
    apply_update(
        g,
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        INSERT DATA { <http://example.org/people/x> a foaf:Person . }
        """,
        model_cls=Person,
    )
    assert len(list(g)) == 1


def test_prepare_model_query():
    pq = prepare_model_query(
        Person,
        "SELECT ?name WHERE { ?s foaf:name ?name }",
    )
    assert isinstance(pq, PreparedModelQuery)
    g = _foaf_graph()
    result = pq.execute(g)
    assert result.type in ("SELECT", "bindings")
    assert pq.as_result(g).type in ("SELECT", "bindings")


def test_run_sparql_without_model_cls():
    g = _foaf_graph()
    result = run_sparql(g, "SELECT ?s WHERE { ?s a foaf:Person }")
    assert result.type in ("SELECT", "bindings")


def test_open_sparql_graph_read_only() -> None:
    with pytest.raises(NotImplementedError, match="open_sparql_graph"):
        open_sparql_graph("http://example.invalid/sparql", read_only=True)


def test_open_sparql_graph_read_write() -> None:
    with pytest.raises(NotImplementedError, match="open_sparql_graph"):
        open_sparql_graph("http://example.invalid/sparql", read_only=False)


def test_open_sparql_graph_helpers() -> None:
    with pytest.raises(NotImplementedError):
        open_sparql_graph("http://example.invalid/sparql", read_only=True)


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_construct(mock_open: MagicMock) -> None:
    mock_open.return_value = _foaf_graph()
    people = load_sparql(
        Person,
        "http://example.org/sparql",
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s a foaf:Person . ?s ?p ?o . }",
    )
    assert len(people) == 2


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_select(mock_open: MagicMock) -> None:
    mock_open.return_value = _foaf_graph()
    rows = load_sparql(
        Person,
        "http://example.org/sparql",
        "SELECT ?s ?name WHERE { ?s a foaf:Person . ?s foaf:name ?name }",
        subject_var="s",
    )
    assert len(rows) == 2


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_ask_raises(mock_open: MagicMock) -> None:
    mock_open.return_value = MagicMock()
    with pytest.raises(TypeError, match="ASK"):
        load_sparql(Person, "http://example.org/sparql", "ASK { ?s a ?o }")


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_unknown_form(mock_open: MagicMock) -> None:
    mock_open.return_value = MagicMock()
    with pytest.raises(ValueError, match="Cannot load models"):
        load_sparql(
            Person,
            "http://example.org/sparql",
            "PREFIX x: <http://x/> INSERT {}",
            query_form="unknown",
        )


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_unsupported_query_object(mock_open: MagicMock) -> None:
    mock_open.return_value = MagicMock()
    with pytest.raises(ValueError, match="Cannot load models"):
        load_sparql(Person, "http://example.org/sparql", cast(Any, object()))


@patch("triplemodel.io.sparql.open_sparql_graph")
def test_load_sparql_classmethod(mock_open: MagicMock) -> None:
    mock_open.return_value = _foaf_graph()
    people = Person.load_sparql(
        "http://example.org/sparql",
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s a foaf:Person . ?s ?p ?o . }",
    )
    assert len(people) == 2


def test_select_models_subject_in_field_map():
    g = _foaf_graph()
    rows = select_models(
        Person,
        g,
        """
        SELECT ?s ?name WHERE {
          ?s a foaf:Person .
          ?s foaf:name ?name .
        }
        """,
        subject_var="s",
        field_map={"s": "slug", "name": "name"},
    )
    assert len(rows) == 2
    by_slug = {r.slug: r for r in rows}
    assert by_slug["alice"].name == "Alice"
    assert by_slug["alice"].subject_uri() == f"{EX}alice"
    assert by_slug["bob"].name == "Bob"


def test_select_models_optional_binding_missing():
    g = _foaf_graph()
    rows = select_models(
        Person,
        g,
        """
        SELECT ?slug ?name WHERE {
          BIND("alice" AS ?slug)
          BIND("Alice" AS ?name)
        }
        """,
        field_map={"slug": "slug", "name": "name", "age": "age"},
    )
    assert rows[0].name == "Alice"
    assert rows[0].age is None


def test_select_models_hydrate_skips_missing_and_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from triplemodel.store.sparql_result import Variable as V

    g = _foaf_graph()
    alice = NamedNode(f"{EX}alice")
    fake_result = MagicMock()
    fake_result.type = "SELECT"
    fake_result.__iter__ = MagicMock(
        return_value=iter(
            [
                {V("s"): alice},
                {V("s"): alice},
                {},
            ]
        )
    )
    monkeypatch.setattr(
        "triplemodel.io.sparql.run_sparql",
        lambda *args, **kwargs: fake_result,
    )
    people = select_models(
        Person,
        g,
        "SELECT ?s WHERE { ?s a foaf:Person }",
        subject_var="s",
        hydrate=True,
    )
    assert len(people) == 1


def test_load_sparql_prepared_query_select():
    pq = prepare_model_query(
        Person,
        """
        SELECT ?slug ?name WHERE {
          ?s a foaf:Person .
          ?s foaf:name ?name .
          BIND(REPLACE(STR(?s), "http://example.org/people/", "") AS ?slug)
        }
        """,
    )
    with patch("triplemodel.io.sparql.open_sparql_graph") as mock_open:
        mock_open.return_value = _foaf_graph()
        rows = load_sparql(Person, "http://example.org/sparql", pq.prepared)
    assert len(rows) == 2


def test_prepare_model_query_returns_string():
    pq = prepare_model_query(Person, "SELECT ?n WHERE { ?s foaf:name ?n }")
    assert isinstance(pq.prepared, str)
    assert detect_query_form(pq.prepared) == "select"


def test_init_bindings_filter_subject_uri():
    """Guide parity: id_field binds subject URI for FILTER(?s = ?subj)."""
    g = _foaf_graph()
    alice = Person(slug="alice", name="Alice", age=30)
    bindings = init_bindings_from_model(alice, {"subj": "slug"})
    assert ask(
        g,
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        ASK {
          ?s foaf:name "Alice" .
          FILTER(?s = ?subj)
        }
        """,
        initBindings=bindings,  # ty: ignore[invalid-argument-type]
    )


def test_union_member_term_conversion():
    class MaybeAge(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        val: str | int = rdf_field("foaf:age", default=0)

    class UnionTry(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Thing"
            id_field = "slug"

        slug: str
        val: int | float = rdf_field("foaf:age", default=0)

    g = Graph()
    g.add(
        (
            NamedNode(f"{EX}a"),
            NamedNode(f"{FOAF}age"),
            Literal("not-a-number"),
        )
    )
    rows = select_models(
        MaybeAge,
        g,
        """
        SELECT ?slug ?val WHERE {
          BIND("a" AS ?slug)
          BIND("not-a-number" AS ?val)
        }
        """,
    )
    assert rows[0].val == "not-a-number"

    g2 = Graph()
    rows2 = select_models(
        UnionTry,
        g2,
        'SELECT ?slug ?val WHERE { BIND("x" AS ?slug) BIND("3.5"^^<http://www.w3.org/2001/XMLSchema#decimal> AS ?val) }',
    )
    assert rows2[0].val == 3.5


def test_term_for_field_union_member_fallback() -> None:
    from datetime import date

    from triplemodel.io.sparql import _term_for_field

    class Mixed(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Thing"
            id_field = "slug"

        slug: str
        val: int | date = rdf_field("foaf:age", default=0)

    from triplemodel.terms.registry import default_registry

    field_info = Mixed.model_fields["val"]
    out = _term_for_field(
        Literal("not-a-valid-int-or-date"),
        field_info,
        registry=default_registry,
    )
    assert out == "not-a-valid-int-or-date"


def test_hydrate_wrong_result_type():
    g = _foaf_graph()
    with pytest.raises(TypeError, match="bindings"):
        select_models(
            Person,
            g,
            "ASK { ?s a foaf:Person }",
            subject_var="s",
            hydrate=True,
        )


def test_subject_uri_outside_namespace_uses_full_uri_as_slug():
    g = Graph()
    g.add(
        (
            NamedNode("http://other.example/alien"),
            NamedNode(RDF_TYPE),
            NamedNode(f"{FOAF}Person"),
        )
    )
    g.add(
        (
            NamedNode("http://other.example/alien"),
            NamedNode(f"{FOAF}name"),
            Literal("ET"),
        )
    )
    rows = select_models(
        Person,
        g,
        "SELECT ?s ?name WHERE { ?s foaf:name ?name }",
        subject_var="s",
        field_map={"name": "name"},
    )
    assert rows[0].slug == "http://other.example/alien"
