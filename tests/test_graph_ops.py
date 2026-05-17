"""Tests for graph helper utilities."""

from __future__ import annotations

from triplemodel import (
    TripleModel,
    graph_set,
    graph_value,
    merge_graphs,
    objects_for_field,
    rdf_field,
)

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)


def test_merge_graphs():
    a = Person(slug="a", name="A").to_graph()
    b = Person(slug="b", name="B").to_graph()
    merged = merge_graphs(a, b)
    assert len(merged) == len(a) + len(b)


def test_graph_value_and_set():
    p = Person(slug="a", name="A")
    g = p.to_graph()
    uri = p.subject_uri()
    assert graph_value(g, uri, f"{FOAF}name", Person, "name") == "A"
    graph_set(g, uri, f"{FOAF}name", "Alice")
    assert graph_value(g, uri, f"{FOAF}name", Person, "name") == "Alice"
    graph_set(g, uri, f"{FOAF}name", None)
    assert graph_value(g, uri, f"{FOAF}name", Person, "name") is None


def test_objects_for_field():
    p = Person(slug="a", name="A", nick=["x", "y"])
    g = p.to_graph()
    objs = objects_for_field(g, p.subject_uri(), Person, "nick")
    assert set(objs) == {"x", "y"}
