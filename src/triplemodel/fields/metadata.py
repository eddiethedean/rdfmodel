"""Field helpers and predicate metadata for RDF mapping."""

from __future__ import annotations

from dataclasses import dataclass
from types import EllipsisType
from typing import Annotated, Any, TypeVar, cast, get_args, get_origin, overload

from typing_extensions import Unpack

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from triplemodel._typing import AnnotationExpr, JsonSchemaExtra, RdfFieldKwargs
from triplemodel.metadata.cardinality import field_annotation

_T = TypeVar("_T")


@dataclass(frozen=True)
class Predicate:
    """Marks a model field with its RDF predicate IRI."""

    uri: str


@dataclass(frozen=True)
class IriId:
    """Mark ``id_field`` as a full IRI string (not appended to ``namespace``)."""


@overload
def rdf_field(
    predicate: str,
    *,
    default: EllipsisType = ...,
    **field_kwargs: Unpack[RdfFieldKwargs],
) -> Any: ...


@overload
def rdf_field(
    predicate: str,
    *,
    default: _T,
    **field_kwargs: Unpack[RdfFieldKwargs],
) -> _T: ...


def rdf_field(
    predicate: str,
    *,
    default: _T | EllipsisType = ...,
    **field_kwargs: Unpack[RdfFieldKwargs],
) -> _T:
    """Create a Pydantic field bound to an RDF predicate."""
    extra = field_kwargs.pop("json_schema_extra", None) or {}
    if not isinstance(extra, dict):
        extra = {}
    merged_extra: JsonSchemaExtra = {
        **cast(JsonSchemaExtra, extra),
        "rdf_predicate": predicate,
    }
    return cast(
        _T,
        Field(
            default=default, json_schema_extra=merged_extra, **cast(Any, field_kwargs)
        ),
    )


def predicate_for_field(field_info: FieldInfo) -> str | None:
    """Resolve the RDF predicate URI for a Pydantic field, if any."""
    extra = field_info.json_schema_extra
    if isinstance(extra, dict):
        predicate = cast(JsonSchemaExtra, extra).get("rdf_predicate")
        if predicate is not None:
            return str(predicate)

    for meta in field_info.metadata:
        if isinstance(meta, Predicate):
            return meta.uri

    return None


def predicate_from_annotation(annotation: AnnotationExpr) -> str | None:
    """Read :class:`Predicate` from ``Annotated[..., Predicate(...)]``."""
    if get_origin(annotation) is not Annotated:
        return None
    for meta in get_args(annotation)[1:]:
        if isinstance(meta, Predicate):
            return meta.uri
    return None


def annotation_has_iri_id(annotation: AnnotationExpr) -> bool:
    """True when ``annotation`` includes :class:`IriId` metadata."""
    if get_origin(annotation) is not Annotated:
        return False
    return any(isinstance(meta, IriId) for meta in get_args(annotation)[1:])


def id_field_is_iri_id(model_cls: type[BaseModel], id_field: str) -> bool:
    """True when the configured ``id_field`` is marked with :class:`IriId`."""
    model_fields = getattr(model_cls, "model_fields", {})
    field_info = model_fields.get(id_field)
    if field_info is None:
        return False
    return annotation_has_iri_id(field_annotation(field_info)) or any(
        isinstance(meta, IriId) for meta in field_info.metadata
    )
