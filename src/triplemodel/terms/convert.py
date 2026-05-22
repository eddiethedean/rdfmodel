"""Convert between Python values and RDF terms."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import overload

from pyoxigraph import BlankNode, Literal, NamedNode, Triple

from triplemodel._typing import PythonToTermInput, RdfValue
from triplemodel.config.constants import RDF as RDF_NS
from triplemodel.store.namespaces import XSD
from triplemodel.store.terms import OxTerm, RdfTerm
from triplemodel.terms import iri
from triplemodel.terms.iri import normalize_iri
from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.terms.lang import (
    LangString,
    MultiLangString,
    _base_direction_name,
    _direction_to_base,
)
from triplemodel.terms.opaque import OpaqueLiteral
from triplemodel.terms.typed_literal import TypedLiteral
from triplemodel.terms.registry import LiteralRegistry, default_registry

RegistryLike = LiteralRegistry

_RDF_XML = f"{RDF_NS}XMLLiteral"
_RDF_HTML = f"{RDF_NS}HTML"


def python_to_term(
    value: PythonToTermInput,
    *,
    registry: RegistryLike = default_registry,
) -> RdfTerm:
    """Serialize a Python scalar to an RDF term."""
    if isinstance(value, (NamedNode, BlankNode, Literal)):
        return value
    if isinstance(value, ResourceRef):
        return NamedNode(value.iri)
    if isinstance(value, OpaqueLiteral):
        return value.to_literal()
    if isinstance(value, TypedLiteral):
        return value.to_literal()
    if isinstance(value, MultiLangString):
        raise TypeError(
            "MultiLangString cannot be serialized as a single term; "
            "export expands it to one triple per language."
        )
    if isinstance(value, LangString):
        direction = _direction_to_base(value.direction)
        if value.lang:
            if direction is not None:
                return Literal(value.value, language=value.lang, direction=direction)
            return Literal(value.value, language=value.lang)
        if direction is not None:
            return Literal(value.value, direction=direction)
        return Literal(value.value)
    if isinstance(value, Enum):
        lit = registry.python_to_literal(value, type(value))
        if lit is not None:
            return lit
        return Literal(value.value, datatype=XSD.string)
    lit = registry.python_to_literal(value, type(value))
    if lit is not None:
        return lit
    if isinstance(value, bool):
        return Literal(str(value).lower(), datatype=XSD.boolean)
    if isinstance(value, int) and not isinstance(value, bool):
        return Literal(str(value), datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(str(value), datatype=XSD.double)
    if isinstance(value, datetime):
        return Literal(value.isoformat(), datatype=XSD.dateTime)
    if isinstance(value, date):
        return Literal(value.isoformat(), datatype=XSD.date)
    if isinstance(value, str):
        text = normalize_iri(value)
        if iri.looks_like_iri(text):
            return NamedNode(text)
        return Literal(value, datatype=XSD.string)
    if isinstance(value, (bytes, bytearray)):
        return Literal(bytes(value).decode("utf-8", errors="replace"))
    return Literal(str(value))


@overload
def term_to_python(
    term: OxTerm, target_type: type[str], *, registry: RegistryLike = ...
) -> str: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[int], *, registry: RegistryLike = ...
) -> int: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[float], *, registry: RegistryLike = ...
) -> float: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[bool], *, registry: RegistryLike = ...
) -> bool: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[date], *, registry: RegistryLike = ...
) -> date: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[datetime], *, registry: RegistryLike = ...
) -> datetime: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type[Enum], *, registry: RegistryLike = ...
) -> Enum: ...


@overload
def term_to_python(
    term: OxTerm, target_type: None = None, *, registry: RegistryLike = ...
) -> RdfValue: ...


@overload
def term_to_python(
    term: OxTerm, target_type: type, *, registry: RegistryLike = ...
) -> RdfValue: ...


def term_to_python(
    term: OxTerm,
    target_type: type | None = None,
    *,
    registry: RegistryLike = default_registry,
) -> RdfValue:
    """Deserialize an RDF term to a Python value."""
    if isinstance(term, Triple):
        raise TypeError("RDF-star triple terms cannot be converted to Python values.")
    if target_type is TypedLiteral:
        if not isinstance(term, Literal):
            raise TypeError(
                f"Cannot convert {term!r} to TypedLiteral; expected a literal."
            )
        return TypedLiteral.from_literal(term)

    if isinstance(term, NamedNode):
        if target_type is ResourceRef:
            return ResourceRef(str(term.value))
        return str(term.value)

    if not isinstance(term, Literal):
        if isinstance(term, BlankNode) and target_type is not None:
            raise TypeError(
                "BNode objects cannot be assigned to scalar fields; "
                "use a nested TripleModel field with embed='bnode'."
            )
        return term

    if target_type is ResourceRef:
        return ResourceRef(str(term.value))

    if target_type is LangString:
        return LangString(
            str(term.value),
            term.language or None,
            _base_direction_name(term.direction),
        )

    if target_type is OpaqueLiteral:
        return OpaqueLiteral.from_literal(term)

    if target_type is not None:
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            return target_type(str(term.value))
        converted = registry.literal_to_python(term, target_type)
        if converted is not None:
            return converted

    dt = term.datatype
    dt_str = str(dt.value) if dt is not None else None

    if target_type is bool:
        if dt == XSD.boolean:
            return term.value in (True, "true", "1", 1)
        return term.value in (True, "true", "1", 1)
    if target_type is int:
        return int(term.value)
    if target_type is str:
        if dt_str == _RDF_XML or dt_str == _RDF_HTML:
            return str(term.value)
        return str(term.value)

    if target_type is float:
        return float(term.value)
    if target_type is datetime:
        return datetime.fromisoformat(str(term.value))
    if target_type is date:
        return date.fromisoformat(str(term.value))

    if target_type is None:
        converted = registry.literal_to_python(term, None)
        if converted is not None:
            return converted
        if dt is not None:
            return OpaqueLiteral.from_literal(term)

    if dt is not None and dt_str != str(XSD.string.value):
        return OpaqueLiteral.from_literal(term)

    return term.value
