"""Tests for RDF term conversion."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from rdflib import Literal, URIRef, XSD

from rdfmodel._types import python_to_term, term_to_python


def test_string_literal():
    term = python_to_term("hello")
    assert isinstance(term, Literal)
    assert term.value == "hello"
    assert term.datatype == XSD.string


def test_typed_literals():
    assert python_to_term(42).datatype == XSD.integer
    assert python_to_term(3.14).datatype == XSD.double
    assert python_to_term(True).datatype == XSD.boolean


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
    from rdflib import BNode

    with pytest.raises(TypeError, match="BNode"):
        term_to_python(BNode(), str)
