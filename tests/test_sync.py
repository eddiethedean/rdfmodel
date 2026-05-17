"""Tests for sync_to_graph and graph modes."""

from __future__ import annotations

from rdflib import Graph, URIRef

from triplemodel import TripleModel, rdf_field, sync_to_graph

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


def test_replace_removes_cleared_age():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    sync_to_graph(p2, g, mode="replace")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []


def test_add_leaves_stale_triples():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    p2.sync_to_graph(g, mode="add")
    subj = URIRef(p.subject_uri())
    assert len(list(g.objects(subj, URIRef(f"{FOAF}age")))) == 1


def test_patch_clears_only_none_fields():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    sync_to_graph(p2, g, mode="patch")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []
    names = list(g.objects(subj, URIRef(f"{FOAF}name")))
    assert any(str(o) == "A" for o in names)


def test_instance_sync_to_graph():
    p = Person(slug="a", name="A", age=25)
    g = Graph()
    p.sync_to_graph(g, mode="replace")
    assert len(g) >= 2


def test_patch_clears_curie_predicate_empty_list():
    class CuriePerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            prefixes = {"foaf": FOAF}

        slug: str
        nick: list[str] = rdf_field("foaf:nick", default_factory=list)

    p = CuriePerson(slug="a", nick=["x"])
    g = p.to_graph()
    sync_to_graph(CuriePerson(slug="a", nick=[]), g, mode="patch")
    subj = URIRef(EX + "a")
    assert list(g.objects(subj, URIRef(f"{FOAF}nick"))) == []
