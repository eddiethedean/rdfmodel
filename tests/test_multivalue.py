"""Tests for multi-valued list/set fields."""

from __future__ import annotations

import pytest

from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)
    tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)


def test_list_field_roundtrip():
    p = Person(slug="a", name="A", nick=["Al", "Alice"])
    restored = Person.from_graph(p.to_graph(), p.subject_uri())
    assert restored.nick == ["Al", "Alice"]


def test_set_field_roundtrip():
    p = Person(slug="a", name="A", tag={"x", "y"})
    restored = Person.from_graph(p.to_graph(), p.subject_uri())
    assert restored.tag == {"x", "y"}


def test_empty_list_omitted():
    p = Person(slug="a", name="A", nick=[])
    triples = p.to_triples()
    assert not any(f"{FOAF}nick" in pred for _, pred, _ in triples)


def test_set_skips_none_elements_on_export():
    p = Person.model_construct(slug="a", name="A", tag={"x", None, "y"})
    tag_triples = [t for t in p.to_triples() if t[1] == "http://example.org/tag"]
    assert len(tag_triples) == 2


def test_scalar_duplicate_still_warns():
    from rdflib import Graph, Literal, URIRef

    g = Graph()
    subj = URIRef(EX + "a")
    g.add(
        (
            subj,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{FOAF}Person"),
        )
    )
    g.add((subj, URIRef(f"{FOAF}name"), Literal("A")))
    g.add((subj, URIRef(f"{FOAF}name"), Literal("B")))
    with pytest.warns(UserWarning, match="Multiple objects"):
        Person.from_graph(g, str(subj), validate_type=False)
