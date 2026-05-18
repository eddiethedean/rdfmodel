"""Edge-case coverage for codegen emit helpers."""

from __future__ import annotations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from triplemodel.codegen.emit import (
    _class_name,
    _field_name,
    _local_name,
    _namespace_for,
    generate_models_from_graph,
)


def test_emit_helpers_local_names():
    assert _local_name("http://ex.org/path#Frag")
    assert _local_name("http://ex.org") == "Resource"
    assert _class_name("http://ex.org/123bad").startswith("C_")
    assert _field_name("http://ex.org/9bad").startswith("f_")
    assert _namespace_for("http://ex.org/path/resource").endswith("/")
    assert _namespace_for("http://ex.org#Type").endswith("#")
    assert _namespace_for("noscheme").endswith("/")


def test_generate_object_property_range():
    g = Graph()
    cls = URIRef("http://example.org/onto#Doc")
    prop = URIRef("http://example.org/onto#relates")
    g.add((cls, RDF.type, OWL.Class))
    g.add((prop, RDF.type, OWL.ObjectProperty))
    g.add((prop, RDFS.domain, cls))
    g.add((prop, RDFS.range, URIRef("http://example.org/onto#Other")))
    source = generate_models_from_graph(g)
    assert "class Doc" in source


def test_generate_skips_non_uri_domain():
    g = Graph()
    cls = URIRef("http://example.org/onto#Item")
    prop = URIRef("http://example.org/onto#title")
    g.add((cls, RDF.type, OWL.Class))
    g.add((prop, RDF.type, OWL.DatatypeProperty))
    g.add((prop, RDFS.domain, Literal("not-uri")))
    source = generate_models_from_graph(g)
    assert "class Item" in source


def test_generate_duplicate_field_names():
    import warnings

    g = Graph()
    cls = URIRef("http://example.org/onto#Item")
    g.add((cls, RDF.type, OWL.Class))
    for uri in (
        "http://example.org/onto#name",
        "http://example.org/other#name",
    ):
        prop = URIRef(uri)
        g.add((prop, RDF.type, OWL.DatatypeProperty))
        g.add((prop, RDFS.domain, cls))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        source = generate_models_from_graph(g)
    assert source.count("name:") == 1
    assert any("duplicate field name" in str(w.message).lower() for w in caught)


def test_emit_class_parent_already_emitted():
    g = Graph()
    parent = URIRef("http://example.org/onto#Animal")
    child = URIRef("http://example.org/onto#Aardvark")
    for node in (parent, child):
        g.add((node, RDF.type, OWL.Class))
    g.add((child, RDFS.subClassOf, parent))
    source = generate_models_from_graph(g)
    assert "class Aardvark" in source


def test_generate_skips_non_uri_property(monkeypatch):
    g = Graph()
    cls = URIRef("http://example.org/onto#Thing")
    g.add((cls, RDF.type, OWL.Class))
    real_subjects = g.subjects

    def subjects(predicate, object):
        if predicate == RDF.type and object == OWL.DatatypeProperty:
            yield URIRef("http://example.org/onto#p")
            yield "not-a-uri"  # type: ignore[misc]
        else:
            yield from real_subjects(predicate, object)

    monkeypatch.setattr(g, "subjects", subjects)
    source = generate_models_from_graph(g)
    assert "class Thing" in source
