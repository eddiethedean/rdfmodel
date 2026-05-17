"""Export Pydantic models to RDF triple rows."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from triplemodel._typing import ModelFieldScalar, ModelFieldValue, TripleRow
from triplemodel.config import RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel.embed.strategies import export_nested_triples
from triplemodel.fields.metadata import lang_for_field
from triplemodel.fields.resolver import default_resolver
from triplemodel.terms.lang import LangString
from triplemodel.metadata.cardinality import (
    field_cardinality,
    raise_if_nested_collection,
)
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry


def _field_values_for_export(
    name: str,
    value: ModelFieldValue,
    field_info: FieldInfo,
) -> list[ModelFieldScalar]:
    """Normalize a field value to a list of objects to emit as triples."""
    card = field_cardinality(field_info)
    if value is None:
        return []
    if card == "list":
        return []
    if card == "set":
        items = cast(set[ModelFieldScalar], value)
        return [v for v in items if v is not None]
    return [cast(ModelFieldScalar, value)]


def model_to_triples(
    model: BaseModel,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry | None = None,
) -> list[TripleRow]:
    """Return (subject, predicate, object) tuples for a model instance."""
    _ = registry  # reserved for future per-field literal overrides
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    r = resolver or default_resolver
    prefixes = cfg.prefixes_dict
    subject = uri or cfg.subject_uri(model)
    triples: list[TripleRow] = []

    if cfg.type_uri:
        triples.append((subject, RDF_TYPE, cfg.type_uri))

    id_field = cfg.id_field
    for name, field_info in cls.model_fields.items():
        if id_field and name == id_field:
            continue
        predicate = r.resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        raise_if_nested_collection(field_info)
        value = getattr(model, name)
        card = field_cardinality(field_info)

        if card == "nested":
            if value is None:
                continue
            triples.extend(
                export_nested_triples(
                    subject,
                    predicate,
                    value,
                    embed=cfg.embed,
                    config=cfg,
                )
            )
            continue

        if card == "list":
            continue

        lang = lang_for_field(field_info)
        for item in _field_values_for_export(name, value, field_info):
            obj: ModelFieldScalar = cast(ModelFieldScalar, item)
            if lang and isinstance(obj, str):
                obj = LangString(obj, lang)
            triples.append((subject, predicate, obj))

    return triples
