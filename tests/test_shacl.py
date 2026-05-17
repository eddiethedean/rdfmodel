"""SHACL validation (optional pyshacl)."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, URIRef

from triplemodel import TripleModel, rdf_field
from triplemodel.config import RDF_TYPE

pyshacl = pytest.importorskip("pyshacl")

EX = "http://example.org/"


class Thing(TripleModel):
    class Rdf:
        namespace = f"{EX}things/"
        type_uri = f"{EX}Thing"
        id_field = "slug"

    slug: str
    label: str = rdf_field(f"{EX}label")


def test_shacl_validate_passes() -> None:
    shapes = Graph()
    shapes.parse(
        data=f"""
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <{EX}> .
        ex:ThingShape a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:label ;
                sh:minCount 1 ;
            ] .
        """,
        format="turtle",
    )
    thing = Thing(slug="t1", label="ok")
    thing.to_graph(shacl_shapes=shapes)


def test_shacl_validate_fails() -> None:
    from triplemodel.validation.shacl import validate_graph

    shapes = Graph()
    shapes.parse(
        data=f"""
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <{EX}> .
        ex:ThingShape a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:label ;
                sh:minCount 1 ;
            ] .
        """,
        format="turtle",
    )
    g = Graph()
    subj = URIRef(f"{EX}things/bad")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{EX}Thing")))
    with pytest.raises(ValueError, match="SHACL"):
        validate_graph(g, shapes)


def test_shacl_validate_graph_from_path_string(tmp_path: Path) -> None:
    from triplemodel.validation.shacl import validate_graph

    shapes_path = tmp_path / "shapes.ttl"
    shapes_path.write_text(
        f"""
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <{EX}> .
        ex:ThingShape a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:label ;
                sh:minCount 1 ;
            ] .
        """,
        encoding="utf-8",
    )
    thing = Thing(slug="ok", label="fine")
    validate_graph(thing.to_graph(), str(shapes_path))


def test_shacl_validate_graph_from_path(tmp_path: Path) -> None:
    from triplemodel.validation.shacl import validate_graph

    shapes_path = tmp_path / "shapes.ttl"
    shapes_path.write_text(
        f"""
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <{EX}> .
        ex:ThingShape a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:label ;
                sh:minCount 1 ;
            ] .
        """,
        encoding="utf-8",
    )
    thing = Thing(slug="ok", label="fine")
    validate_graph(thing.to_graph(), shapes_path)


def test_shacl_import_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(  # type: ignore[no-untyped-def]
        name: str,
        globals=None,
        locals=None,
        fromlist=(),
        level: int = 0,
    ):
        if name == "pyshacl":
            raise ImportError("no pyshacl")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from triplemodel.validation.shacl import validate_graph

    with pytest.raises(ImportError, match="triplemodel\\[shacl\\]"):
        validate_graph(Graph(), Graph())
