"""Tests for graph build/parse helpers."""

from __future__ import annotations

from rdflib import BNode, Graph, Literal, URIRef

from rdfmodel import RDFModel, models_to_graph, rdf_field
from rdfmodel._graph import _unwrap_optional, graph_to_model, model_to_triples

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(RDFModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


def test_unmapped_field_omitted_from_triples():
    class WithExtra(RDFModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        mystery: str = "hidden"

    p = WithExtra(slug="a", name="A", mystery="x")
    preds = {pred for _, pred, _ in model_to_triples(p)}
    assert all("mystery" not in pred for pred in preds)


def test_null_field_omitted_from_triples():
    p = Person(slug="a", name="A", age=None)
    preds = {pred for _, pred, _ in p.to_triples()}
    assert f"{FOAF}age" not in preds


def test_unwrap_optional_multi_member_union():
    assert _unwrap_optional(str | int) == (str | int)


def test_unwrap_optional_single_optional():
    assert _unwrap_optional(int | None) is int


def test_unwrap_optional_plain_type():
    assert _unwrap_optional(str) is str


def test_unwrap_optional_non_union_generic():
    assert _unwrap_optional(list[str]) == list[str]


def test_models_to_graph_into_existing_graph():
    g = Graph()
    people = [Person(slug="alice", name="Alice")]
    result = models_to_graph(people, g)
    assert result is g
    assert len(g) == 2


def test_graph_to_models_skips_bnode_subjects():
    g = Graph()
    bnode = BNode()
    g.add(
        (
            bnode,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{FOAF}Person"),
        )
    )
    assert Person.all_from_graph(g) == []


def test_graph_to_model_skips_unmapped_fields():
    class WithExtra(RDFModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        mystery: str = ""

    g = Graph()
    subj = URIRef(EX + "alice")
    g.add((subj, URIRef(f"{FOAF}name"), Literal("Alice")))
    m = graph_to_model(g, WithExtra, str(subj))
    assert m.name == "Alice"
    assert m.slug == "alice"
    assert m.mystery == ""
