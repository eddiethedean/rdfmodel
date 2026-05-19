"""Extra codegen coverage."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.config.constants import OWL, RDF_TYPE, RDFS

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


def test_ontology_graph_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        ontology_graph(tmp_path / "missing.ttl")


def test_ontology_graph_directory_not_file(tmp_path: Path) -> None:
    directory = tmp_path / "onto_dir"
    directory.mkdir()
    with pytest.raises(FileNotFoundError, match="not a file"):
        ontology_graph(directory)


def test_ontology_graph_from_path(tmp_path: Path):
    ttl = "@prefix ex: <http://example.org/onto#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\nex:Thing a owl:Class .\n"
    path = tmp_path / "inline.ttl"
    path.write_text(ttl, encoding="utf-8")
    g = ontology_graph(path)
    assert len(g) >= 1


def test_generate_subclass_and_paths(tmp_path: Path) -> None:
    g = Graph()
    agent = NamedNode("http://example.org/onto#Agent")
    person = NamedNode("http://example.org/onto#Person")
    g.add((person, NamedNode(RDF_TYPE), NamedNode(f"{OWL}Class")))
    g.add((person, NamedNode(f"{RDFS}subClassOf"), agent))
    g.add((agent, NamedNode(RDF_TYPE), NamedNode(f"{RDFS}Class")))
    prop = NamedNode("http://example.org/onto#label")
    g.add((prop, NamedNode(RDF_TYPE), NamedNode(f"{OWL}DatatypeProperty")))
    g.add((prop, NamedNode(f"{RDFS}domain"), person))
    g.add((prop, NamedNode(f"{RDFS}range"), NamedNode(f"{RDFS}Literal")))
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
