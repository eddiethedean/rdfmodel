"""Shared typing aliases for TripleModel."""

from __future__ import annotations

import types
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import ForwardRef, TypedDict, TypeAlias, TypeVar

from uuid import UUID

from pydantic import BaseModel
from rdflib.term import Node

# --- Python / RDF value shapes ---

RdfScalar: TypeAlias = str | int | float | bool | date | datetime | Decimal | UUID

"""Scalars serialized to XSD literals or IRIs."""

PythonToTermInput: TypeAlias = RdfScalar | Enum | Node

"""Values accepted by :func:`~triplemodel.terms.convert.python_to_term`."""

TripleObject: TypeAlias = PythonToTermInput | str

"""Object slot in pre-serialization triple rows (includes ``rdf:type`` IRIs)."""

TripleRow: TypeAlias = tuple[str | Node, str, TripleObject]

RdfValue: TypeAlias = RdfScalar | Node | Enum

"""Values produced by :func:`~triplemodel.terms.convert.term_to_python` for mapped fields."""

ModelFieldScalar: TypeAlias = (
    RdfScalar | str
)  # includes :class:`~triplemodel.terms.lang.LangString`

ModelFieldValue: TypeAlias = (
    ModelFieldScalar | list[ModelFieldScalar] | set[ModelFieldScalar] | BaseModel | None
)

ModelInitData: TypeAlias = dict[str, ModelFieldValue]

# --- Annotation introspection (Pydantic field annotations) ---

AnnotationExpr: TypeAlias = (
    type | types.GenericAlias | types.UnionType | str | ForwardRef
)

# --- Pydantic ``Field`` kwargs accepted by :func:`~triplemodel.rdf_field` ---

JsonSchemaExtra: TypeAlias = dict[str, str | bool | int | float | None]

FactoryReturn: TypeAlias = (
    ModelFieldScalar | list[ModelFieldScalar] | set[ModelFieldScalar]
)


class RdfFieldKwargs(TypedDict, total=False):
    """Keyword arguments forwarded to :func:`pydantic.Field` from :func:`~triplemodel.rdf_field`."""

    alias: str
    alias_priority: int
    title: str
    description: str
    examples: list[str]
    default_factory: Callable[[], FactoryReturn]
    frozen: bool
    repr: bool
    init: bool
    init_var: bool
    kw_only: bool
    json_schema_extra: JsonSchemaExtra


# --- Literal registry ---

PyT = TypeVar("PyT")
