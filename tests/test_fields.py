"""Tests for field helpers and predicate resolution."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from rdfmodel import Predicate, rdf_field
from rdfmodel._fields import (
    predicate_for_field,
    predicate_from_annotation,
)


def test_rdf_field_non_dict_json_schema_extra():
    field = rdf_field("http://example.org/name", json_schema_extra="ignored")
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
