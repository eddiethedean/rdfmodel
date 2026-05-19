"""Tests for custom literal registry."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import ConfigDict
from pyoxigraph import Literal
from triplemodel.store.namespaces import XSD

from triplemodel import TripleModel, graph_to_model, rdf_field
from triplemodel.terms import (
    LiteralRegistry,
    converter_for_type,
    literal_to_python,
    python_to_literal,
    register_literal_type,
)
from triplemodel.terms import python_to_term, term_to_python

AMOUNT = "http://example.org/amount"
HAS_BOX = "http://example.org/hasBox"


class Color(Enum):
    RED = "red"


def test_decimal_roundtrip():
    term = python_to_term(Decimal("1.5"))
    assert isinstance(term, Literal)
    assert term_to_python(term, Decimal) == Decimal("1.5")


def test_uuid_roundtrip():
    uid = UUID("12345678-1234-5678-1234-567812345678")
    term = python_to_term(uid)
    assert term_to_python(term, UUID) == uid


def test_enum_roundtrip():
    term = python_to_term(Color.RED)
    assert term_to_python(term, Color) is Color.RED


def test_register_custom_type():
    class Custom:
        def __init__(self, v: str):
            self.v = v

    register_literal_type(
        Custom,
        lambda c: Literal(c.v, datatype=XSD.string),
        lambda lit: Custom(str(lit.value)),
    )
    assert converter_for_type(Custom) is not None
    lit = python_to_literal(Custom("x"), Custom)
    assert lit is not None
    result = literal_to_python(lit, Custom)
    assert isinstance(result, Custom)
    assert result.v == "x"


def test_nested_import_uses_custom_registry():
    class CustomAmount:
        def __init__(self, v: Decimal) -> None:
            self.v = v

        def __eq__(self, other: object) -> bool:
            return isinstance(other, CustomAmount) and self.v == other.v

    registry = LiteralRegistry()
    registry.register_literal_type(
        CustomAmount,
        lambda a: Literal(str(a.v), datatype=XSD.decimal),
        lambda lit: CustomAmount(Decimal(str(lit.value))),
        datatype=str(XSD.decimal),
    )

    class Box(TripleModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str
        amount: CustomAmount = rdf_field(AMOUNT)

    class Parent(TripleModel):
        class Rdf:
            namespace = "http://example.org/parent/"
            id_field = "slug"
            embed = "iri"

        slug: str
        box: Box = rdf_field(HAS_BOX)

    box = Box(slug="b1", amount=CustomAmount(Decimal("9.99")))
    parent = Parent(slug="p1", box=box)
    g = parent.to_graph(registry=registry)
    restored = graph_to_model(g, Parent, parent.subject_uri(), registry=registry)
    assert restored.box.amount == CustomAmount(Decimal("9.99"))
