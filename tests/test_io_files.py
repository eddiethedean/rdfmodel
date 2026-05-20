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

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
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
]

UNSUPPORTED_FORMATS = ["hext", "longturtle", "trix"]


@pytest.mark.parametrize("fmt", FORMATS)
def test_round_trip_formats(person: Person, fmt: str, tmp_path: Path) -> None:
    serialized = person.serialize(format=fmt)
    assert serialized
    loaded = Person.parse(data=serialized, format=fmt)
    assert len(loaded) == 1
    assert loaded[0].slug == person.slug
    assert loaded[0].name == person.name
    assert loaded[0].nick == person.nick


@pytest.mark.parametrize("fmt", UNSUPPORTED_FORMATS)
def test_unsupported_formats_raise(person: Person, fmt: str) -> None:
    with pytest.raises(ValueError, match="not supported by pyoxigraph"):
        person.serialize(format=fmt)


def test_infer_format_from_suffix() -> None:
    assert infer_format("data.ttl", None) == "turtle"
    assert infer_format("data.trig", None) == "trig"
    assert infer_format(None, "xml") == "xml"


def test_infer_format_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_format("file.xyz", None)


@pytest.mark.parametrize(
    "hint",
    [
        "data.hext",
        "data.trix",
        "application/hextuples",
        pytest.param("hext", id="explicit-hext"),
    ],
)
def test_infer_format_removed_formats_raise(hint: str) -> None:
    with pytest.raises(ValueError, match="not supported by pyoxigraph"):
        infer_format(hint, "hext" if hint == "hext" else None)


def test_parse_file_removed_suffix_raises(person: Person, tmp_path: Path) -> None:
    path = tmp_path / "alice.hext"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="not supported by pyoxigraph"):
        Person.parse_file(path)


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
            type_uri = module_type_uri("Person_2")
            id_field = "slug"
            base_uri = EX
            prefixes = {"foaf": FOAF_NS}

        slug: str
        name: str = rdf_field(f"{FOAF_NS}name")

    rel_type = module_type_uri("Person_2")
    ttl = f'@base <{EX}> .\n<alice> a <{rel_type}> ; <{FOAF_NS}name> "Alice" .'
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
        pytest.skip(f"format {fmt!r} not supported for serialize")  # ty: ignore
    try:
        loaded = Person.parse(data=serialized, format=fmt)
    except Exception:
        pytest.skip(f"format {fmt!r} not supported for parse")  # ty: ignore
    assert loaded[0].name == person.name


def test_parse_into_graph_data_bytes() -> None:
    ttl = f"<{EX}alice> a <{FOAF_NS}Person> ."
    g = parse_into_graph(data=ttl.encode(), format="turtle")
    assert len(g) == 1
