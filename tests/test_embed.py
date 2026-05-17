"""Tests for nested TripleModel embedding."""

from __future__ import annotations

from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field("http://example.org/address")


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "iri"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)


def test_nested_iri_embed_roundtrip():
    mbox = Mailbox(slug="m1", address="alice@example.org")
    p = Person(slug="alice", name="Alice", mbox=mbox)
    g = p.to_graph()
    restored = Person.from_graph(g, p.subject_uri())
    assert restored.mbox is not None
    assert restored.mbox.address == "alice@example.org"


class PersonBnode(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "bnode"

    slug: str
    mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)


def test_nested_bnode_embed_roundtrip():
    mbox = Mailbox(slug="m1", address="bob@example.org")
    p = PersonBnode(slug="bob", mbox=mbox)
    g = p.to_graph()
    restored = PersonBnode.from_graph(g, p.subject_uri())
    assert restored.mbox is not None
    assert restored.mbox.address == "bob@example.org"
