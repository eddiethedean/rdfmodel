"""Additional coverage for remaining branches."""

from __future__ import annotations

from typing import Any, cast

import pytest
from rdflib import Graph, Literal, URIRef

from triplemodel import TripleModel, model_to_graph, rdf_field
from triplemodel.metadata.cardinality import is_triple_model_type
from triplemodel.io import graph_to_model, model_to_triples
from triplemodel.namespaces import expand_curie
from triplemodel.io.sync import sync_to_graph as sync_fn
from triplemodel.terms import python_to_term

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


def test_expand_curie_no_match_returns_input():
    assert expand_curie("notaCurie", {}) == "notaCurie"


def test_is_triple_model_type_raises_typeerror():
    class Meta(type):
        def __subclasscheck__(cls, sub):
            raise TypeError("nope")

    class Weird(metaclass=Meta):
        pass

    assert is_triple_model_type(Weird) is False


def test_is_triple_model_type_not_type():
    assert is_triple_model_type("x") is False


def test_python_to_term_mailto():
    from rdflib import URIRef

    assert isinstance(python_to_term("mailto:a@b.co"), URIRef)


def test_model_to_triples_skips_none_list_items():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        nick: list[str | None] = rdf_field(f"{FOAF}nick", default_factory=list)

    t = model_to_triples(P(slug="a", nick=["x", None]))
    assert len([x for x in t if FOAF in str(x[1])]) == 1


def test_graph_import_nested_typeerror():
    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            type_uri = "http://example.org/Box"
            id_field = "slug"

        slug: str = "b"
        v: str = rdf_field("http://example.org/v")

    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            embed = "iri"

        slug: str
        box: Box | None = rdf_field("http://example.org/box", default=None)

    g = Graph()
    subj = URIRef(EX + "p")
    g.add((subj, URIRef(f"{FOAF}Person"), URIRef(f"{FOAF}Person")))
    g.add((subj, URIRef("http://example.org/box"), Literal("not-a-node")))
    with pytest.raises(ValueError, match="Cannot import nested"):
        graph_to_model(g, P, str(subj), validate_type=False)


def test_sync_add_mode_explicit():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    p = P(slug="a", name="A")
    g = sync_fn(p, mode="add")
    assert len(g) >= 1


def test_export_nested_invalid_embed_raises():
    from triplemodel.embed import export_nested_triples

    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str = "b"

    with pytest.raises(ValueError, match="embed"):
        export_nested_triples(
            EX + "p",
            "http://example.org/h",
            Box(slug="b"),
            embed=cast(Any, "nope"),
        )


def test_model_to_graph_patch_mode():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        age: int | None = rdf_field(f"{FOAF}age", default=None)

    p = P(slug="a", name="A", age=1)
    g = p.to_graph()
    p2 = P(slug="a", name="A", age=None)
    model_to_graph(p2, g, mode="patch")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []
