"""Tests for file parse/serialize (0.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from triplemodel import (
    TripleModel,
    infer_format,
    load_models,
    parse_into_graph,
    rdf_field,
)
from triplemodel.io.files import merge_jsonld_kwargs
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)


@pytest.fixture
def person() -> Person:
    return Person(slug="alice", name="Alice", nick=["a1", "a2"])


FORMATS = [
    "turtle",
    "xml",
    "n3",
    "nt",
    "hext",
]


@pytest.mark.parametrize("fmt", FORMATS)
def test_round_trip_formats(person: Person, fmt: str, tmp_path: Path) -> None:
    serialized = person.serialize(format=fmt)
    assert serialized
    loaded = Person.parse(data=serialized, format=fmt)
    assert len(loaded) == 1
    assert loaded[0].slug == person.slug
    assert loaded[0].name == person.name
    assert loaded[0].nick == person.nick


def test_infer_format_from_suffix() -> None:
    assert infer_format("data.ttl", None) == "turtle"
    assert infer_format("data.trig", None) == "trig"
    assert infer_format(None, "xml") == "xml"


def test_infer_format_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_format("file.xyz", None)


def test_parse_file_autodetect(person: Person, tmp_path: Path) -> None:
    path = tmp_path / "alice.ttl"
    person.serialize(destination=path)
    loaded = Person.parse_file(path)
    assert loaded[0].name == "Alice"


def test_load_models_alias(person: Person, tmp_path: Path) -> None:
    path = tmp_path / "alice.ttl"
    person.serialize(destination=path)
    loaded = load_models(path, Person)
    assert loaded[0].slug == "alice"


def test_base_uri_relative_import(tmp_path: Path) -> None:
    class RelPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"
            base_uri = EX
            prefixes = {"foaf": FOAF_NS}

        slug: str
        name: str = rdf_field(f"{FOAF_NS}name")

    ttl = f'@base <{EX}> .\n<alice> a <{FOAF_NS}Person> ; <{FOAF_NS}name> "Alice" .'
    graph = parse_into_graph(data=ttl, format="turtle", base=EX)
    loaded = RelPerson.all_from_graph(graph)
    assert len(loaded) == 1
    assert loaded[0].name == "Alice"


def test_merge_jsonld_context() -> None:
    ctx = {"name": "http://xmlns.com/foaf/0.1/name"}
    merged = merge_jsonld_kwargs("json-ld", ctx, {})
    assert merged["context"] == ctx
    merged2 = merge_jsonld_kwargs("json-ld", ctx, {"context": {"x": 1}})
    assert merged2["context"] == {"x": 1}


@pytest.mark.parametrize("fmt", ["turtle", "json-ld"])
def test_jsonld_round_trip_if_supported(person: Person, fmt: str) -> None:
    try:
        serialized = person.serialize(format=fmt)
    except Exception:
        pytest.skip(f"rdflib does not support serialize format {fmt!r}")
    try:
        loaded = Person.parse(data=serialized, format=fmt)
    except Exception:
        pytest.skip(f"rdflib does not support parse format {fmt!r}")
    assert loaded[0].name == person.name


def test_parse_into_graph_data_bytes() -> None:
    ttl = f"<{EX}alice> a <{FOAF_NS}Person> ."
    g = parse_into_graph(data=ttl.encode(), format="turtle")
    assert len(g) == 1
