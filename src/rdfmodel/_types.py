"""Convert between Python values and RDF terms."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from rdflib import Literal, URIRef, XSD
from rdflib.term import Node

_SCALAR_MAP: dict[type, URIRef] = {
    str: XSD.string,
    int: XSD.integer,
    float: XSD.double,
    bool: XSD.boolean,
    date: XSD.date,
    datetime: XSD.dateTime,
}


def python_to_term(value: Any) -> Node:
    """Serialize a Python scalar to an RDF term."""
    if isinstance(value, Node):
        return value
    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)
    if isinstance(value, int) and not isinstance(value, bool):
        return Literal(value, datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(value, datatype=XSD.double)
    if isinstance(value, datetime):
        return Literal(value.isoformat(), datatype=XSD.dateTime)
    if isinstance(value, date):
        return Literal(value.isoformat(), datatype=XSD.date)
    if isinstance(value, str) and _looks_like_iri(value):
        return URIRef(value)
    return Literal(value)


def term_to_python(term: Node, target_type: type | None = None) -> Any:
    """Deserialize an RDF term to a Python value."""
    if isinstance(term, URIRef):
        return str(term)

    if not isinstance(term, Literal):
        return term

    if target_type is bool:
        return term.value in (True, "true", "1", 1)
    if target_type is int:
        return int(term)
    if target_type is float:
        return float(term)
    if target_type is datetime:
        return datetime.fromisoformat(str(term))
    if target_type is date:
        return date.fromisoformat(str(term))

    return term.toPython()


def _looks_like_iri(value: str) -> bool:
    return value.startswith(("http://", "https://", "urn:"))
