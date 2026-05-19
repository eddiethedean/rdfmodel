"""Tests for CBD helpers."""

from __future__ import annotations

from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, cbd_graph, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF

FOAF_PERSON = f"{FOAF}Person"
FOAF_NAME = f"{FOAF}name"
FOAF_KNOWS = f"{FOAF}knows"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = FOAF_PERSON
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


def test_cbd_graph_includes_related_triples():
    g = Graph()
    alice = NamedNode(f"{EX}alice")
    bob = NamedNode(f"{EX}bob")
    g.add((alice, NamedNode(RDF_TYPE), NamedNode(FOAF_PERSON)))
    g.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    g.add((alice, NamedNode(FOAF_KNOWS), bob))
    g.add((bob, NamedNode(FOAF_NAME), Literal("Bob")))
    sub = cbd_graph(g, alice)
    assert (alice, NamedNode(FOAF_KNOWS), bob) in sub


def test_cbd_model_classmethod():
    g = Graph()
    alice = NamedNode(f"{EX}alice")
    g.add((alice, NamedNode(RDF_TYPE), NamedNode(FOAF_PERSON)))
    g.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    p = Person.cbd(g, alice)
    assert p.name == "Alice"
