"""Tests for class-definition predicate IRI validation."""

from __future__ import annotations

import warnings

import pytest

from triplemodel import TripleModel, rdf_field


def test_invalid_predicate_namespace_only_raises() -> None:
    with pytest.raises(ValueError, match="no local name"):

        class Bad(TripleModel):
            class Rdf:
                namespace = "http://example.org/"
                type_uri = "http://example.org/Type"
                id_field = "slug"
                prefixes = {"rdfs": "http://www.w3.org/2000/01/rdf-schema#"}

            slug: str
            name: str = rdf_field("http://www.w3.org/2000/01/rdf-schema#")


def test_valid_predicate_passes() -> None:
    class Good(TripleModel):
        class Rdf:
            namespace = "http://example.org/"
            type_uri = "http://example.org/Type"
            id_field = "slug"
            prefixes = {"rdfs": "http://www.w3.org/2000/01/rdf-schema#"}

        slug: str
        name: str = rdf_field("rdfs:label")

    assert Good.model_fields["name"].json_schema_extra is not None


def test_predicate_equals_prefix_namespace_warns() -> None:
    pred = "http://ex.org/pred"

    with warnings.catch_warnings(record=True) as caught:

        class Warn(TripleModel):
            class Rdf:
                namespace = "http://example.org/"
                type_uri = "http://example.org/Type"
                id_field = "slug"
                prefixes = {"p": pred}

            slug: str
            name: str = rdf_field(pred)

        assert any(
            issubclass(w.category, UserWarning) and "equals" in str(w.message)
            for w in caught
        )
