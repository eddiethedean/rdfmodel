"""Tests for OWL/RDFS codegen."""

from __future__ import annotations

from pathlib import Path

from triplemodel.codegen import generate_models_from_graph, ontology_graph

ONTOLOGY = """\
@prefix ex: <http://example.org/onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Person a owl:Class .
ex:name a owl:DatatypeProperty ;
    rdfs:domain ex:Person ;
    rdfs:range rdfs:Literal .
"""


def test_generate_models_from_ttl(tmp_path: Path) -> None:
    path = tmp_path / "onto.ttl"
    path.write_text(ONTOLOGY, encoding="utf-8")
    graph = ontology_graph(path)
    source = generate_models_from_graph(graph)
    assert "class Person" in source
    assert "rdf_field" in source
    assert "http://example.org/onto#Person" in source
