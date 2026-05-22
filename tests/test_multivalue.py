"""Tests for multi-valued list/set fields."""

from __future__ import annotations

import warnings
from typing import cast

import pytest
from pyoxigraph import Literal, NamedNode

from triplemodel import TripleModel, TypedLiteral, rdf_field
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.namespaces import XSD
from triplemodel.store.terms import OxTerm, term_str
from triplemodel.terms import python_to_term

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"
MEASURE = "http://example.org/measure/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
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


class Measured(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Measured"
        id_field = "slug"

    slug: str
    amount: set[TypedLiteral] = rdf_field(f"{MEASURE}amount", default_factory=set)
    readings: list[TypedLiteral] = rdf_field(f"{MEASURE}reading", default_factory=list)


def test_typed_literal_set_roundtrip_mixed_datatypes():
    int_dt = str(XSD.integer.value)
    dec_dt = str(XSD.decimal.value)
    amounts = {
        TypedLiteral("42", int_dt),
        TypedLiteral("3.14", dec_dt),
    }
    m = Measured(slug="m1", amount=amounts)
    g = m.to_graph()
    pred = NamedNode(f"{MEASURE}amount")
    literals = [o for o in g.objects(NamedNode(m.subject_uri()), pred)]
    assert len(literals) == 2
    dts = {str(o.datatype.value) for o in literals if isinstance(o, Literal)}
    assert dts == {int_dt, dec_dt}
    restored = Measured.from_graph(g, m.subject_uri())
    assert restored.amount == amounts


def test_typed_literal_list_roundtrip():
    values = [
        TypedLiteral(10, str(XSD.integer.value)),
        TypedLiteral("3.14", str(XSD.decimal.value)),
    ]
    m = Measured(slug="m1", readings=values)
    restored = Measured.from_graph(m.to_graph(), m.subject_uri())
    assert restored.readings == values


def test_typed_literal_plain_untyped():
    m = Measured(slug="m1", amount={TypedLiteral("plain")})
    restored = Measured.from_graph(m.to_graph(), m.subject_uri())
    assert restored.amount == {TypedLiteral("plain")}


def test_typed_literal_set_duplicate_same_datatype_warns():
    from triplemodel.io.import_ import import_field_value

    objects = [
        Literal("5", datatype=XSD.integer),
        Literal("5", datatype=XSD.integer),
    ]
    field_info = Measured.model_fields["amount"]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = import_field_value(
            Graph(),
            cast(list[OxTerm], objects),
            field_info,
            "amount",
            f"{MEASURE}amount",
            f"{EX}m1",
            embed="iri",
            on_duplicate="warn",
        )
    assert len(w) == 1
    assert "Duplicate TypedLiteral" in str(w[0].message)
    assert result == {TypedLiteral("5", str(XSD.integer.value))}


def test_scalar_typed_literal_roundtrip():
    class Note(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Note"
            id_field = "slug"

        slug: str
        value: TypedLiteral = rdf_field(f"{MEASURE}value")

    n = Note(slug="n1", value=TypedLiteral("99", str(XSD.integer.value)))
    restored = Note.from_graph(n.to_graph(), n.subject_uri())
    assert restored.value == TypedLiteral("99", str(XSD.integer.value))


def test_typed_literal_python_to_term():
    term = python_to_term(TypedLiteral("7", str(XSD.integer.value)))
    assert isinstance(term, Literal)
    assert term.datatype == XSD.integer
    assert term.value == "7"


def test_typed_literal_term_to_python_requires_literal():
    from triplemodel.terms.convert import term_to_python

    with pytest.raises(TypeError, match="TypedLiteral"):
        term_to_python(NamedNode(EX + "x"), TypedLiteral)


def test_scalar_duplicate_still_warns():
    g = Graph()
    subj = NamedNode(EX + "a")
    g.add(
        (
            subj,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            NamedNode(PERSON_TYPE),
        )
    )
    g.add((subj, NamedNode(f"{FOAF}name"), Literal("A")))
    g.add((subj, NamedNode(f"{FOAF}name"), Literal("B")))
    with pytest.warns(UserWarning, match="Multiple objects"):
        Person.from_graph(g, term_str(subj), validate_type=False)
