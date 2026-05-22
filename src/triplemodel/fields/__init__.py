"""RDF field metadata and predicate resolution."""

from triplemodel.fields.back_populates import (
    BackPopulates,
    inverse_pair,
    back_populates_for_field,
    models_via_back_populates,
    subjects_via_back_populates,
)
from triplemodel.fields.metadata import (
    IriId,
    InverseOf,
    Predicate,
    Transitive,
    id_field_is_iri_id,
    inverse_for_field,
    rdf_field,
    ref_field,
    transitive_for_field,
)
from triplemodel.fields.metadata import (
    annotation_has_iri_id,
    predicate_for_field,
    predicate_from_annotation,
)
from triplemodel.fields.resolver import (
    FieldPredicateResolver,
    default_resolver,
    owned_predicates,
    resolve_field_predicate,
)

__all__ = [
    "BackPopulates",
    "FieldPredicateResolver",
    "IriId",
    "InverseOf",
    "Predicate",
    "Transitive",
    "back_populates_for_field",
    "inverse_pair",
    "inverse_for_field",
    "models_via_back_populates",
    "subjects_via_back_populates",
    "transitive_for_field",
    "annotation_has_iri_id",
    "default_resolver",
    "id_field_is_iri_id",
    "owned_predicates",
    "predicate_for_field",
    "predicate_from_annotation",
    "rdf_field",
    "ref_field",
    "resolve_field_predicate",
]
