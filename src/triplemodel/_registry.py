"""Pluggable Python ↔ RDF literal converters."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from rdflib import Literal, XSD

_ToLiteral = Callable[[Any], Literal]
_FromLiteral = Callable[[Literal], Any]

_REGISTRY: dict[type[Any], tuple[_ToLiteral, _FromLiteral]] = {}


def register_literal_type(
    py_type: type[Any],
    to_literal: _ToLiteral,
    from_literal: _FromLiteral,
    *,
    datatype: str | None = None,
) -> None:
    """Register converters for a Python type."""
    _REGISTRY[py_type] = (to_literal, from_literal)
    if datatype is not None:
        from rdflib.term import bind

        bind(datatype, py_type)


def converter_for_type(py_type: type[Any]) -> tuple[_ToLiteral, _FromLiteral] | None:
    for registered, converters in _REGISTRY.items():
        if registered is py_type or (
            isinstance(py_type, type) and issubclass(py_type, registered)
        ):
            return converters
    return None


def python_to_literal(value: Any, py_type: type[Any] | None = None) -> Literal | None:
    """Use registry for ``value`` when a converter is registered."""
    target = py_type if py_type is not None else type(value)
    conv = converter_for_type(target)
    if conv is None:
        return None
    to_literal, _ = conv
    return to_literal(value)


def literal_to_python(term: Literal, py_type: type[Any] | None) -> Any | None:
    if py_type is None:
        return None
    conv = converter_for_type(py_type)
    if conv is None:
        return None
    _, from_literal = conv
    return from_literal(term)


def _decimal_to_literal(value: Decimal) -> Literal:
    return Literal(str(value), datatype=XSD.decimal)


def _decimal_from_literal(term: Literal) -> Decimal:
    return Decimal(str(term))


def _uuid_to_literal(value: UUID) -> Literal:
    return Literal(str(value), datatype=XSD.string)


def _uuid_from_literal(term: Literal) -> UUID:
    return UUID(str(term))


def _register_defaults() -> None:
    register_literal_type(
        Decimal, _decimal_to_literal, _decimal_from_literal, datatype=str(XSD.decimal)
    )
    register_literal_type(UUID, _uuid_to_literal, _uuid_from_literal)


_register_defaults()
