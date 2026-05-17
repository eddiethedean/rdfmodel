"""Field helpers and predicate metadata for RDF mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, cast, get_args, get_origin

from pydantic import Field
from pydantic.fields import FieldInfo


@dataclass(frozen=True)
class Predicate:
    """Marks a model field with its RDF predicate IRI."""

    uri: str


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
