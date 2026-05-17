"""Predicate resolution for model fields."""

from __future__ import annotations

from pydantic import BaseModel

from triplemodel.config import RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel.fields.metadata import (
    predicate_for_field,
    predicate_from_annotation,
)
from triplemodel.metadata.cardinality import field_annotation
from triplemodel.namespaces import resolve_predicate
from triplemodel.protocols import PredicateResolver
from pydantic.fields import FieldInfo


class FieldPredicateResolver:
    """Default :class:`~triplemodel.protocols.PredicateResolver` implementation."""

    def resolve_field_predicate(
        self, field_info: FieldInfo, prefixes: dict[str, str]
    ) -> str | None:
        raw = predicate_for_field(field_info) or predicate_from_annotation(
            field_annotation(field_info)
        )
        if raw is None:
            return None
        return resolve_predicate(raw, prefixes)

    def owned_predicates(
        self,
        model_cls: type[BaseModel],
        config: RdfConfig | None = None,
    ) -> frozenset[str]:
        cfg = config or get_rdf_config(model_cls)
        preds: set[str] = set()
        if cfg.type_uri:
            preds.add(RDF_TYPE)
        prefixes = cfg.prefixes_dict
        for field_info in model_cls.model_fields.values():
            pred = self.resolve_field_predicate(field_info, prefixes)
            if pred is not None:
                preds.add(pred)
        return frozenset(preds)


default_resolver = FieldPredicateResolver()


def resolve_field_predicate(
    field_info: FieldInfo,
    prefixes: dict[str, str],
    *,
    resolver: PredicateResolver | None = None,
) -> str | None:
    """Resolved full predicate IRI for a field."""
    r = resolver or default_resolver
    return r.resolve_field_predicate(field_info, prefixes)


def owned_predicates(
    model_cls: type[BaseModel],
    config: RdfConfig | None = None,
    *,
    resolver: PredicateResolver | None = None,
) -> frozenset[str]:
    """Predicates owned by ``model_cls`` (mapped fields and ``rdf:type``)."""
    r = resolver or default_resolver
    return r.owned_predicates(model_cls, config)
