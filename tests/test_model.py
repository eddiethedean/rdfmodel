"""Tests for TripleModel round-trip serialization."""

from __future__ import annotations

from typing import Annotated

import pytest
from rdflib import BNode, Graph, Literal, URIRef

from triplemodel import Predicate, TripleModel, models_to_graph, rdf_field
from triplemodel.config import RDF_TYPE, id_from_subject_uri

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


class Document(TripleModel):
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
    class Bare(TripleModel):
        label: str = rdf_field("http://example.org/label")

    with pytest.raises(ValueError, match="namespace"):
        Bare(label="x").subject_uri()


def test_explicit_uri_override():
    person = Person(slug="alice", name="Alice")
    uri = "http://custom.example/alice"
    triples = person.to_triples(uri=uri)
    assert all(s == uri for s, _, _ in triples)


def test_all_from_graph_without_type_uri_discovers_subjects():
    class Untyped(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            type_uri = ""

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    g = models_to_graph(
        [
            Untyped(slug="a", name="A"),
            Untyped(slug="b", name="B"),
        ]
    )
    loaded = Untyped.all_from_graph(g)
    assert {p.slug for p in loaded} == {"a", "b"}


def test_all_from_graph_ignores_inverse_predicate_subjects():
    EX_INV = "http://example.org/inv/"

    class Report(TripleModel):
        class Rdf:
            namespace = f"{EX_INV}report/"
            type_uri = ""
            id_field = "slug"

        slug: str
        author: str | None = rdf_field(
            f"{EX_INV}hasAuthor",
            inverse=f"{EX_INV}authored",
            default=None,
        )

    g = Graph()
    report_uri = URIRef(f"{EX_INV}report/r1")
    author_uri = URIRef(f"{EX_INV}person/alice")
    g.add((author_uri, URIRef(f"{EX_INV}authored"), report_uri))
    g.add((report_uri, URIRef(f"{EX_INV}hasAuthor"), author_uri))

    loaded = Report.all_from_graph(g)
    assert len(loaded) == 1
    assert loaded[0].slug == "r1"


def test_id_extraction_rejects_prefix_collision():
    ns = "http://example.com"
    uri = "http://example.computer/alice"
    assert id_from_subject_uri(ns, uri) is None

    class LocalPerson(TripleModel):
        class Rdf:
            namespace = ns
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    g = Graph()
    g.add((URIRef(uri), URIRef(f"{FOAF}name"), Literal("Alice")))
    with pytest.raises(ValueError, match="validate"):
        LocalPerson.from_graph(g, uri, validate_type=False)


def test_id_roundtrip_hash_namespace():
    class Hashed(TripleModel):
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
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}age"), Literal("not-a-number")))
    with pytest.raises(ValueError, match="field 'age'"):
        Person.from_graph(g, str(subj))


def test_bnode_object_rejected_for_str_field():
    class WithFriend(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        friend: str | None = rdf_field(f"{FOAF}knows", default=None)

    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}knows"), BNode()))
    with pytest.raises(ValueError, match="field 'friend'"):
        WithFriend.from_graph(g, str(subj))


def test_multi_valued_predicate_uses_first():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alicia")))
    with pytest.warns(UserWarning, match="Multiple objects"):
        person = Person.from_graph(g, str(subj), on_duplicate="warn")
    assert person.name == "Alice"


def test_union_type_roundtrip():
    class Mixed(TripleModel):
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


def test_subject_uri_override():
    person = Person(slug="alice", name="Alice")
    assert (
        person.subject_uri(uri="http://custom.example/alice")
        == "http://custom.example/alice"
    )


def test_rdf_config_classmethod():
    cfg = Person.rdf_config()
    assert cfg.namespace == EX
    assert cfg.type_uri == f"{FOAF}Person"
    assert cfg.id_field == "slug"


def test_inherited_rdf_config_roundtrip():
    class Base(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

    class Employee(Base):
        slug: str
        name: str = rdf_field(f"{FOAF}name")

    emp = Employee(slug="alice", name="Alice")
    restored = Employee.from_graph(emp.to_graph(), emp.subject_uri())
    assert restored == emp


def test_from_graph_rejects_wrong_rdf_type():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef("http://example.org/Document")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    with pytest.raises(ValueError, match="rdf:type"):
        Person.from_graph(g, str(subj))


def test_from_graph_validate_type_can_be_disabled():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    person = Person.from_graph(g, str(subj), validate_type=False)
    assert person.name == "Alice"


def test_from_graph_validation_error_includes_subject():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}age"), URIRef("http://example.org/not-an-int")))
    with pytest.raises(ValueError, match="Cannot validate Person"):
        Person.from_graph(g, str(subj))


def test_duplicate_predicate_on_error():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alicia")))
    with pytest.raises(ValueError, match="Multiple objects"):
        Person.from_graph(g, str(subj), on_duplicate="error")


def test_duplicate_predicate_ignore():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alicia")))
    person = Person.from_graph(g, str(subj), on_duplicate="ignore")
    assert person.name == "Alice"


class AnnotatedAgePerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: Annotated[int, Predicate(f"{FOAF}age")]


def test_annotated_int_roundtrip():
    person = AnnotatedAgePerson(slug="alice", name="Alice", age=30)
    restored = AnnotatedAgePerson.from_graph(person.to_graph(), person.subject_uri())
    assert restored == person
    assert isinstance(restored.age, int)


class Flagged(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    active: bool = rdf_field("http://example.org/active", default=False)
    count: int = rdf_field("http://example.org/count", default=0)


def test_false_and_zero_roundtrip():
    item = Flagged(slug="a", name="A", active=False, count=0)
    restored = Flagged.from_graph(item.to_graph(), item.subject_uri())
    assert restored.active is False
    assert restored.count == 0


class WithBio(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    bio: str = rdf_field(f"{FOAF}nick", default="")


def test_empty_string_field_roundtrip():
    person = WithBio(slug="a", name="A", bio="")
    triples = person.to_triples()
    assert any(obj == "" for _, _, obj in triples)
    restored = WithBio.from_graph(person.to_graph(), person.subject_uri())
    assert restored.bio == ""


def test_from_graph_missing_required_field():
    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    with pytest.raises(ValueError, match="Cannot validate Person"):
        Person.from_graph(g, str(subj))


def test_union_type_string_roundtrip():
    class Mixed(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = "http://example.org/Mixed"
            id_field = "slug"

        slug: str
        val: str | int = rdf_field("http://example.org/val")

    original = Mixed(slug="a", val="hello")
    restored = Mixed.from_graph(original.to_graph(), original.subject_uri())
    assert restored.val == "hello"
    assert isinstance(restored.val, str)


def test_off_namespace_uri_import_fails():
    person = Person(slug="alice", name="Alice")
    uri = "http://custom.example/alice"
    g = person.to_graph(uri=uri)
    with pytest.raises(ValueError, match="Cannot validate Person"):
        Person.from_graph(g, uri, validate_type=False)


def test_empty_child_rdf_shadows_parent():
    class Base(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

    class Child(Base):
        class Rdf:
            pass

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    with pytest.raises(ValueError, match="namespace"):
        Child(slug="a", name="A").subject_uri()


def test_validate_assignment_rejects_invalid_value():
    alice = Person(slug="alice", name="Alice")
    with pytest.raises(Exception):
        setattr(alice, "age", "not an int")
