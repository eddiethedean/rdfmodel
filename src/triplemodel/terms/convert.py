"""Convert between Python values and RDF terms."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import overload

from rdflib import BNode, Literal, URIRef, XSD
from rdflib.term import Node

from triplemodel._typing import PythonToTermInput, RdfValue
from triplemodel.terms import iri
from triplemodel.terms.registry import LiteralRegistry, default_registry

RegistryLike = LiteralRegistry


def python_to_term(
    value: PythonToTermInput,
    *,
    registry: RegistryLike = default_registry,
) -> Node:
    """Serialize a Python scalar to an RDF term."""
    if isinstance(value, Node):
        return value
    if isinstance(value, Enum):
        lit = registry.python_to_literal(value, type(value))
        if lit is not None:
            return lit
        return Literal(value.value, datatype=XSD.string)
    lit = registry.python_to_literal(value, type(value))
    if lit is not None:
        return lit
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
    if isinstance(value, str):
        if iri.looks_like_iri(value):
            return URIRef(value)
        return Literal(value, datatype=XSD.string)
    return Literal(value)


@overload
def term_to_python(
    term: Node, target_type: type[str], *, registry: RegistryLike = ...
) -> str: ...


@overload
def term_to_python(
    term: Node, target_type: type[int], *, registry: RegistryLike = ...
) -> int: ...


@overload
def term_to_python(
    term: Node, target_type: type[float], *, registry: RegistryLike = ...
) -> float: ...


@overload
def term_to_python(
    term: Node, target_type: type[bool], *, registry: RegistryLike = ...
) -> bool: ...


@overload
def term_to_python(
    term: Node, target_type: type[date], *, registry: RegistryLike = ...
) -> date: ...


@overload
def term_to_python(
    term: Node, target_type: type[datetime], *, registry: RegistryLike = ...
) -> datetime: ...


@overload
def term_to_python(
    term: Node, target_type: type[Enum], *, registry: RegistryLike = ...
) -> Enum: ...


@overload
def term_to_python(
    term: Node, target_type: None = None, *, registry: RegistryLike = ...
) -> RdfValue: ...


@overload
def term_to_python(
    term: Node, target_type: type, *, registry: RegistryLike = ...
) -> RdfValue: ...


def term_to_python(
    term: Node,
    target_type: type | None = None,
    *,
    registry: RegistryLike = default_registry,
) -> RdfValue:
    """Deserialize an RDF term to a Python value."""
    if isinstance(term, URIRef):
        return str(term)

    if not isinstance(term, Literal):
        if isinstance(term, BNode) and target_type is str:
            raise TypeError(
                "BNode objects cannot be assigned to str fields; "
                "blank node support is planned for a future release."
            )
        return term

    if target_type is not None:
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            return target_type(str(term))
        converted = registry.literal_to_python(term, target_type)
        if converted is not None:
            return converted

    if target_type is bool:
        if term.datatype == XSD.boolean:
            return bool(term.toPython())
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
