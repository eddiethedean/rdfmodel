"""Tests for Dataset and named-graph support (0.5)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from rdflib import Dataset, Graph, Literal, URIRef

from triplemodel import (
    TripleModel,
    get_graph_context,
    is_quad_format,
    load_models,
    load_models_from_dataset,
    models_to_dataset,
    parse_into_dataset,
    rdf_field,
    resolve_graph_iri,
)
from triplemodel.io.dataset import (
    all_from_dataset,
    dump_dataset,
    graph_to_model_from_dataset,
    iter_model_quads,
    quads_in_context,
    sync_to_dataset,
)
from triplemodel.io.dispatch import (
    all_from_dataset_dispatch,
    graph_to_model_dispatch_from_dataset,
)
from triplemodel.vocab import FOAF

PEOPLE_GRAPH = "http://example.org/graph/people"
CATALOG_GRAPH = "http://example.org/graph/catalog"
FOAF_NS = str(FOAF)
DCAT_NS = "http://www.w3.org/ns/dcat#"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        graph_iri = PEOPLE_GRAPH
        prefixes = {"foaf": FOAF_NS}

    slug: str
    name: str = rdf_field("foaf:name")


class Catalog(TripleModel):
    class Rdf:
        namespace = "http://example.org/catalog/"
        type_uri = f"{DCAT_NS}Catalog"
        id_field = "slug"
        graph_iri = CATALOG_GRAPH
        prefixes = {"dcat": DCAT_NS}

    slug: str
    title: str = rdf_field(f"{DCAT_NS}title")


class PlainPerson(TripleModel):
    class Rdf:
        namespace = "http://example.org/plain/"
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF_NS}name")


class PersonWithGraphAlias(TripleModel):
    class Rdf:
        namespace = "http://example.org/alias/"
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        graph = PEOPLE_GRAPH

    slug: str
    name: str = rdf_field(f"{FOAF_NS}name")


class OverridableGraph(TripleModel):
    class Rdf:
        namespace = "http://example.org/override/"
        type_uri = "http://example.org/OverridePerson"
        id_field = "slug"
        graph_iri = PEOPLE_GRAPH

    slug: str
    name: str = rdf_field(f"{FOAF_NS}name")

    def graph_iri(self) -> str:
        return CATALOG_GRAPH


def test_is_quad_format() -> None:
    assert is_quad_format("trig")
    assert is_quad_format("nquads")
    assert not is_quad_format("turtle")


def test_get_rdf_config_graph_iri_and_alias() -> None:
    assert Person.rdf_config().graph_iri == PEOPLE_GRAPH
    assert PersonWithGraphAlias.rdf_config().graph_iri == PEOPLE_GRAPH


def test_resolve_graph_iri_instance_hook() -> None:
    p = OverridableGraph(slug="x", name="X")
    assert resolve_graph_iri(p) == CATALOG_GRAPH


def test_resolve_graph_iri_private_field() -> None:
    class M(TripleModel):
        class Rdf:
            namespace = "http://example.org/p/"
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"
            graph_iri = PEOPLE_GRAPH

        slug: str
        _graph_iri: str | None = CATALOG_GRAPH

    assert resolve_graph_iri(M(slug="a")) == CATALOG_GRAPH


def test_normalize_graph_iri_empty_raises() -> None:
    class Bad(TripleModel):
        class Rdf:
            namespace = "http://example.org/b/"
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"

        slug: str

        def graph_iri(self) -> str:
            return "   "

    with pytest.raises(ValueError, match="non-empty"):
        resolve_graph_iri(Bad(slug="x"))


def test_get_graph_context_plain_graph() -> None:
    g = Graph()
    assert get_graph_context(g, PEOPLE_GRAPH) is g


def test_trig_round_trip_two_graphs(tmp_path: Path) -> None:
    ds = models_to_dataset(
        [
            Person(slug="alice", name="Alice"),
            Catalog(slug="c1", title="Cat"),
        ]
    )
    path = tmp_path / "data.trig"
    dump_dataset(ds, path, format="trig")
    loaded = load_models_from_dataset(parse_into_dataset(path), Person, Catalog)
    people = cast(list[Person], loaded[Person])
    catalogs = cast(list[Catalog], loaded[Catalog])
    assert len(people) == 1
    assert len(catalogs) == 1
    assert people[0].name == "Alice"
    assert catalogs[0].title == "Cat"


@pytest.mark.parametrize("fmt", ["trig", "nquads"])
def test_serialize_parse_round_trip(fmt: str, tmp_path: Path) -> None:
    p = Person(slug="bob", name="Bob")
    path = tmp_path / f"data.{fmt}"
    p.serialize(destination=path, format=fmt)
    loaded = Person.parse_file(path)
    assert loaded[0].name == "Bob"


def test_all_from_dataset_scoped(tmp_path: Path) -> None:
    other = Graph()
    other.add(
        (
            URIRef("http://example.org/people/eve"),
            URIRef(f"{FOAF_NS}name"),
            Literal("Eve"),
        )
    )
    other.add(
        (
            URIRef("http://example.org/people/eve"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{FOAF_NS}Person"),
        )
    )
    ds = models_to_dataset([Person(slug="alice", name="Alice")])
    for t in other:
        ds.default_graph.add(t)
    people = Person.all_from_dataset(ds)
    assert len(people) == 1
    assert people[0].slug == "alice"


def test_from_dataset_and_to_dataset() -> None:
    p = Person(slug="a", name="A")
    ds = p.to_dataset()
    restored = Person.from_dataset(ds, p.subject_uri())
    assert restored.name == "A"


def test_sync_to_dataset_replace(tmp_path: Path) -> None:
    p = Person(slug="a", name="A")
    ds = p.to_dataset()
    ctx = get_graph_context(ds, PEOPLE_GRAPH)
    p.name = "B"
    sync_to_dataset(p, ds, mode="replace")
    obj = list(ctx.objects(URIRef(p.subject_uri()), URIRef(f"{FOAF_NS}name")))[0]
    assert str(obj) == "B"


def test_models_to_dataset_groups_graphs() -> None:
    ds = models_to_dataset(
        [
            Person(slug="a", name="A"),
            Catalog(slug="c", title="C"),
        ]
    )
    graph_ids = {str(g.identifier) for g in ds.graphs()}
    assert PEOPLE_GRAPH in graph_ids
    assert CATALOG_GRAPH in graph_ids


def test_load_models_trig_multi_class(tmp_path: Path) -> None:
    ds = models_to_dataset(
        [
            Person(slug="a", name="A"),
            Catalog(slug="c", title="C"),
        ]
    )
    path = tmp_path / "multi.trig"
    dump_dataset(ds, path, format="trig")
    bundles = load_models(path, Person, Catalog)
    assert len(bundles[Person]) == 1
    assert len(bundles[Catalog]) == 1


def test_parse_uses_dataset_when_graph_iri_set(tmp_path: Path) -> None:
    path = tmp_path / "p.trig"
    Person(slug="a", name="A").serialize(destination=path, format="trig")
    loaded = Person.parse_file(path)
    assert loaded[0].slug == "a"


def test_plain_parse_trig_without_graph_iri(tmp_path: Path) -> None:
    path = tmp_path / "plain.trig"
    PlainPerson(slug="a", name="A").serialize(destination=path, format="turtle")
    loaded = PlainPerson.parse_file(path)
    assert loaded[0].name == "A"


def test_iter_model_quads() -> None:
    p = Person(slug="a", name="A")
    rows = list(iter_model_quads(p))
    assert rows
    assert rows[0][3] == PEOPLE_GRAPH


def test_quads_in_context() -> None:
    ds = Person(slug="a", name="A").to_dataset()
    quads = list(quads_in_context(ds, PEOPLE_GRAPH))
    assert quads


def test_dispatch_from_dataset() -> None:
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(Person)
    ds = models_to_dataset(
        [
            Person(slug="a", name="A"),
            Catalog(slug="c", title="C"),
        ]
    )
    p = graph_to_model_dispatch_from_dataset(ds, "http://example.org/people/a")
    assert isinstance(p, Person)
    all_models = all_from_dataset_dispatch(ds)
    assert len(all_models) == 2


def test_all_from_dataset_dispatch_model_classes_filter() -> None:
    ds = models_to_dataset(
        [
            Person(slug="a", name="A"),
            Catalog(slug="c", title="C"),
        ]
    )
    only_people = all_from_dataset_dispatch(ds, model_classes=[Person])
    assert len(only_people) == 1
    assert isinstance(only_people[0], Person)


def test_all_from_dataset_dispatch_model_classes_type_error() -> None:
    with pytest.raises(TypeError, match="TripleModel"):
        all_from_dataset_dispatch(Dataset(), model_classes=[object])  # ty: ignore[list-item]


def test_dispatch_from_dataset_prefers_class_graph_context() -> None:
    from triplemodel.config import RDF_TYPE
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(PlainPerson)
    uri = URIRef("http://example.org/plain/ambiguous")
    ds = Dataset()
    people_ctx = get_graph_context(ds, PEOPLE_GRAPH)
    default_ctx = get_graph_context(ds, None)
    for ctx in (people_ctx, default_ctx):
        ctx.add((uri, URIRef(RDF_TYPE), URIRef(f"{FOAF_NS}Person")))
        ctx.add((uri, URIRef(f"{FOAF_NS}name"), Literal("Plain")))
    m = graph_to_model_dispatch_from_dataset(ds, uri)
    assert isinstance(m, PlainPerson)
    assert m.name == "Plain"


def test_dispatch_from_dataset_ambiguous_graph_raises() -> None:
    from triplemodel.config import RDF_TYPE
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(Catalog)
    uri = URIRef("http://example.org/catalog/ambiguous")
    ds = Dataset()
    people_ctx = get_graph_context(ds, PEOPLE_GRAPH)
    default_ctx = get_graph_context(ds, None)
    for ctx in (people_ctx, default_ctx):
        ctx.add((uri, URIRef(RDF_TYPE), URIRef(f"{DCAT_NS}Catalog")))
        ctx.add((uri, URIRef(f"{DCAT_NS}title"), Literal("X")))
    with pytest.raises(ValueError, match="multiple dataset graphs"):
        graph_to_model_dispatch_from_dataset(ds, uri)


def test_graph_to_model_from_dataset() -> None:
    ds = Person(slug="a", name="A").to_dataset()
    m = graph_to_model_from_dataset(ds, Person, "http://example.org/people/a")
    assert m.name == "A"


def test_all_from_dataset_helper() -> None:
    ds = Person(slug="a", name="A").to_dataset()
    items = all_from_dataset(ds, Person)
    assert len(items) == 1


def test_load_dataset_alias() -> None:
    from triplemodel import load_dataset

    ds = load_dataset(data="@prefix foaf: <{}> .".format(FOAF_NS), format="turtle")
    assert isinstance(ds, Dataset)


def test_dispatch_missing_subject_raises() -> None:
    ds = Dataset()
    with pytest.raises(ValueError, match="No registered"):
        graph_to_model_dispatch_from_dataset(ds, "http://example.org/missing")


def test_parse_into_dataset_requires_source() -> None:
    with pytest.raises(ValueError, match="requires source"):
        parse_into_dataset()


def test_load_models_from_dataset_type_error() -> None:
    with pytest.raises(TypeError, match="TripleModel"):
        load_models_from_dataset(Dataset(), object)  # ty: ignore[invalid-argument-type]


def test_quads_in_context_default_graph() -> None:
    p = PlainPerson(slug="a", name="A")
    ds = p.to_dataset()
    assert list(quads_in_context(ds, None))


def test_sync_to_dataset_instance_method() -> None:
    p = Person(slug="a", name="A")
    ds = p.to_dataset()
    p.name = "Z"
    p.sync_to_dataset(ds, mode="replace")
    ctx = get_graph_context(ds, PEOPLE_GRAPH)
    assert (
        str(list(ctx.objects(URIRef(p.subject_uri()), URIRef(f"{FOAF_NS}name")))[0])
        == "Z"
    )


def test_to_dataset_shacl(tmp_path: Path) -> None:
    from rdflib import Graph as RdfGraph

    p = Person(slug="a", name="A")
    shape = RdfGraph()
    p.to_dataset(shacl_shapes=shape)


def test_parse_dispatch_from_dataset(tmp_path: Path) -> None:
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(Person)
    register_rdf_resource(Catalog)
    path = tmp_path / "both.trig"
    dump_dataset(
        models_to_dataset([Person(slug="a", name="A"), Catalog(slug="c", title="T")]),
        path,
        format="trig",
    )
    loaded = Person.parse_file(path, dispatch=True)
    assert any(isinstance(m, Person) for m in loaded)


def test_parse_url_into_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    from triplemodel.io import dataset as dataset_mod

    trig = (
        f"GRAPH <{PEOPLE_GRAPH}> {{\n"
        f"  @prefix foaf: <{FOAF_NS}> .\n"
        f'  <http://example.org/people/a> a foaf:Person ; foaf:name "Ann" .\n'
        f"}}\n"
    )
    monkeypatch.setattr(
        dataset_mod, "fetch_url", lambda url, timeout=30.0: trig.encode()
    )

    loaded = Person.parse_url("http://example.org/data.trig", format="trig")
    assert loaded[0].name == "Ann"


def test_parse_url_dataset_path(monkeypatch: pytest.MonkeyPatch) -> None:
    from triplemodel.io import dataset as dataset_mod

    trig = (
        f"GRAPH <{PEOPLE_GRAPH}> {{\n"
        f"  @prefix foaf: <{FOAF_NS}> .\n"
        f'  <http://example.org/people/u> a foaf:Person ; foaf:name "U" .\n'
        f"}}\n"
    )
    monkeypatch.setattr(
        dataset_mod, "fetch_url", lambda url, timeout=30.0: trig.encode()
    )
    loaded = Person.parse_url("http://example.org/data.trig", format="trig")
    assert loaded[0].name == "U"


def test_get_rdf_config_graph_iri_in_config() -> None:
    assert Catalog.rdf_config().graph_iri == CATALOG_GRAPH
