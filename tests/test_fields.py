"""Tests for field helpers and predicate resolution."""

from __future__ import annotations

from typing import Annotated, Any, cast

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from triplemodel import Predicate, rdf_field
from triplemodel import IriId, TripleModel
from triplemodel.fields import (
    annotation_has_iri_id,
    id_field_is_iri_id,
    predicate_for_field,
    predicate_from_annotation,
)


def test_rdf_field_non_dict_json_schema_extra():
    field = rdf_field(
        "http://example.org/name",
        json_schema_extra=cast(Any, "ignored"),
    )
    info = field
    assert isinstance(info, FieldInfo)
    assert info.json_schema_extra == {"rdf_predicate": "http://example.org/name"}


def test_predicate_for_field_from_json_schema_extra():
    info = rdf_field("http://example.org/name")
    assert predicate_for_field(info) == "http://example.org/name"


def test_predicate_for_field_from_metadata():
    class MetaModel(BaseModel):
        label: Annotated[str, Predicate("http://example.org/from-meta")]

    info = MetaModel.model_fields["label"]
    assert predicate_for_field(info) == "http://example.org/from-meta"


def test_predicate_for_field_returns_none():
    info = Field()
    assert predicate_for_field(info) is None


def test_predicate_from_annotation_non_annotated():
    assert predicate_from_annotation(str) is None


def test_predicate_from_annotation_without_predicate():
    assert predicate_from_annotation(Annotated[str, "meta"]) is None


def test_predicate_from_annotation_with_predicate():
    ann = Annotated[str, Predicate("http://example.org/pred")]
    assert predicate_from_annotation(ann) == "http://example.org/pred"


def test_iri_id_annotation_detection():
    ann = Annotated[str, IriId()]
    assert annotation_has_iri_id(ann) is True
    assert annotation_has_iri_id(str) is False


def test_id_field_is_iri_id_on_model():
    class Resource(TripleModel):
        class Rdf:
            namespace = "http://example.org/"
            id_field = "uri"

        uri: Annotated[str, IriId()]
        label: str = rdf_field("http://example.org/label")

    assert id_field_is_iri_id(Resource, "uri") is True
    assert id_field_is_iri_id(Resource, "label") is False
    assert id_field_is_iri_id(Resource, "missing") is False


def test_id_field_is_iri_id_from_field_metadata_only():
    class M(BaseModel):
        uri: str

    field_info = M.model_fields["uri"]
    object.__setattr__(field_info, "annotation", str)
    object.__setattr__(field_info, "metadata", [IriId()])
    assert id_field_is_iri_id(M, "uri") is True
