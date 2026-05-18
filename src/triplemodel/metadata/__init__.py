"""Field annotation and cardinality helpers."""

from triplemodel.metadata.cardinality import (
    FieldCardinality,
    element_type,
    field_annotation,
    field_cardinality,
    is_triple_model_type,
    nested_model_type,
    raise_if_inverse_collection,
    raise_if_nested_collection,
    scalar_python_type,
    unwrap_annotation,
)

__all__ = [
    "FieldCardinality",
    "element_type",
    "field_annotation",
    "field_cardinality",
    "is_triple_model_type",
    "nested_model_type",
    "raise_if_inverse_collection",
    "raise_if_nested_collection",
    "scalar_python_type",
    "unwrap_annotation",
]
