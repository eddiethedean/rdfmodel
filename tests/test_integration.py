"""End-to-end and regression tests for triplemodel 0.2.x behaviour."""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Annotated

import pytest
from rdflib import Graph, Literal, URIRef

from triplemodel import (
    IriId,
    Predicate,
    TripleModel,
    graph_value,
    merge_graphs,
    models_to_graph,
    rdf_field,
    sync_to_graph,
)
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"
ANNOTATION = "http://example.org/annotation"


class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field("http://example.org/address")


class Person(TripleModel):
    """FOAF-style model used across integration scenarios."""

    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}
        embed = "iri"

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    mbox: Mailbox | None = rdf_field("foaf:mbox", default=None)
    age: int | None = rdf_field("foaf:age", default=None)


class PricedItem(TripleModel):
    class Rdf:
        namespace = "http://example.org/items/"
        type_uri = "http://example.org/Item"
        id_field = "sku"

    sku: str
    label: str = rdf_field("http://example.org/label")
    price: Decimal = rdf_field("http://example.org/price")


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Member(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"

    slug: str
    status: Status = rdf_field("http://example.org/status")


class ExternalResource(TripleModel):
    """Subject IRI is stored verbatim on the id field (``IriId`` metadata)."""

    class Rdf:
        namespace = EX
        type_uri = "http://example.org/External"
        id_field = "uri"

    uri: Annotated[str, IriId()]
    title: str = rdf_field("http://example.org/title")


# --- 0.2 exit criteria (mirrors examples/foaf_person_02.py) ---


def test_foaf_exit_criteria_roundtrip_and_sync_clear_age():
    alice = Person(
        slug="alice",
        name="Alice",
        nick=["Al", "Alice"],
        mbox=Mailbox(address="alice@example.org"),
        age=30,
    )
    g = alice.to_graph()
    ttl = g.serialize(format="turtle")
    assert "foaf:" in ttl or "PREFIX foaf:" in ttl

    restored = Person.from_graph(g, alice.subject_uri())
    assert restored == alice
    assert restored.mbox is not None
    assert restored.mbox.address == "alice@example.org"

    alice.age = None
    sync_to_graph(alice, g, mode="replace")
    subj = URIRef(alice.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF_NS}age"))) == []


def test_foaf_person_02_example_script():
    root = Path(__file__).resolve().parents[1]
    env = {**__import__("os").environ, "PYTHONPATH": str(root / "src")}
    result = subprocess.run(
        [sys.executable, str(root / "examples" / "foaf_person_02.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "0.2.0 FOAF example OK" in result.stdout


# --- Multi-value ---


def test_list_order_preserved_through_graph_roundtrip():
    p = Person(slug="a", name="A", nick=["first", "second", "third"])
    restored = Person.from_graph(p.to_graph(), p.subject_uri())
    assert restored.nick == ["first", "second", "third"]


def test_list_skips_none_elements_on_export():
    p = Person.model_construct(slug="a", name="A", nick=["ok", None, "also"])
    nick_triples = [t for t in p.to_triples() if t[1] == f"{FOAF_NS}nick"]
    assert len(nick_triples) == 2


def test_set_import_dedupes_duplicate_objects():
    class Tagged(Person):
        tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)

    g = Graph()
    subj = URIRef(EX + "a")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF_NS}Person")))
    g.add((subj, URIRef("http://example.org/tag"), Literal("x")))
    g.add((subj, URIRef("http://example.org/tag"), Literal("x")))
    g.add((subj, URIRef(f"{FOAF_NS}name"), Literal("A")))
    restored = Tagged.from_graph(g, str(subj), validate_type=False)
    assert restored.tag == {"x"}


def test_scalar_duplicate_raises_when_configured():
    g = Graph()
    subj = URIRef(EX + "a")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF_NS}Person")))
    g.add((subj, URIRef(f"{FOAF_NS}name"), Literal("A")))
    g.add((subj, URIRef(f"{FOAF_NS}name"), Literal("B")))
    with pytest.raises(ValueError, match="Multiple objects"):
        Person.from_graph(g, str(subj), validate_type=False, on_duplicate="error")


# --- Sync modes ---


def test_replace_updates_scalar_and_removes_old_value():
    p = Person(slug="a", name="Alice", age=30)
    g = p.to_graph()
    updated = Person(slug="a", name="Alicia", age=30)
    sync_to_graph(updated, g, mode="replace")
    subj = URIRef(p.subject_uri())
    names = [str(o) for o in g.objects(subj, URIRef(f"{FOAF_NS}name"))]
    assert names == ["Alicia"]


def test_patch_empty_list_clears_nick_only():
    p = Person(slug="a", name="A", nick=["x"], age=20)
    g = p.to_graph()
    cleared = Person(slug="a", name="A", nick=[], age=20)
    sync_to_graph(cleared, g, mode="patch")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF_NS}nick"))) == []
    assert any(str(o) == "A" for o in g.objects(subj, URIRef(f"{FOAF_NS}name")))


