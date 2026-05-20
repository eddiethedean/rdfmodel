"""Tests for graph build/parse helpers."""

from __future__ import annotations

from typing import Annotated

from pyoxigraph import BlankNode as BNode, Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import Predicate, TripleModel, models_to_graph, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io import graph_to_model, model_to_triples
from triplemodel.metadata import unwrap_annotation

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


def test_unmapped_field_omitted_from_triples():
    class WithExtra(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = module_type_uri("Person_2")
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


def test_unwrap_annotation_multi_member_union():
    assert unwrap_annotation(str | int) == (str | int)


def test_unwrap_annotation_single_optional():
    assert unwrap_annotation(int | None) is int


def test_unwrap_annotation_plain_type():
    assert unwrap_annotation(str) is str


def test_unwrap_annotation_non_union_generic():
    assert unwrap_annotation(list[str]) == list[str]


def test_unwrap_annotation_annotated_int():
    ann = Annotated[int, Predicate("http://example.org/age")]
    assert unwrap_annotation(ann) is int


def test_unwrap_annotation_annotated_optional_int():
    ann = Annotated[int | None, Predicate("http://example.org/age")]
    assert unwrap_annotation(ann) is int


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
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            NamedNode(PERSON_TYPE),
        )
    )
    assert Person.all_from_graph(g) == []


def test_graph_to_model_skips_unmapped_fields():
    class WithExtra(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = module_type_uri("Person_3")
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        mystery: str = ""

    g = Graph()
    subj = NamedNode(EX + "alice")
    extra_type = module_type_uri("Person_3")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(extra_type)))
    g.add((subj, NamedNode(f"{FOAF}name"), Literal("Alice")))
    m = graph_to_model(g, WithExtra, str(subj))
    assert m.name == "Alice"
    assert m.slug == "alice"
    assert m.mystery == ""


def test_all_from_graph_empty_when_no_mapped_predicates():
    class IdOnly(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            type_uri = ""

        slug: str

    g = Graph()
    assert IdOnly.all_from_graph(g) == []


def test_graph_to_model_accepts_uri_ref_subject():
    g = Person(slug="alice", name="Alice").to_graph()
    uri = NamedNode(EX + "alice")
    m = graph_to_model(g, Person, uri)
    assert m.slug == "alice"
    assert m.name == "Alice"


def test_all_from_graph_type_uri_override():
    class Worker(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = "http://example.org/Worker"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    g = Graph()
    subj = NamedNode(EX + "w1")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(PERSON_TYPE)))
    g.add((subj, NamedNode(f"{FOAF}name"), Literal("Pat")))
    loaded = Worker.all_from_graph(g, type_uri=PERSON_TYPE, validate_type=False)
    assert len(loaded) == 1
    assert loaded[0].slug == "w1"
    assert loaded[0].name == "Pat"
