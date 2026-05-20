"""Tests for graph and model comparison helpers."""

from __future__ import annotations

from pyoxigraph import BlankNode as BNode, Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import (
    TripleModel,
    graph_diff,
    graphs_equal,
    model_diff,
    rdf_field,
    sync_to_graph,
)
from triplemodel.vocab import FOAF

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF_PERSON = PERSON_TYPE
FOAF_NAME = f"{FOAF}name"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
        id_field = "slug"

    slug: str
    name: str = rdf_field(FOAF_NAME)


def test_graphs_equal_isomorphic():
    g1 = Graph()
    g2 = Graph()
    alice = NamedNode(f"{EX}alice")
    for g in (g1, g2):
        g.add((alice, NamedNode(f"{FOAF}type"), NamedNode(PERSON_TYPE)))
        g.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    assert graphs_equal(g1, g2)


def test_graphs_equal_same_bnode_id():
    g1 = Graph()
    g2 = Graph()
    b = BNode("shared")
    g1.add((b, NamedNode(FOAF_NAME), Literal("A")))
    g2.add((b, NamedNode(FOAF_NAME), Literal("A")))
    assert graphs_equal(g1, g2)


def test_graph_diff_delta():
    g1 = Graph()
    g2 = Graph()
    alice = NamedNode(f"{EX}alice")
    g1.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    g2.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    g2.add((alice, NamedNode(f"{FOAF}age"), Literal(30)))
    diff = graph_diff(g1, g2)
    assert not diff.equal
    assert len(diff.only_in_first) == 0
    assert len(diff.only_in_second) == 1


def test_model_diff_fields():
    a = Person(slug="alice", name="Alice")
    b = Person(slug="alice", name="Alicia")
    changes = model_diff(a, b)
    assert changes["fields"]["name"] == ("Alice", "Alicia")


def test_model_diff_with_graph():
    a = Person(slug="alice", name="Alice")
    b = Person(slug="alice", name="Bob")
    g = Graph()
    changes = model_diff(a, b, g)
    assert "fields" in changes
    assert "graph" in changes


def test_model_diff_type_mismatch():
    class Other(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = module_type_uri("Person_2")
            id_field = "slug"

        slug: str

    import pytest

    with pytest.raises(TypeError, match="same class"):
        model_diff(Person(slug="a", name="A"), Other(slug="a"))


def test_sync_then_graphs_equal():
    g = Graph()
    p = Person(slug="alice", name="Alice")
    sync_to_graph(p, g, mode="replace")
    restored = Person.from_graph(g, p.subject_uri())
    assert graphs_equal(p.to_graph(), restored.to_graph())