def test_replace_preserves_unowned_triples_on_subject():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    subj = URIRef(p.subject_uri())
    note = Literal("external note")
    g.add((subj, URIRef(ANNOTATION), note))
    sync_to_graph(Person(slug="a", name="Renamed", age=None), g, mode="replace")
    assert (subj, URIRef(ANNOTATION), note) in g
    assert list(g.objects(subj, URIRef(f"{FOAF_NS}age"))) == []


def test_to_graph_replace_mode_matches_sync_replace():
    p = Person(slug="a", name="A", age=25)
    g = p.to_graph()
    p.age = None
    p.to_graph(g, mode="replace")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF_NS}age"))) == []


def test_replace_clears_nested_mbox_link_on_parent():
    mbox = Mailbox(slug="m1", address="a@example.org")
    p = Person(slug="a", name="A", mbox=mbox)
    g = p.to_graph()
    child_uri = mbox.subject_uri()
    assert len(list(g.triples((URIRef(child_uri), None, None)))) >= 1
    sync_to_graph(Person(slug="a", name="A", mbox=None), g, mode="replace")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF_NS}mbox"))) == []
    assert list(g.triples((URIRef(child_uri), None, None))) == []
    restored = Person.from_graph(g, p.subject_uri())
    assert restored.mbox is None


def test_shared_graph_two_subjects_independent_sync():
    alice = Person(slug="alice", name="Alice", age=30)
    bob = Person(slug="bob", name="Bob", age=40)
    g = models_to_graph([alice, bob])
    bob.age = None
    sync_to_graph(bob, g, mode="replace")
    alice_subj = URIRef(alice.subject_uri())
    bob_subj = URIRef(bob.subject_uri())
    assert len(list(g.objects(alice_subj, URIRef(f"{FOAF_NS}age")))) == 1
    assert list(g.objects(bob_subj, URIRef(f"{FOAF_NS}age"))) == []


# --- Nested embed + batch load ---


def test_two_people_distinct_nested_mailboxes_in_one_graph():
    people = [
        Person(
            slug="alice",
            name="Alice",
            mbox=Mailbox(slug="ma", address="alice@example.org"),
        ),
        Person(
            slug="bob",
            name="Bob",
            mbox=Mailbox(slug="mb", address="bob@example.org"),
        ),
    ]
    g = models_to_graph(people)
    loaded = {p.slug: p for p in Person.all_from_graph(g)}
    assert loaded["alice"].mbox is not None
    assert loaded["bob"].mbox is not None
    assert loaded["alice"].mbox.address == "alice@example.org"
    assert loaded["bob"].mbox.address == "bob@example.org"
    assert loaded["alice"].mbox.subject_uri() != loaded["bob"].mbox.subject_uri()


# --- Registry + Annotated predicates in full models ---


def test_decimal_field_model_roundtrip():
    item = PricedItem(sku="1", label="Widget", price=Decimal("19.99"))
    restored = PricedItem.from_graph(item.to_graph(), item.subject_uri())
    assert restored.price == Decimal("19.99")


def test_enum_field_model_roundtrip():
    m = Member(slug="x", status=Status.ACTIVE)
    restored = Member.from_graph(m.to_graph(), m.subject_uri())
    assert restored.status is Status.ACTIVE


class Document(TripleModel):
    class Rdf:
        namespace = "http://example.org/docs/"
        type_uri = "http://example.org/Document"
        id_field = "slug"

    slug: str
    title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]


def test_annotated_predicate_in_combined_workflow():
    doc = Document(slug="d1", title="Report")
    g = doc.to_graph()
    assert (
        graph_value(
            g, doc.subject_uri(), "http://purl.org/dc/terms/title", Document, "title"
        )
        == "Report"
    )
    assert Document.from_graph(g, doc.subject_uri()).title == "Report"


# --- Subject IRI + graph helpers ---


def test_slug_as_full_iri_without_iri_id_metadata():
    """Export works when slug holds a full IRI; import needs ``IriId`` on the id field."""
    iri = "https://example.org/resources/99"
    g = Person(slug=iri, name="X").to_graph()
    with pytest.raises(ValueError, match="validate"):
        Person.from_graph(g, iri, validate_type=False)


def test_explicit_full_iri_id_field_as_subject():
    uri = "https://example.org/resources/42"
    res = ExternalResource(uri=uri, title="Hello")
    assert res.subject_uri() == uri
    g = res.to_graph()
    restored = ExternalResource.from_graph(g, uri)
    assert restored == res


def test_merge_graphs_then_all_from_graph():
    g1 = Person(slug="a", name="A").to_graph()
    g2 = Person(slug="b", name="B").to_graph()
    merged = merge_graphs(g1, g2)
    slugs = {p.slug for p in Person.all_from_graph(merged)}
    assert slugs == {"a", "b"}


def test_sync_to_graph_on_empty_graph_binds_prefixes():
    p = Person(slug="a", name="A")
    g = sync_to_graph(p, None, mode="replace")
    ttl = g.serialize(format="turtle")
    assert "foaf:" in ttl or "PREFIX foaf:" in ttl
