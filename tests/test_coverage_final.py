"""Final branch coverage for 0.2.0."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, cast

import pytest
from pyoxigraph import BlankNode as BNode, Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, model_to_graph, rdf_field
from triplemodel.metadata.cardinality import scalar_python_type
from triplemodel.io import graph_to_model, model_to_triples, import_field_value
from triplemodel.terms.iri import subject_node
from triplemodel.namespaces import bind_namespaces, resolve_predicate
from triplemodel.terms import literal_to_python, register_literal_type
from triplemodel.io.sync import predicates_to_patch
from triplemodel.terms import python_to_term

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


def testsubject_node_bnode():
    n = BNode("abc")
    assert isinstance(subject_node(str(n)), BNode)


def test_resolve_predicate_without_colon():
    assert resolve_predicate("localname", {"ex": EX}) == "localname"


def test_bind_namespaces_core_strategy():
    g = Graph()
    bind_namespaces(g, {"ex": EX}, strategy="core")
    assert ("ex", EX) in list(g.namespaces())


def test_literal_to_python_none_type():
    assert literal_to_python(Literal("x"), None) is None


def test_python_to_term_fallback_bytes():
    term = python_to_term(cast(Any, b"bytes"))
    assert isinstance(term, Literal)
    assert str(term.value) == "bytes"


def test_enum_uses_registry_when_registered():
    class Color(Enum):
        RED = "red"

    register_literal_type(
        Color,
        lambda c: Literal(c.value),
        lambda lit: Color(str(lit)),
    )
    term = python_to_term(Color.RED)
    assert isinstance(term, Literal)


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
            type_uri = PERSON_TYPE
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)
        tag: set[str] = rdf_field("http://example.org/t", default_factory=set)

    g = Graph()
    subj = NamedNode(EX + "a")
    g.add(
        (
            subj,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            NamedNode(PERSON_TYPE),
        )
    )
    empty = graph_to_model(g, P, str(subj), validate_type=False)
    assert empty.nick == []

    g2 = Graph()
    g2.add(
        (
            subj,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            NamedNode(PERSON_TYPE),
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

    g = model_to_graph(P(slug="p", box=None), mode="add")
    preds = {str(p) for _, p, _ in g}
    assert not any("box" in p for p in preds)
    assert len(list(model_to_triples(P(slug="p", box=None)))) == 0


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
    subj = NamedNode(EX + "p")
    g.add((subj, NamedNode("http://example.org/box"), Literal("not-node")))
    with pytest.raises(ValueError, match="Cannot import nested"):
        graph_to_model(g, P, str(subj), validate_type=False)


def test_nested_duplicate_warn():
    from pydantic.fields import FieldInfo

    class Box(TripleModel):
        slug: str = "b"

    fi = FieldInfo(annotation=cast(Any, Optional[Box]))
    g = Graph()
    u1, u2 = (
        NamedNode("http://example.org/box/1"),
        NamedNode("http://example.org/box/2"),
    )
    with pytest.warns(UserWarning, match="Multiple objects"):
        import_field_value(
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
    from triplemodel.metadata.cardinality import is_triple_model_type

    class Meta(type):
        def __subclasscheck__(cls, sub):
            raise TypeError("no")

    class Weird(metaclass=Meta):
        pass

    assert is_triple_model_type(Weird) is False


def testimport_field_value_empty_set():
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=set[str])
    assert (
        import_field_value(
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


def testimport_field_value_invalid_nested_term():
    from pydantic.fields import FieldInfo

    class Box(TripleModel):
        slug: str = "b"

    fi = FieldInfo(annotation=cast(Any, Optional[Box]))
    with pytest.raises(ValueError, match="Cannot import nested field"):
        import_field_value(
            Graph(),
            cast(Any, [5]),
            fi,
            "box",
            "http://example.org/box",
            EX + "p",
            embed="iri",
            on_duplicate="warn",
        )


def testimport_field_value_empty_list():
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=list[str])
    assert (
        import_field_value(
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


def testimport_field_value_empty_scalar():
    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=str)
    assert (
        import_field_value(
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


def test_bnode_embed_import_rejects_uri_ref():
    from triplemodel.embed.strategies import BnodeEmbedStrategy

    class Child(TripleModel):
        class Rdf:
            namespace = "http://example.org/c/"
            id_field = "slug"

        slug: str

    g = Child(slug="c").to_graph()
    with pytest.raises(ValueError, match="embed='bnode'"):
        BnodeEmbedStrategy().import_value(
            g, NamedNode(Child(slug="c").subject_uri()), Child
        )


def test_add_graph_mode_apply():
    from triplemodel.config import get_rdf_config
    from triplemodel.io.sync.modes import AddGraphMode

    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    p = P(slug="a", name="A")
    g = Graph()
    AddGraphMode().apply(g, p, config=get_rdf_config(P), bind=True)
    assert len(g) > 0


def test_is_rdf_resource_class_edge_cases():
    from unittest.mock import patch

    from triplemodel.protocols import _rdf_resource_classes, is_rdf_resource_class

    saved = set(_rdf_resource_classes)
    try:
        _rdf_resource_classes.clear()
        assert is_rdf_resource_class(TripleModel) is False
        _rdf_resource_classes.add(TripleModel)
        with patch(
            "triplemodel.protocols.issubclass",
            side_effect=TypeError,
        ):
            assert is_rdf_resource_class(TripleModel) is False
    finally:
        _rdf_resource_classes.clear()
        _rdf_resource_classes.update(saved)
