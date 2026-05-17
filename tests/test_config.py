"""Tests for RDF configuration helpers."""

from __future__ import annotations

import pytest

import rdfmodel
from rdfmodel import (
    RDFModel,
    id_from_subject_uri,
    rdf_field,
    subject_base,
)
from rdfmodel._config import RdfConfig, get_rdf_config

EX = "http://example.org/people/"


def test_public_package_exports_subject_helpers():
    assert rdfmodel.subject_base is subject_base
    assert rdfmodel.id_from_subject_uri is id_from_subject_uri
    assert "subject_base" in rdfmodel.__all__
    assert "id_from_subject_uri" in rdfmodel.__all__


def test_subject_base_adds_slash():
    assert subject_base("http://example.org/people") == "http://example.org/people/"
    assert subject_base("http://example.org/people#") == "http://example.org/people#"
    assert subject_base("http://example.org/people/") == "http://example.org/people/"


def test_id_from_subject_uri_roundtrip():
    ns = "http://example.org/people"
    assert id_from_subject_uri(ns, "http://example.org/people/alice") == "alice"
    assert id_from_subject_uri(ns, "http://other.example/alice") is None


def test_subject_uri_requires_id_field():
    cfg = RdfConfig(namespace=EX, type_uri="http://example.org/T", id_field=None)

    class Stub:
        slug = "alice"

    with pytest.raises(ValueError, match="id_field"):
        cfg.subject_uri(Stub())


def test_subject_uri_empty_id_field():
    cfg = RdfConfig(namespace=EX, type_uri="http://example.org/T", id_field="slug")

    class Stub:
        slug = ""

    with pytest.raises(ValueError, match="empty"):
        cfg.subject_uri(Stub())


def test_get_rdf_config_without_rdf_class():
    class Bare(RDFModel):
        label: str = rdf_field("http://example.org/label")

    cfg = get_rdf_config(Bare)
    assert cfg.namespace == ""
    assert cfg.type_uri is None
    assert cfg.id_field is None
