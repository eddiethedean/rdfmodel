"""Tests for RDF configuration helpers."""

from __future__ import annotations

import pytest
from pyoxigraph import NamedNode

import triplemodel
from triplemodel import (
    TripleModel,
    id_from_subject_uri,
    rdf_field,
    subject_base,
)
from triplemodel.config import RdfConfig, get_rdf_config, resolve_graph_iri
from triplemodel.config.rdf_config import _normalize_graph_iri

EX = "http://example.org/people/"


def test_public_package_exports_subject_helpers():
    assert triplemodel.subject_base is subject_base
    assert triplemodel.id_from_subject_uri is id_from_subject_uri
    assert "subject_base" in triplemodel.__all__
    assert "id_from_subject_uri" in triplemodel.__all__
    assert "IriId" in triplemodel.__all__


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
    class Bare(TripleModel):
        label: str = rdf_field("http://example.org/label")

    cfg = get_rdf_config(Bare)
    assert cfg.namespace == ""
    assert cfg.type_uri is None
    assert cfg.id_field is None


def test_get_rdf_config_inherits_from_base():
    FOAF = "http://xmlns.com/foaf/0.1/"

    class Base(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

    class Employee(Base):
        slug: str
        name: str = rdf_field(f"{FOAF}name")

    cfg = get_rdf_config(Employee)
    assert cfg.namespace == EX
    assert cfg.type_uri == f"{FOAF}Person"
    assert cfg.id_field == "slug"


def test_subject_uri_accepts_zero_and_false_id_values():
    FOAF = "http://xmlns.com/foaf/0.1/"

    class Counter(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: int | bool
        name: str = rdf_field(f"{FOAF}name")

    zero = Counter(slug=0, name="Zero")
    assert zero.subject_uri().endswith("/0")
    assert Counter.from_graph(zero.to_graph(), zero.subject_uri()) == zero

    flag = Counter(slug=False, name="Flag")
    assert flag.subject_uri().endswith("/False")
    assert Counter.from_graph(flag.to_graph(), flag.subject_uri()) == flag


def test_falsy_type_uri_omits_rdf_type_on_export():
    class Untyped(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = ""
            id_field = "slug"

        slug: str
        name: str = rdf_field("http://xmlns.com/foaf/0.1/name")

    g = Untyped(slug="a", name="A").to_graph()
    subj = NamedNode(EX + "a")
    assert (
        list(
            g.objects(
                subj, NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
            )
        )
        == []
    )


def test_iter_model_resource_classes() -> None:
    from triplemodel.protocols import iter_model_resource_classes

    classes = iter_model_resource_classes()
    assert TripleModel in classes or any(issubclass(c, TripleModel) for c in classes)


def test_normalize_graph_iri_none() -> None:
    assert _normalize_graph_iri(None) is None


def test_get_rdf_config_empty_graph_iri_becomes_none() -> None:
    class EmptyGraph(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = "http://xmlns.com/foaf/0.1/Person"
            id_field = "slug"
            graph_iri = ""

        slug: str

    assert get_rdf_config(EmptyGraph).graph_iri is None


def test_resolve_graph_iri_method_returns_none_falls_back() -> None:
    class WithHook(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = "http://xmlns.com/foaf/0.1/Person"
            id_field = "slug"
            graph_iri = "http://example.org/graph/g1"

        slug: str

        def graph_iri(self) -> None:
            return None

    assert resolve_graph_iri(WithHook(slug="a")) == "http://example.org/graph/g1"


def test_get_rdf_config_reads_graph_iri() -> None:
    class InGraph(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = "http://xmlns.com/foaf/0.1/Person"
            id_field = "slug"
            graph_iri = "http://example.org/graph/g1"

        slug: str

    cfg = get_rdf_config(InGraph)
    assert cfg.graph_iri == "http://example.org/graph/g1"


def test_id_from_subject_uri_returns_multi_segment_suffix():
    ns = "http://example.org/people"
    uri = "http://example.org/people/alice/extra"
    assert id_from_subject_uri(ns, uri) == "alice/extra"
