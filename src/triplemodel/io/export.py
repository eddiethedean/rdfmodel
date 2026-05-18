"""Export Pydantic models to RDF triple rows."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from rdflib import Literal, URIRef, XSD

from triplemodel._typing import ModelFieldScalar, ModelFieldValue, TripleRow
from triplemodel.config import RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel.embed.strategies import export_nested_triples
from triplemodel.fields.metadata import lang_for_field, literal_datatype_for_field
from triplemodel.namespaces import resolve_predicate
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.predicate_map import predicate_map_for_class
from triplemodel.terms.lang import LangString
from triplemodel.metadata.cardinality import (
    field_cardinality,
    raise_if_inverse_collection,
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
    """Return (subject, predicate, object) tuples for a model instance.

    ``registry`` is accepted for API symmetry with graph writers; literal
    conversion happens when triples are added to a graph (``graph_set_many``).
    """
    _ = registry
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    r = resolver or default_resolver
    prefixes = cfg.prefixes_dict
    subject = uri or cfg.subject_uri(model)
    triples: list[TripleRow] = []

    if cfg.type_uri:
        triples.append((subject, RDF_TYPE, cfg.type_uri))

    for name, predicate in predicate_map_for_class(cls, resolver=r).items():
        if predicate is None:
            continue
        field_info = cls.model_fields[name]
        raise_if_nested_collection(field_info)
        raise_if_inverse_collection(field_info)
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

        if card == "ref":
            if value is None:
                continue
            child_cfg = get_rdf_config(type(value))
            triples.append((subject, predicate, child_cfg.subject_uri(value)))
            continue

        if card == "list":
            continue

        lang = lang_for_field(field_info)
        dt_raw = literal_datatype_for_field(field_info)
        for item in _field_values_for_export(name, value, field_info):
            obj = item
            if lang and isinstance(obj, str):
                obj = LangString(obj, lang)
            elif dt_raw is not None and isinstance(item, int):
                if dt_raw in ("gYear", "xsd:gYear") or dt_raw == str(XSD.gYear):
                    obj = Literal(str(item), datatype=XSD.gYear)
                else:
                    dt_uri = resolve_predicate(dt_raw, prefixes)
                    obj = Literal(str(item), datatype=URIRef(dt_uri))
            triples.append((subject, predicate, obj))

    return triples
