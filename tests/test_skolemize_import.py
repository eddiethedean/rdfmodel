"""Tests that de_skolemize runs once per top-level import path."""

from __future__ import annotations

import pytest
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.config.constants import RDFS

from triplemodel import TripleModel, hydrate_refs, rdf_field, ref_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.dispatch import all_from_graph_dispatch
from triplemodel.io.import_ import graph_to_model
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/skolem/"


class SkolemCountry(TripleModel):
    class Rdf:
        namespace = f"{EX}country/"
        type_uri = f"{EX}Country"
        id_field = "code"
        skolemize_import = True

    code: str
    label: str = rdf_field(f"{EX}label")


class SkolemCity(TripleModel):
    class Rdf:
        namespace = f"{EX}city/"
        type_uri = f"{EX}City"
        id_field = "code"
        skolemize_import = True
        prefixes = {"foaf": FOAF_NS}

    code: str
    name: str = rdf_field("foaf:name")
    country: SkolemCountry = ref_field(f"{EX}inCountry", model=SkolemCountry)


def test_nested_ref_import_de_skolemize_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def track(graph, *, de_skolemize: bool = False):
        calls.append(de_skolemize)
        return graph

    monkeypatch.setattr("triplemodel.io.skolem.apply_de_skolemize", track)

    g = Graph()
    fr = NamedNode(f"{EX}country/fr")
    paris = NamedNode(f"{EX}city/paris")
    g.add((fr, NamedNode(RDF_TYPE), NamedNode(f"{EX}Country")))
    g.add((fr, NamedNode(f"{EX}label"), Literal("France")))
    g.add((paris, NamedNode(RDF_TYPE), NamedNode(f"{EX}City")))
    g.add((paris, NamedNode(f"{EX}inCountry"), fr))
    g.add((paris, NamedNode(f"{FOAF_NS}name"), Literal("Paris")))

    graph_to_model(
        g,
        SkolemCity,
        paris,
        config=SkolemCity.rdf_config(),
    )
    assert calls[0] is True
    assert all(flag is False for flag in calls[1:])


def test_hydrate_refs_de_skolemize_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def track(graph, *, de_skolemize: bool = False):
        calls.append(de_skolemize)
        return graph

    monkeypatch.setattr("triplemodel.io.skolem.apply_de_skolemize", track)

    g = Graph()
    fr = NamedNode(f"{EX}country/fr")
    paris = NamedNode(f"{EX}city/paris")
    london = NamedNode(f"{EX}city/london")
    for city_uri, name in ((paris, "Paris"), (london, "London")):
        g.add((city_uri, NamedNode(RDF_TYPE), NamedNode(f"{EX}City")))
        g.add((city_uri, NamedNode(f"{FOAF_NS}name"), Literal(name)))
        g.add((city_uri, NamedNode(f"{EX}inCountry"), fr))
    g.add((fr, NamedNode(RDF_TYPE), NamedNode(f"{EX}Country")))
    g.add((fr, NamedNode(f"{EX}label"), Literal("France")))

    cities = [
        SkolemCity(
            code="paris", name="Paris", country=SkolemCountry(code="fr", label="")
        ),
        SkolemCity(
            code="london", name="London", country=SkolemCountry(code="fr", label="")
        ),
    ]
    hydrate_refs(cities, g, "country")
    assert calls[0] is True
    assert all(flag is False for flag in calls[1:])


def test_all_from_graph_dispatch_de_skolemize_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[bool] = []

    def track(graph, *, de_skolemize: bool = False):
        calls.append(de_skolemize)
        return graph

    monkeypatch.setattr("triplemodel.io.skolem.apply_de_skolemize", track)

    class SkolemPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"
            skolemize_import = True
            prefixes = {"foaf": FOAF_NS}

        slug: str
        name: str = rdf_field("foaf:name")

    g = Graph()
    for slug, name in (("a", "A"), ("b", "B")):
        subj = NamedNode(f"{EX}{slug}")
        g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{FOAF_NS}Person")))
        g.add((subj, NamedNode(f"{FOAF_NS}name"), Literal(name)))

    all_from_graph_dispatch(g)
    assert calls[0] is True
    assert all(flag is False for flag in calls[1:])


