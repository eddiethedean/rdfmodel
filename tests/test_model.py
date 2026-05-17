"""Tests for RdfModel round-trip serialization."""

from __future__ import annotations

from typing import Annotated

import pytest
from rdflib import Graph

from rdfmodel import Predicate, RdfModel, graph_to_models, models_to_graph, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(RdfModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


class Document(RdfModel):
    class Rdf:
        namespace = "http://example.org/docs/"
        type_uri = "http://example.org/Document"
        id_field = "slug"

    slug: str
    title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]


def test_to_graph_and_back():
    alice = Person(slug="alice", name="Alice", age=30)
    g = alice.to_graph()

    restored = Person.from_graph(g, alice.subject_uri())
    assert restored == alice


def test_optional_field_omitted():
    bob = Person(slug="bob", name="Bob")
    triples = bob.to_triples()
    predicates = {p for _, p, _ in triples}
    assert f"{FOAF}age" not in predicates


def test_all_from_graph():
    people = [
        Person(slug="alice", name="Alice", age=30),
        Person(slug="bob", name="Bob"),
    ]
    g = models_to_graph(people)
    loaded = Person.all_from_graph(g)
    assert {p.slug for p in loaded} == {"alice", "bob"}


def test_annotated_predicate():
    doc = Document(slug="readme", title="README")
    g = doc.to_graph()
    restored = Document.from_graph(g, doc.subject_uri())
    assert restored.title == "README"


def test_subject_uri_requires_config():
    class Bare(RdfModel):
        label: str = rdf_field("http://example.org/label")

    with pytest.raises(ValueError, match="namespace"):
        Bare(label="x").subject_uri()


def test_explicit_uri_override():
    person = Person(slug="alice", name="Alice")
    uri = "http://custom.example/alice"
    triples = person.to_triples(uri=uri)
    assert all(s == uri for s, _, _ in triples)


def test_graph_to_models_requires_type():
    class Untyped(RdfModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    g = Graph()
    with pytest.raises(ValueError, match="type_uri"):
        Untyped.all_from_graph(g)
