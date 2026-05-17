"""Tests for RdfModel round-trip serialization."""

from __future__ import annotations

from typing import Annotated

import pydantic
import pytest
from rdflib import BNode, Graph, Literal, URIRef

from rdfmodel import Predicate, RdfModel, models_to_graph, rdf_field
from rdfmodel._config import id_from_subject_uri

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


def test_id_extraction_rejects_prefix_collision():
    ns = "http://example.com"
    uri = "http://example.computer/alice"
    assert id_from_subject_uri(ns, uri) is None

    class LocalPerson(RdfModel):
        class Rdf:
            namespace = ns
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    g = Graph()
    g.add((URIRef(uri), URIRef(f"{FOAF}name"), Literal("Alice")))
    with pytest.raises(pydantic.ValidationError):
        LocalPerson.from_graph(g, uri)


def test_id_roundtrip_hash_namespace():
    class Hashed(RdfModel):
        class Rdf:
            namespace = "http://example.org/people#"
            type_uri = "http://example.org/Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    person = Hashed(slug="bob", name="Bob")
    uri = person.subject_uri()
    assert uri == "http://example.org/people#bob"
    restored = Hashed.from_graph(person.to_graph(), uri)
    assert restored == person


def test_subject_uri_encodes_special_chars():
    person = Person(slug="alice bob", name="Alice")
    uri = person.subject_uri()
    assert " " not in uri
    assert "%20" in uri
    restored = Person.from_graph(person.to_graph(), uri)
    assert restored.slug == "alice bob"


def test_from_graph_invalid_literal_raises():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}age"), Literal("not-a-number")))
    with pytest.raises(ValueError, match="field 'age'"):
        Person.from_graph(g, str(subj))


def test_bnode_object_rejected_for_str_field():
    class WithFriend(RdfModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        friend: str | None = rdf_field(f"{FOAF}knows", default=None)

    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}knows"), BNode()))
    with pytest.raises(ValueError, match="field 'friend'"):
        WithFriend.from_graph(g, str(subj))


def test_multi_valued_predicate_uses_first():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alicia")))
    person = Person.from_graph(g, str(subj))
    assert person.name == "Alice"


def test_union_type_roundtrip():
    class Mixed(RdfModel):
        class Rdf:
            namespace = EX
            type_uri = "http://example.org/Mixed"
            id_field = "slug"

        slug: str
        val: str | int = rdf_field("http://example.org/val")

    original = Mixed(slug="a", val=42)
    restored = Mixed.from_graph(original.to_graph(), original.subject_uri())
    assert restored.val == 42
    assert isinstance(restored.val, int)


def test_slug_whitespace_not_stripped():
    person = Person(slug="  alice  ", name="Alice")
    assert person.slug == "  alice  "
