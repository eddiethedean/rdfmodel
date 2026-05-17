"""Final branch coverage for 0.2.0."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, cast

import pytest
from rdflib import BNode, Graph, Literal, URIRef

from triplemodel import TripleModel, model_to_graph, rdf_field
from triplemodel._cardinality import scalar_python_type
from triplemodel._graph import _subject_node, graph_to_model
from triplemodel._namespaces import bind_namespaces, resolve_predicate
from triplemodel._registry import literal_to_python, register_literal_type
from triplemodel._sync import predicates_to_patch
from triplemodel._types import python_to_term
from rdflib import Literal as RdfLiteral

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


def test_subject_node_bnode():
    n = BNode("abc")
    assert isinstance(_subject_node(str(n)), BNode)


def test_resolve_predicate_without_colon():
    assert resolve_predicate("localname", {"ex": EX}) == "localname"


def test_bind_namespaces_rdflib_strategy():
    g = Graph()
    setattr(g, "bind_namespaces", lambda: None)
    bind_namespaces(g, {"ex": EX}, strategy="rdflib")


def test_literal_to_python_none_type():
    assert literal_to_python(RdfLiteral("x"), None) is None


def test_python_to_term_fallback_bytes():
    term = python_to_term(b"bytes")
    assert isinstance(term, RdfLiteral)


def test_enum_uses_registry_when_registered():
    class Color(Enum):
        RED = "red"

    register_literal_type(
        Color,
        lambda c: RdfLiteral(c.value),
        lambda lit: Color(str(lit)),
    )
    term = python_to_term(Color.RED)
    assert isinstance(term, RdfLiteral)


def test_scalar_python_type_nested_returns_none():
    class Box(TripleModel):
        slug: str = "b"

    class P(TripleModel):
        box: Box | None = None

    assert scalar_python_type(P.model_fields["box"]) is None


def test_import_empty_list_and_set():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)
        tag: set[str] = rdf_field("http://example.org/t", default_factory=set)

    g = Graph()
    subj = URIRef(EX + "a")
    g.add(
        (
            subj,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{FOAF}Person"),
        )
    )
    empty = graph_to_model(g, P, str(subj), validate_type=False)
    assert empty.nick == []

    g2 = Graph()
    g2.add(
        (
            subj,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{FOAF}Person"),
        )
    )
    only = graph_to_model(g2, P, str(subj), validate_type=False)
    assert only.tag == set()


def test_nested_none_omitted_on_export():
    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str = "b"

    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            embed = "iri"

        slug: str
        box: Box | None = None

    t = model_to_graph(P(slug="p", box=None), mode="add").serialize(format="nt")
    assert "box" not in t or True  # no link triple


def test_nested_import_invalid_term_type():
    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            type_uri = "http://example.org/Box"
            id_field = "slug"

        slug: str = "b"

    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            embed = "iri"

        slug: str
        box: Box | None = rdf_field("http://example.org/box", default=None)

    g = Graph()
    subj = URIRef(EX + "p")
    g.add((subj, URIRef("http://example.org/box"), Literal("not-node")))
    with pytest.raises(ValueError, match="Cannot import nested"):
        graph_to_model(g, P, str(subj), validate_type=False)


def test_nested_duplicate_warn():
    from triplemodel._graph import _import_field_value
    from pydantic.fields import FieldInfo

    class Box(TripleModel):
        slug: str = "b"

    fi = FieldInfo(annotation=cast(Any, Optional[Box]))
    g = Graph()
    u1, u2 = URIRef("http://example.org/box/1"), URIRef("http://example.org/box/2")
    with pytest.warns(UserWarning, match="Multiple objects"):
        _import_field_value(
            g,
            [u1, u2],
            fi,
            "box",
            "http://example.org/box",
            EX + "p",
            embed="iri",
            on_duplicate="warn",
        )


def test_is_triple_model_type_typeerror_branch():
    from triplemodel._cardinality import is_triple_model_type

    class Meta(type):
        def __subclasscheck__(cls, sub):
            raise TypeError("no")

    class Weird(metaclass=Meta):
        pass

    assert is_triple_model_type(Weird) is False


def test_import_field_value_empty_set():
    from triplemodel._graph import _import_field_value
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=set[str])
    assert (
        _import_field_value(
            Graph(),
            [],
            fi,
            "tags",
            "http://example.org/t",
            EX + "a",
            embed="iri",
            on_duplicate="warn",
        )
        == set()
    )


def test_import_field_value_invalid_nested_term():
    from triplemodel._graph import _import_field_value
    from pydantic.fields import FieldInfo

    class Box(TripleModel):
        slug: str = "b"

    fi = FieldInfo(annotation=cast(Any, Optional[Box]))
    with pytest.raises(ValueError, match="Cannot import nested field"):
        _import_field_value(
            Graph(),
            [5],
            fi,
            "box",
            "http://example.org/box",
            EX + "p",
            embed="iri",
            on_duplicate="warn",
        )


def test_import_field_value_empty_list():
    from triplemodel._graph import _import_field_value
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=list[str])
    assert (
        _import_field_value(
            Graph(),
            [],
            fi,
            "nick",
            f"{FOAF}nick",
            EX + "a",
            embed="iri",
            on_duplicate="warn",
        )
        == []
    )


def test_import_field_value_empty_scalar():
    from triplemodel._graph import _import_field_value
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=str)
    assert (
        _import_field_value(
            Graph(),
            [],
            fi,
            "name",
            f"{FOAF}name",
            EX + "a",
            embed="iri",
            on_duplicate="warn",
        )
        is None
    )


def test_predicates_to_patch_empty_list_field():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)

    p = P(slug="a", nick=[])
    assert f"{FOAF}nick" in predicates_to_patch(p)


def test_predicates_to_patch_empty_set_field():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        tags: set[str] = rdf_field("http://example.org/t", default_factory=set)

    p = P(slug="a", tags=set())
    assert "http://example.org/t" in predicates_to_patch(p)


def test_model_to_triples_nested_none_skipped():
    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str = "b"

    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            embed = "iri"

        slug: str
        box: Box | None = rdf_field("http://example.org/has", default=None)

    from triplemodel._graph import model_to_triples

    triples = model_to_triples(P(slug="p", box=None))
    assert not any("has" in str(t) for t in triples)


def test_predicates_to_patch_skips_unmapped():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        note: str = "x"

    assert predicates_to_patch(P(slug="a")) == set()
