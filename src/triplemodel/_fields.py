"""Field helpers and predicate metadata for RDF mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, cast, get_args, get_origin

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from triplemodel._config import RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel._namespaces import resolve_predicate


@dataclass(frozen=True)
class Predicate:
    """Marks a model field with its RDF predicate IRI."""

    uri: str


@dataclass(frozen=True)
class IriId:
    """Mark ``id_field`` as a full IRI string (not appended to ``namespace``)."""


def rdf_field(
    predicate: str,
    *,
    default: Any = ...,
    **field_kwargs: Any,
) -> Any:
    """Create a Pydantic field bound to an RDF predicate.

    Example::

        name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
    """
    extra = field_kwargs.pop("json_schema_extra", None) or {}
    if not isinstance(extra, dict):
        extra = {}
    extra = {**extra, "rdf_predicate": predicate}
    return Field(default=default, json_schema_extra=extra, **field_kwargs)


def predicate_for_field(field_info: FieldInfo) -> str | None:
    """Resolve the RDF predicate URI for a Pydantic field, if any."""
    extra = field_info.json_schema_extra
    if isinstance(extra, dict):
        predicate = cast(dict[str, Any], extra).get("rdf_predicate")
        if predicate is not None:
            return str(predicate)

    for meta in field_info.metadata:
        if isinstance(meta, Predicate):
            return meta.uri

    return None


def predicate_from_annotation(annotation: Any) -> str | None:
    """Read :class:`Predicate` from ``Annotated[..., Predicate(...)]``."""
    if get_origin(annotation) is not Annotated:
        return None
    for meta in get_args(annotation)[1:]:
        if isinstance(meta, Predicate):
            return meta.uri
    return None


def annotation_has_iri_id(annotation: Any) -> bool:
    """True when ``annotation`` includes :class:`IriId` metadata."""
    if get_origin(annotation) is not Annotated:
        return False
    return any(isinstance(meta, IriId) for meta in get_args(annotation)[1:])


def id_field_is_iri_id(model_cls: type[BaseModel], id_field: str) -> bool:
    """True when the configured ``id_field`` is marked with :class:`IriId`."""
    field_info = model_cls.model_fields.get(id_field)
    if field_info is None:
        return False
    return annotation_has_iri_id(field_info.annotation) or any(
        isinstance(meta, IriId) for meta in field_info.metadata
    )


def resolve_field_predicate(
    field_info: FieldInfo,
    prefixes: dict[str, str],
) -> str | None:
    """Resolved full predicate IRI for a field."""
    raw = predicate_for_field(field_info) or predicate_from_annotation(
        field_info.annotation
    )
    if raw is None:
        return None
    return resolve_predicate(raw, prefixes)


def owned_predicates(
    model_cls: type[BaseModel],
    config: RdfConfig | None = None,
) -> frozenset[str]:
    """Predicates owned by ``model_cls`` (mapped fields and ``rdf:type``)."""
    cfg = config or get_rdf_config(model_cls)
    preds: set[str] = set()
    if cfg.type_uri:
        preds.add(RDF_TYPE)
    prefixes = cfg.prefixes_dict
    for field_info in model_cls.model_fields.values():
        pred = resolve_field_predicate(field_info, prefixes)
        if pred is not None:
            preds.add(pred)
    return frozenset(preds)
