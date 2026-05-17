"""Field cardinality and type resolution for RDF mapping."""

from __future__ import annotations

import types
from typing import Annotated, Literal, Union, cast, get_args, get_origin

from pydantic.fields import FieldInfo

from triplemodel._typing import AnnotationExpr


def _field_annotation(field_info: FieldInfo) -> AnnotationExpr:
    return cast(AnnotationExpr, field_info.annotation)


FieldCardinality = Literal["scalar", "list", "set", "nested"]


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
    "list[TripleModel] and set[TripleModel] are not supported in 0.2; "
    "use a single nested field or multiple scalar objects per predicate."
)


def raise_if_nested_collection(field_info: FieldInfo) -> None:
    """Reject ``list[TripleModel]`` / ``set[TripleModel]`` field annotations."""
    ann = unwrap_annotation(_field_annotation(field_info))
    origin = get_origin(ann)
    if origin not in (list, set):
        return
    inner = element_type(_field_annotation(field_info))
    if isinstance(inner, type) and is_triple_model_type(inner):
        raise ValueError(_NESTED_COLLECTION_MSG)


def is_triple_model_type(tp: AnnotationExpr) -> bool:
    if not isinstance(tp, type):
        return False
    from triplemodel.model import TripleModel

    return _safe_issubclass(tp, TripleModel)


def field_cardinality(field_info: FieldInfo) -> FieldCardinality:
    """Classify how a mapped field maps to RDF objects."""
    ann = unwrap_annotation(_field_annotation(field_info))
    origin = get_origin(ann)
    if origin is list:
        return "list"
    if origin is set:
        return "set"
    if isinstance(ann, type) and is_triple_model_type(ann):
        return "nested"
    return "scalar"


def scalar_python_type(field_info: FieldInfo) -> type | None:
    """Resolved scalar type for term conversion, if a single type."""
    ann = unwrap_annotation(_field_annotation(field_info))
    card = field_cardinality(field_info)
    if card in ("list", "set"):
        inner = element_type(_field_annotation(field_info))
        return inner if isinstance(inner, type) else None
    if card == "nested":
        return None
    return ann if isinstance(ann, type) else None


def nested_model_type(field_info: FieldInfo) -> type | None:
    """Return nested :class:`TripleModel` subclass for a field, if any."""
    ann = unwrap_annotation(_field_annotation(field_info))
    if isinstance(ann, type) and is_triple_model_type(ann):
        return ann
    return None
