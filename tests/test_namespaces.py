"""Tests for namespaces and CURIE expansion."""

from __future__ import annotations

import pytest
from rdflib import Graph

from triplemodel import TripleModel, bind_namespaces, expand_curie, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


def test_expand_curie():
    prefixes = {"foaf": FOAF}
    assert expand_curie("foaf:name", prefixes) == f"{FOAF}name"
    assert expand_curie(FOAF + "name", prefixes) == f"{FOAF}name"


def test_expand_curie_unknown_prefix():
    with pytest.raises(ValueError, match="Unknown prefix"):
        expand_curie("foo:bar", {})


def test_bind_namespaces_and_turtle_prefix():
    class Person(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            prefixes = {"foaf": FOAF}

        slug: str
        name: str = rdf_field("foaf:name")

    p = Person(slug="a", name="A")
    g = p.to_graph()
    ttl = g.serialize(format="turtle")
    assert "foaf:" in ttl or "PREFIX foaf:" in ttl


def test_bind_namespaces_strategies():
    g = Graph()
    bind_namespaces(g, {"ex": EX}, strategy="none")
    bind_namespaces(g, {"foaf": FOAF}, strategy="core")
    bind_namespaces(g, {}, strategy="rdflib")


def test_rdf_prefixes_as_list_of_tuples_roundtrip():
    class Person(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            prefixes = [("foaf", FOAF)]

        slug: str
        name: str = rdf_field("foaf:name")

    p = Person(slug="a", name="A")
    restored = Person.from_graph(p.to_graph(), p.subject_uri())
    assert restored == p
