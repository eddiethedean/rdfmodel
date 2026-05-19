"""Edge-case coverage for codegen emit helpers."""

from __future__ import annotations

from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.config.constants import OWL, RDF, RDFS

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
    cls = NamedNode("http://example.org/onto#Doc")
    prop = NamedNode("http://example.org/onto#relates")
    g.add((cls, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}Class")))
    g.add((prop, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}ObjectProperty")))
    g.add((prop, NamedNode(f"{RDFS}domain"), cls))
    g.add((prop, NamedNode(f"{RDFS}range"), NamedNode("http://example.org/onto#Other")))
    source = generate_models_from_graph(g)
    assert "class Doc" in source


def test_generate_skips_non_uri_domain():
    g = Graph()
    cls = NamedNode("http://example.org/onto#Item")
    prop = NamedNode("http://example.org/onto#title")
    g.add((cls, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}Class")))
    g.add((prop, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}DatatypeProperty")))
    g.add((prop, NamedNode(f"{RDFS}domain"), Literal("not-uri")))
    source = generate_models_from_graph(g)
    assert "class Item" in source


def test_generate_duplicate_field_names():
    import warnings

    g = Graph()
    cls = NamedNode("http://example.org/onto#Item")
    g.add((cls, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}Class")))
    for uri in (
        "http://example.org/onto#name",
        "http://example.org/other#name",
    ):
        prop = NamedNode(uri)
        g.add((prop, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}DatatypeProperty")))
        g.add((prop, NamedNode(f"{RDFS}domain"), cls))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        source = generate_models_from_graph(g)
    assert source.count("name:") == 1
    assert any("duplicate field name" in str(w.message).lower() for w in caught)


def test_emit_class_parent_already_emitted():
    g = Graph()
    parent = NamedNode("http://example.org/onto#Animal")
    child = NamedNode("http://example.org/onto#Aardvark")
    for node in (parent, child):
        g.add((node, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}Class")))
    g.add((child, NamedNode(f"{RDFS}subClassOf"), parent))
    source = generate_models_from_graph(g)
    assert "class Aardvark" in source


def test_generate_skips_non_uri_property():
    g = Graph()
    cls = NamedNode("http://example.org/onto#Thing")
    g.add((cls, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}Class")))
    source = generate_models_from_graph(g)
    assert "class Thing" in source
