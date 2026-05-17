"""Tests for RDF term conversion."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from rdflib import BNode, Literal, URIRef, XSD

from rdfmodel._types import python_to_term, term_to_python


def test_string_literal():
    term = python_to_term("hello")
    assert isinstance(term, Literal)
    assert term.value == "hello"
    assert term.datatype == XSD.string


def test_typed_literals():
    int_lit = python_to_term(42)
    assert isinstance(int_lit, Literal)
    assert int_lit.datatype == XSD.integer
    float_lit = python_to_term(3.14)
    assert isinstance(float_lit, Literal)
    assert float_lit.datatype == XSD.double
    bool_lit = python_to_term(True)
    assert isinstance(bool_lit, Literal)
    assert bool_lit.datatype == XSD.boolean


def test_iri_string_becomes_uri_ref():
    term = python_to_term("http://example.org/resource")
    assert isinstance(term, URIRef)


def test_round_trip_int():
    lit = python_to_term(7)
    assert term_to_python(lit, int) == 7


def test_round_trip_datetime():
    dt = datetime(2024, 1, 15, 12, 0, 0)
    lit = python_to_term(dt)
    assert term_to_python(lit, datetime) == dt


def test_round_trip_date():
    d = date(2024, 1, 15)
    lit = python_to_term(d)
    assert term_to_python(lit, date) == d


def test_bool_xsd_boolean():
    lit = Literal("true", datatype=XSD.boolean)
    assert term_to_python(lit, bool) is True
    lit_false = Literal("false", datatype=XSD.boolean)
    assert term_to_python(lit_false, bool) is False


def test_bnode_rejected_for_str():
    with pytest.raises(TypeError, match="BNode"):
        term_to_python(BNode(), str)


def test_python_to_term_passes_through_node():
    ref = URIRef("http://example.org/resource")
    assert python_to_term(ref) is ref


def test_python_to_term_fallback_literal():
    term = python_to_term(Decimal("1.5"))
    assert isinstance(term, Literal)
    assert str(term) == "1.5"


def test_term_to_python_uri_ref():
    ref = URIRef("http://example.org/resource")
    assert term_to_python(ref) == "http://example.org/resource"


def test_term_to_python_bnode_without_str_target():
    node = BNode()
    assert term_to_python(node) is node
    assert term_to_python(node, int) is node


def test_term_to_python_bool_from_non_xsd_literal():
    lit = Literal(1, datatype=XSD.integer)
    assert term_to_python(lit, bool) is True


def test_term_to_python_float():
    lit = python_to_term(3.14)
    assert term_to_python(lit, float) == 3.14


def test_term_to_python_plain_literal():
    lit = Literal("hello")
    assert term_to_python(lit) == "hello"


def test_urn_string_becomes_uri_ref():
    term = python_to_term("urn:example:resource")
    assert isinstance(term, URIRef)
