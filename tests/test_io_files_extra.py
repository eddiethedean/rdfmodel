"""Additional coverage for io/files and parse helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, infer_format, rdf_field
from triplemodel.io.files import (
    dump_graph,
    dump_model,
    fetch_url,
    load_models,
    merge_jsonld_kwargs,
    parse_into_graph,
    parse_url_into_graph,
)
from triplemodel.io.dispatch import graph_to_model_dispatch
from triplemodel.protocols import resolve_model_class
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Mini(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}

    slug: str
    name: str = rdf_field("foaf:name")


def test_parse_into_graph_requires_source_or_data() -> None:
    with pytest.raises(ValueError, match="source= or data="):
        parse_into_graph()


def test_infer_format_media_type() -> None:
    assert infer_format("text/turtle", None) == "turtle"


def test_infer_format_requires_hint_without_explicit() -> None:
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_format(None, None)


def test_dump_model_and_load_models(tmp_path: Path) -> None:
    m = Mini(slug="a", name="A")
    path = tmp_path / "a.ttl"
    dump_model(m, path)
    loaded = load_models(path, Mini)
    assert loaded[0].slug == "a"


def test_load_models_type_error() -> None:
    class NotModel(BaseModel):
        pass

    with pytest.raises(TypeError, match="TripleModel"):
        load_models("x.ttl", NotModel)


def test_dump_model_type_error() -> None:
    class NotModel(BaseModel):
        pass

    with pytest.raises(TypeError, match="TripleModel"):
        dump_model(NotModel(), "x.ttl")


def test_fetch_url() -> None:
    with patch("triplemodel.io.files.urlopen") as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = (
            b"@prefix ex: <http://ex/> ."
        )
        body = fetch_url("http://example.org/data.ttl")
        assert b"prefix" in body


def test_parse_url_into_graph() -> None:
    ttl = f'<{EX}a> a <{FOAF_NS}Person> ; <{FOAF_NS}name> "A" .'
    with patch("triplemodel.io.files.fetch_url", return_value=ttl.encode()):
        g = parse_url_into_graph("http://example.org/a.ttl")
        assert len(g) >= 1


def test_dump_graph_returns_string() -> None:
    g = Graph()
    text = dump_graph(g, format="turtle")
    assert isinstance(text, str)


def test_resolve_model_class_unknown() -> None:
    g = Graph()
    from pyoxigraph import NamedNode

    with pytest.raises(ValueError, match="No registered"):
        resolve_model_class(g, NamedNode(f"{EX}unknown"))


def test_graph_to_model_dispatch() -> None:
    m = Mini(slug="d", name="D")
    g = m.to_graph()
    from triplemodel.model import TripleModel as TM

    loaded = graph_to_model_dispatch(g, NamedNode(m.subject_uri()))
    assert isinstance(loaded, TM)
    assert getattr(loaded, "slug") == "d"


def test_merge_jsonld_noop() -> None:
    assert merge_jsonld_kwargs("turtle", {"x": 1}, {}) == {}


def test_person_parse_url() -> None:
    ttl = f'<{EX}a> a <{FOAF_NS}Person> ; <{FOAF_NS}name> "A" .'
    with patch("triplemodel.io.files.fetch_url", return_value=ttl.encode()):
        loaded = Mini.parse_url("http://example.org/a.ttl")
    assert loaded[0].slug == "a"


def test_person_serialize_with_shacl(tmp_path: Path) -> None:
    pyshacl = pytest.importorskip("pyshacl")
    _ = pyshacl
    shapes = f"""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix foaf: <{FOAF_NS}> .
@prefix ex: <http://example.org/> .
ex:Shape a sh:NodeShape ;
    sh:targetClass foaf:Person ;
    sh:property [ sh:path foaf:name ; sh:minCount 1 ] .
"""
    m = Mini(slug="s", name="S")
    text = m.serialize(format="turtle", shacl_shapes=shapes)
    assert "S" in str(text)
