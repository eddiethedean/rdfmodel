"""Tests for field cardinality helpers."""

from __future__ import annotations

from typing import Annotated

import pytest
from rdflib import Graph, URIRef

from triplemodel import Predicate, TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.metadata.cardinality import (
    _safe_issubclass,
    element_type,
    field_cardinality,
    is_triple_model_type,
    nested_model_type,
    raise_if_nested_collection,
    scalar_python_type,
    unwrap_annotation,
)
from triplemodel.fields import owned_predicates

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Child(TripleModel):
    class Rdf:
        namespace = "http://example.org/child/"
        type_uri = "http://example.org/Child"
        id_field = "slug"

    slug: str
    label: str = rdf_field("http://example.org/label")


class Parent(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF}

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    tags: set[str] = rdf_field("http://example.org/tag", default_factory=set)
    child: Child | None = None
    score: int | None = rdf_field("http://example.org/score", default=None)


def test_unwrap_annotation_optional_and_annotated():
    assert unwrap_annotation(int | None) is int
    ann = Annotated[str, Predicate("http://example.org/p")]
    assert unwrap_annotation(ann) is str


def test_element_type_list():
    assert element_type(list[str]) is str


def test_field_cardinality_matrix():
    assert field_cardinality(Parent.model_fields["name"]) == "scalar"
    assert field_cardinality(Parent.model_fields["nick"]) == "list"
    assert field_cardinality(Parent.model_fields["tags"]) == "set"
    assert field_cardinality(Parent.model_fields["child"]) == "nested"


def test_scalar_python_type_and_nested():
    assert scalar_python_type(Parent.model_fields["name"]) is str
    assert scalar_python_type(Parent.model_fields["nick"]) is str
    assert nested_model_type(Parent.model_fields["child"]) is Child


def test_is_triple_model_type():
    assert is_triple_model_type(Child) is True
    assert is_triple_model_type(str) is False
    assert is_triple_model_type("not a type") is False


def test_is_triple_model_type_typeerror_on_subclasscheck():
    class Meta(type):
        def __subclasscheck__(cls, sub):
            raise TypeError("subclass check failed")

    class Broken(metaclass=Meta):
        pass

    assert is_triple_model_type(Broken) is False
    assert _safe_issubclass(Broken, Child) is False


def test_owned_predicates_includes_type_and_curie():
    preds = owned_predicates(Parent)
    assert RDF_TYPE in preds
    assert "foaf:name" in preds or f"{FOAF}name" in preds
    assert f"{FOAF}nick" in preds


def test_list_of_triple_model_raises_on_export():
    class Team(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        members: list[Child] = rdf_field(
            "http://example.org/member", default_factory=list
        )

    with pytest.raises(ValueError, match="not supported"):
        Team(slug="t", members=[Child(slug="c", label="x")]).to_graph()


def test_list_of_triple_model_raises_on_import():
    from triplemodel.io import graph_to_model

    class Team(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        members: list[Child] = rdf_field(
            "http://example.org/member", default_factory=list
        )

    g = Graph()
    subj = URIRef(EX + "t")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF}Person")))
    with pytest.raises(ValueError, match="not supported"):
        graph_to_model(g, Team, str(subj))


def test_set_of_triple_model_raises_on_export():
    class Team(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        members: set[Child] = rdf_field(
            "http://example.org/member", default_factory=set
        )

    with pytest.raises(ValueError, match="not supported"):
        raise_if_nested_collection(Team.model_fields["members"])


def test_owned_predicates_unknown_curie_raises_on_resolve():
    class Bad(TripleModel):
        class Rdf:
            namespace = EX
            prefixes = {"ex": EX}

        slug: str
        x: str = rdf_field("unknown:prop")

    with pytest.raises(ValueError, match="Unknown prefix"):
        owned_predicates(Bad)
