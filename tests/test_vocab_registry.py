"""Tests for VocabularyRegistry."""

from __future__ import annotations

from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.vocab_registry import VocabularyRegistry

EX = "http://example.org/"


class Alpha(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Alpha"
        id_field = "slug"
        prefixes = {"ex": EX}

    slug: str
    name: str = rdf_field("ex:name")


class Beta(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Beta"
        id_field = "slug"
        prefixes = {"ex": EX}

    slug: str


def test_registry_register_and_lookup():
    reg = VocabularyRegistry()
    reg.register(Alpha)
    reg.register(Beta)
    assert reg.model_for_type_uri(f"{EX}Alpha") is Alpha
    assert "ex" in reg.prefix_to_uri


def test_registry_model_for_subject():
    reg = VocabularyRegistry()
    reg.register(Alpha)
    g = Graph()
    s = NamedNode(f"{EX}a")
    g.add((s, NamedNode(RDF_TYPE), NamedNode(f"{EX}Alpha")))
    cls = reg.model_for_subject(g, s)
    assert cls is Alpha


def test_from_registered():
    reg = VocabularyRegistry.from_registered()
    assert reg.model_for_type_uri(f"{EX}Alpha") is Alpha
