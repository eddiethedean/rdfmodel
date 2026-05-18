"""Pluggable Python ↔ RDF literal converters."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from enum import Enum
from typing import cast
from uuid import UUID

from rdflib import Literal, XSD

from triplemodel._typing import PyT, RdfScalar

RegistryValue = RdfScalar | Decimal | UUID


class LiteralRegistry:
    """Registry of Python type ↔ RDF literal converters."""

    def __init__(self) -> None:
        self._entries: dict[
            type,
            tuple[Callable[..., Literal], Callable[[Literal], RegistryValue]],
        ] = {}
        self._datatype_from_literal: dict[
            str, Callable[[Literal], RegistryValue]
        ] = {}

    def register_literal_type(
        self,
        py_type: type[PyT],
        to_literal: Callable[[PyT], Literal],
        from_literal: Callable[[Literal], PyT],
        *,
        datatype: str | None = None,
    ) -> None:
        """Register converters for a Python type."""
        self._entries[py_type] = (
            cast(Callable[..., Literal], to_literal),
            cast(Callable[[Literal], RegistryValue], from_literal),
        )
        if datatype is not None:
            from rdflib.term import bind

            bind(datatype, py_type)
            self._datatype_from_literal[str(datatype)] = cast(
                Callable[[Literal], RegistryValue], from_literal
            )

    def converter_for_datatype(
        self, datatype: str
    ) -> Callable[[Literal], RegistryValue] | None:
        """Return import converter registered for an XSD datatype IRI."""
        return self._datatype_from_literal.get(datatype)

    def converter_for_type(
        self, py_type: type
    ) -> tuple[Callable[..., Literal], Callable[[Literal], RegistryValue]] | None:
        for registered, converters in self._entries.items():
            if registered is py_type or (
                isinstance(py_type, type) and issubclass(py_type, registered)
            ):
                return converters
        return None

    def python_to_literal(
        self,
        value: PyT | RdfScalar | Decimal | UUID | Enum,
        py_type: type[PyT] | type | None = None,
    ) -> Literal | None:
        """Use registry for ``value`` when a converter is registered."""
        target = py_type if py_type is not None else type(value)
        conv = self.converter_for_type(target)
        if conv is None:
            return None
        to_literal, _ = conv
        return to_literal(value)

    def literal_to_python(
        self, term: Literal, py_type: type[PyT] | type | None
    ) -> RegistryValue | PyT | None:
        if isinstance(term, Literal) and term.datatype is not None:
            by_dt = self.converter_for_datatype(str(term.datatype))
            if by_dt is not None:
                return by_dt(term)
        if py_type is None:
            return None
        conv = self.converter_for_type(py_type)
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


default_registry = LiteralRegistry()
default_registry.register_literal_type(
    Decimal, _decimal_to_literal, _decimal_from_literal, datatype=str(XSD.decimal)
)
default_registry.register_literal_type(UUID, _uuid_to_literal, _uuid_from_literal)


def _g_year_from_literal(term: Literal) -> int:
    return int(str(term))


def _g_month_from_literal(term: Literal) -> str:
    return str(term)


def _g_month_day_from_literal(term: Literal) -> str:
    return str(term)


# Partial XSD dates: import via datatype; export via rdf_field(literal_datatype=...)
default_registry._datatype_from_literal[str(XSD.gYear)] = _g_year_from_literal
default_registry._datatype_from_literal[str(XSD.gMonth)] = _g_month_from_literal
default_registry._datatype_from_literal[str(XSD.gMonthDay)] = _g_month_day_from_literal


def register_literal_type(
    py_type: type[PyT],
    to_literal: Callable[[PyT], Literal],
    from_literal: Callable[[Literal], PyT],
    *,
    datatype: str | None = None,
) -> None:
    """Register converters on the package-default :data:`default_registry`."""
    default_registry.register_literal_type(
        py_type, to_literal, from_literal, datatype=datatype
    )


def converter_for_type(
    py_type: type,
) -> tuple[Callable[..., Literal], Callable[[Literal], RegistryValue]] | None:
    return default_registry.converter_for_type(py_type)


def python_to_literal(
    value: PyT | RdfScalar | Decimal | UUID | Enum,
    py_type: type[PyT] | type | None = None,
) -> Literal | None:
    return default_registry.python_to_literal(value, py_type=py_type)


def literal_to_python(
    term: Literal, py_type: type[PyT] | type | None
) -> RegistryValue | PyT | None:
    return default_registry.literal_to_python(term, py_type)