def test_all_from_graph_dispatch_explicit_de_skolemize_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[bool] = []

    def track(graph, *, de_skolemize: bool = False):
        calls.append(de_skolemize)
        return graph

    monkeypatch.setattr("triplemodel.io.skolem.apply_de_skolemize", track)

    g = Graph()
    subj = NamedNode(f"{EX}only")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{FOAF_NS}Person")))
    g.add((subj, NamedNode(f"{FOAF_NS}name"), Literal("Only")))

    class One(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"
            skolemize_import = True
            prefixes = {"foaf": FOAF_NS}

        slug: str
        name: str = rdf_field("foaf:name")

    all_from_graph_dispatch(g, de_skolemize=False)
    assert calls and all(flag is False for flag in calls)


def test_resolve_model_class_skips_missing_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import patch

    from triplemodel.protocols import resolve_model_class

    g = Graph()
    alice = NamedNode(f"{EX}alice")
    g.add((alice, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))

    with (
        patch(
            "triplemodel.protocols.iter_registered_type_uris",
            return_value=frozenset({f"{EX}Person"}),
        ),
        patch(
            "triplemodel.protocols.model_class_for_type_uri",
            return_value=None,
        ),
    ):
        with pytest.raises(ValueError, match="No registered"):
            resolve_model_class(g, alice)


def test_all_from_graph_dispatch_finds_subclass_typed_subject() -> None:
    class Base(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Base"
            id_field = "slug"

        slug: str

    class Worker(Base):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Worker"
            id_field = "slug"

        slug: str

    g = Graph()
    worker_t = NamedNode(f"{EX}Worker")
    base_t = NamedNode(f"{EX}Base")
    bob = NamedNode(f"{EX}bob")
    g.add((worker_t, NamedNode(f"{RDFS}subClassOf"), base_t))
    g.add((bob, NamedNode(RDF_TYPE), worker_t))

    loaded = all_from_graph_dispatch(g)
    assert len(loaded) == 1
    assert isinstance(loaded[0], Worker)


def test_all_from_dataset_dispatch_explicit_de_skolemize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from triplemodel.io.dispatch import all_from_dataset_dispatch

    calls: list[bool] = []

    def track(graph, *, de_skolemize: bool = False):
        calls.append(de_skolemize)
        return graph

    monkeypatch.setattr("triplemodel.io.skolem.apply_de_skolemize", track)

    class DsPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF_NS}Person"
            id_field = "slug"
            graph_iri = f"{EX}graph/people"
            skolemize_import = True
            prefixes = {"foaf": FOAF_NS}

        slug: str
        name: str = rdf_field("foaf:name")

    ds = DsPerson(slug="x", name="X").to_dataset()
    all_from_dataset_dispatch(ds, de_skolemize=False)
    assert calls and all(flag is False for flag in calls)


def test_resolve_model_class_with_rdfs_no_types_raises() -> None:
    from triplemodel.io.rdfs import resolve_model_class_with_rdfs

    g = Graph()
    orphan = NamedNode(f"{EX}orphan")
    g.add((orphan, NamedNode(f"{FOAF_NS}name"), Literal("orphan")))

    with pytest.raises(ValueError, match="rdf:types: \\[\\]"):
        resolve_model_class_with_rdfs(g, orphan)


def test_all_from_dataset_dispatch_skips_empty_matching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from triplemodel.io.dispatch import all_from_dataset_dispatch

    class DsOrphan(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}OrphanType"
            id_field = "slug"
            graph_iri = f"{EX}graph/orphan"

        slug: str

    from triplemodel import get_graph_context

    ds = DsOrphan(slug="o").to_dataset()
    ctx = get_graph_context(ds, f"{EX}graph/orphan")
    subj = NamedNode(f"{EX}ghost")
    ctx.add((subj, NamedNode(f"{FOAF_NS}name"), Literal("ghost")))

    monkeypatch.setattr(
        "triplemodel.io.dispatch._contexts_for_subject",
        lambda _dataset, _subject: [],
    )
    loaded = all_from_dataset_dispatch(ds)
    assert loaded == []


def test_all_from_dataset_dispatch_skips_unresolvable_subject() -> None:
    from triplemodel import get_graph_context
    from triplemodel.io.dispatch import all_from_dataset_dispatch

    class DsUntyped(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}UntypedType"
            id_field = "slug"
            graph_iri = f"{EX}graph/unresolved"

        slug: str

    ds = DsUntyped(slug="typed").to_dataset()
    ctx = get_graph_context(ds, f"{EX}graph/unresolved")
    subj = NamedNode(f"{EX}untyped")
    ctx.add((subj, NamedNode(f"{FOAF_NS}name"), Literal("no type")))

    loaded = all_from_dataset_dispatch(ds)
    assert len(loaded) == 1
    assert isinstance(loaded[0], DsUntyped)


def test_all_from_dataset_dispatch_model_classes_excludes_other_types() -> None:
    from triplemodel.io.dispatch import all_from_dataset_dispatch

    class DsPerson(TripleModel):
        class Rdf:
            namespace = "http://example.org/ds-filter/"
            type_uri = "http://example.org/DsFilterPerson"
            id_field = "slug"
            graph_iri = "http://example.org/graph/filter"

        slug: str

    class DsWorker(DsPerson):
        class Rdf:
            namespace = "http://example.org/ds-filter/"
            type_uri = "http://example.org/DsFilterWorker"
            id_field = "slug"
            graph_iri = "http://example.org/graph/filter"

        slug: str

    worker = DsWorker(slug="w")
    loaded = all_from_dataset_dispatch(
        worker.to_dataset(),
        model_classes=[DsPerson],
    )
    assert loaded == []
