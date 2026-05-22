"""Field cardinality and type resolution for RDF mapping."""

from __future__ import annotations

import types
from typing import Annotated, Literal, Union, cast, get_args, get_origin

from pydantic.fields import FieldInfo

from triplemodel._typing import AnnotationExpr
from triplemodel.protocols import is_rdf_resource_class
from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.terms.lang import LangString, MultiLangString
from triplemodel.terms.opaque import OpaqueLiteral
from triplemodel.terms.typed_literal import TypedLiteral

FieldCardinality = Literal["scalar", "list", "set", "nested", "ref"]


def field_annotation(field_info: FieldInfo) -> AnnotationExpr:
    return cast(AnnotationExpr, field_info.annotation)


def unwrap_annotation(annotation: AnnotationExpr) -> AnnotationExpr:
    """Strip ``Annotated`` and single-member optional unions."""
    origin = get_origin(annotation)
    if origin is Annotated:
        return unwrap_annotation(get_args(annotation)[0])
    if origin in (Union, types.UnionType):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return unwrap_annotation(non_none[0])
    return annotation


def element_type(annotation: AnnotationExpr) -> AnnotationExpr:
    """Inner type for ``list[T]`` / ``set[T]`` after unwrapping."""
    ann = unwrap_annotation(annotation)
    origin = get_origin(ann)
    if origin in (list, set):
        args = get_args(ann)
        if len(args) == 1:
            return unwrap_annotation(args[0])
    return ann


def _safe_issubclass(subclass: type, parent: type) -> bool:
    try:
        return issubclass(subclass, parent)
    except TypeError:  # pragma: no cover - defensive; exercised via tests
        return False


_NESTED_COLLECTION_MSG = (
    "list[TripleModel] and set[TripleModel] are not supported; "
    "use a single nested field or multiple scalar objects per predicate."
)

_INVERSE_COLLECTION_MSG = "inverse= is not supported on list or set fields"


def raise_if_inverse_collection(field_info: FieldInfo) -> None:
    """Reject ``inverse=`` on ``list`` / ``set`` fields."""
    from triplemodel.fields.metadata import inverse_for_field

    if inverse_for_field(field_info) is None:
        return
    if field_cardinality(field_info) in ("list", "set"):
        raise ValueError(_INVERSE_COLLECTION_MSG)


def raise_if_nested_collection(field_info: FieldInfo) -> None:
    """Reject ``list[TripleModel]`` / ``set[TripleModel]`` field annotations."""
    ann = unwrap_annotation(field_annotation(field_info))
    origin = get_origin(ann)
    if origin not in (list, set):
        return
    inner = element_type(field_annotation(field_info))
    if isinstance(inner, type) and is_triple_model_type(inner):
        raise ValueError(_NESTED_COLLECTION_MSG)


def is_triple_model_type(tp: AnnotationExpr) -> bool:
    if not isinstance(tp, type):
        return False
    return is_rdf_resource_class(tp)


def _ref_link_for_field(field_info: FieldInfo) -> bool:
    extra = field_info.json_schema_extra
    if isinstance(extra, dict):
        return bool(cast("dict[str, object]", extra).get("rdf_ref_link"))
    return False


def field_cardinality(field_info: FieldInfo) -> FieldCardinality:
    """Classify how a mapped field maps to RDF objects."""
    ann = unwrap_annotation(field_annotation(field_info))
    origin = get_origin(ann)
    if origin is list:
        return "list"
    if origin is set:
        return "set"
    if isinstance(ann, type) and is_triple_model_type(ann):
        if _ref_link_for_field(field_info):
            return "ref"
        return "nested"
    return "scalar"


def union_member_types(field_info: FieldInfo) -> tuple[type, ...]:
    """Non-optional union members for ``str | int``-style fields."""
    ann = unwrap_annotation(field_annotation(field_info))
    origin = get_origin(ann)
    if origin not in (Union, types.UnionType):
        return ()
    return tuple(
        a for a in get_args(ann) if a is not type(None) and isinstance(a, type)
    )


def scalar_python_type(field_info: FieldInfo) -> type | None:
    """Resolved scalar type for term conversion, if a single type."""
    ann = unwrap_annotation(field_annotation(field_info))
    card = field_cardinality(field_info)
    if card in ("list", "set"):
        inner = element_type(field_annotation(field_info))
        return inner if isinstance(inner, type) else None
    if card in ("nested", "ref"):
        return None
    if ann is LangString:
        return LangString
    if ann is MultiLangString:
        return MultiLangString
    if ann is ResourceRef:
        return ResourceRef
    if ann is OpaqueLiteral:
        return OpaqueLiteral
    if ann is TypedLiteral:
        return TypedLiteral
    return ann if isinstance(ann, type) else None


def nested_model_type(field_info: FieldInfo) -> type | None:
    """Return nested :class:`TripleModel` subclass for a field, if any."""
    ann = unwrap_annotation(field_annotation(field_info))
    if isinstance(ann, type) and is_triple_model_type(ann):
        return ann
    return None
