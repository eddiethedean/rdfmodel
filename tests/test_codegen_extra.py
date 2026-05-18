"""Extra codegen coverage."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from triplemodel.codegen.emit import generate_models_from_graph
from triplemodel.codegen.parse import ontology_graph


def test_ontology_graph_from_string_data():
    ttl = (
        "@prefix ex: <http://example.org/onto#> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "ex:Thing a owl:Class .\n"
    )
    g = ontology_graph(ttl, format="turtle")
    assert len(g) >= 1


def test_ontology_graph_from_path(tmp_path: Path):
    ttl = "@prefix ex: <http://example.org/onto#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\nex:Thing a owl:Class .\n"
    path = tmp_path / "inline.ttl"
    path.write_text(ttl, encoding="utf-8")
    g = ontology_graph(path)
    assert len(g) >= 1


def test_generate_subclass_and_paths(tmp_path: Path) -> None:
    g = Graph()
    agent = URIRef("http://example.org/onto#Agent")
    person = URIRef("http://example.org/onto#Person")
    g.add((person, RDF.type, OWL.Class))
    g.add((person, RDFS.subClassOf, agent))
    g.add((agent, RDF.type, RDFS.Class))
    prop = URIRef("http://example.org/onto#label")
    g.add((prop, RDF.type, OWL.DatatypeProperty))
    g.add((prop, RDFS.domain, person))
    g.add((prop, RDFS.range, RDFS.Literal))
    source = generate_models_from_graph(g)
    assert "class Person" in source
    assert "class Agent" in source


def test_codegen_cli_writes_file(tmp_path: Path) -> None:
    from triplemodel.codegen.cli import main

    onto = tmp_path / "o.ttl"
    onto.write_text(
        "@prefix ex: <http://example.org/onto#> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "ex:Person a owl:Class .\n",
        encoding="utf-8",
    )
    out = tmp_path / "models.py"
    assert main([str(onto), "-o", str(out)]) == 0
    assert "class Person" in out.read_text(encoding="utf-8")
