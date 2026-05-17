"""Tests for custom literal registry."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID

from rdflib import Literal, XSD

from triplemodel.terms import (
    converter_for_type,
    literal_to_python,
    python_to_literal,
    register_literal_type,
)
from triplemodel.terms import python_to_term, term_to_python


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
        lambda lit: Custom(str(lit)),
    )
    assert converter_for_type(Custom) is not None
    lit = python_to_literal(Custom("x"), Custom)
    assert lit is not None
    result = literal_to_python(lit, Custom)
    assert isinstance(result, Custom)
    assert result.v == "x"
