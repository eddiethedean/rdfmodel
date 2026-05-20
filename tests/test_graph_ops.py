"""Tests for graph helper utilities."""

from __future__ import annotations

import pytest
from pyoxigraph import NamedNode
from triplemodel.store.terms import term_str

from triplemodel import (
    TripleModel,
    graph_set,
    graph_value,
    merge_graphs,
    objects_for_field,
    rdf_field,
)
from triplemodel.io.ops import graph_set_many

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
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


def test_graph_value_raises_without_predicate():
    class Bare(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        note: str = "x"

    p = Bare(slug="a")
    g = p.to_graph()
    with pytest.raises(ValueError, match="no RDF predicate"):
        graph_value(g, p.subject_uri(), "http://example.org/note", Bare, "note")


def test_graph_set_many():
    p = Person(slug="a", name="A")
    g = p.to_graph()
    subj = NamedNode(p.subject_uri())
    pred = f"{FOAF}nick"
    graph_set_many(g, subj, pred, ["x", "y"])
    nicks = sorted(term_str(o) for o in g.objects(subj, NamedNode(pred)))
    assert nicks == ["x", "y"]
