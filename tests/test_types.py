"""Tests for RDF term conversion."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from pyoxigraph import BlankNode as BNode, Literal, NamedNode as URIRef, Triple

from triplemodel.store.namespaces import XSD
from triplemodel.terms import python_to_term, term_to_python


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


def test_round_trip_float():
    lit = python_to_term(2.5)
    assert term_to_python(lit, float) == 2.5


def test_round_trip_bool():
    lit = python_to_term(False)
    assert term_to_python(lit, bool) is False


def test_round_trip_date():
    lit = python_to_term(date(2020, 1, 2))
    assert term_to_python(lit, date) == date(2020, 1, 2)


def test_round_trip_datetime():
    dt = datetime(2020, 1, 2, 3, 4, 5)
    lit = python_to_term(dt)
    assert term_to_python(lit, datetime) == dt


def test_decimal_registry():
    lit = python_to_term(Decimal("1.5"))
    assert term_to_python(lit, Decimal) == Decimal("1.5")


def test_bnode_scalar_raises():
    with pytest.raises(TypeError, match="BNode"):
        term_to_python(BNode(), str)


def test_rdf_star_triple_term_raises():
    triple = Triple(URIRef("http://ex/s"), URIRef("http://ex/p"), Literal("v"))
    with pytest.raises(TypeError, match="RDF-star triple terms"):
        term_to_python(triple)
