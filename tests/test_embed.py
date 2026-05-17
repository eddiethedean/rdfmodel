"""Tests for nested TripleModel embedding."""

from __future__ import annotations

from rdflib import URIRef

from triplemodel import TripleModel, rdf_field, sync_to_graph

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"
ADDRESS = "http://example.org/address"


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


def test_replace_updates_nested_child_owned_triples():
    mbox = Mailbox(slug="m1", address="alice@example.org")
    p = Person(slug="alice", name="Alice", mbox=mbox)
    g = p.to_graph()
    child = URIRef(mbox.subject_uri())
    assert len(list(g.objects(child, URIRef(ADDRESS)))) == 1

    updated = Person(
        slug="alice",
        name="Alice",
        mbox=Mailbox(slug="m1", address="bob@example.org"),
    )
    sync_to_graph(updated, g, mode="replace")
    addresses = [str(o) for o in g.objects(child, URIRef(ADDRESS))]
    assert addresses == ["bob@example.org"]
    restored = Person.from_graph(g, p.subject_uri())
    assert restored.mbox is not None
    assert restored.mbox.address == "bob@example.org"


def test_to_graph_replace_updates_nested_child_owned_triples():
    mbox = Mailbox(slug="m1", address="alice@example.org")
    p = Person(slug="alice", name="Alice", mbox=mbox)
    g = p.to_graph()
    child = URIRef(mbox.subject_uri())

    updated = Person(
        slug="alice",
        name="Alice",
        mbox=Mailbox(slug="m1", address="bob@example.org"),
    )
    updated.to_graph(g, mode="replace")
    addresses = [str(o) for o in g.objects(child, URIRef(ADDRESS))]
    assert addresses == ["bob@example.org"]


def test_clear_nested_iri_children_noop_for_bnode_embed():
    from triplemodel._config import get_rdf_config
    from triplemodel._sync import _clear_nested_iri_children

    mbox = Mailbox(slug="m1", address="bob@example.org")
    p = PersonBnode(slug="bob", mbox=mbox)
    g = p.to_graph()
    n_before = len(g)
    _clear_nested_iri_children(p, g, config=get_rdf_config(PersonBnode))
    assert len(g) == n_before


def test_clear_nested_iri_children_skips_unresolved_nested_cls():
    from unittest.mock import patch

    from triplemodel._config import get_rdf_config
    from triplemodel._sync import _clear_nested_iri_children

    mbox = Mailbox(slug="m1", address="alice@example.org")
    p = Person(slug="alice", name="Alice", mbox=mbox)
    g = p.to_graph()
    child = URIRef(mbox.subject_uri())
    assert len(list(g.objects(child, URIRef(ADDRESS)))) == 1
    cfg = get_rdf_config(Person)
    with patch(
        "triplemodel._cardinality.nested_model_type",
        return_value=None,
    ):
        _clear_nested_iri_children(p, g, config=cfg)
    assert len(list(g.objects(child, URIRef(ADDRESS)))) == 1


def test_nested_bnode_embed_roundtrip():
    mbox = Mailbox(slug="m1", address="bob@example.org")
    p = PersonBnode(slug="bob", mbox=mbox)
    g = p.to_graph()
    restored = PersonBnode.from_graph(g, p.subject_uri())
    assert restored.mbox is not None
    assert restored.mbox.address == "bob@example.org"
