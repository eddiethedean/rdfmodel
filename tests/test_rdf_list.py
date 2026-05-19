"""Tests for ``list[T]`` as native ``rdf:List``."""

from __future__ import annotations

import warnings

import pytest
from pyoxigraph import BlankNode as BNode, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.namespaces import RDF_FIRST as RDF_FIRST_URI

from triplemodel import TripleModel, objects_for_field, rdf_field, sync_to_graph
from triplemodel.io.list_fields import clear_model_rdf_lists
from triplemodel.terms.collection import read_rdf_list

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)


def test_rdf_list_ordered_roundtrip():
    p = Person(slug="a", nick=["first", "second"])
    restored = Person.from_graph(p.to_graph(), p.subject_uri())
    assert restored.nick == ["first", "second"]


def test_patch_clears_empty_rdf_list():
    p = Person(slug="a", nick=["x"])
    g = p.to_graph()
    sync_to_graph(Person(slug="a", nick=[]), g, mode="patch")
    subj = NamedNode(p.subject_uri())
    assert list(g.objects(subj, NamedNode(f"{FOAF}nick"))) == []


def test_clear_model_rdf_lists():
    p = Person(slug="a", nick=["x"])
    g = p.to_graph()
    clear_model_rdf_lists(g, Person, p.subject_uri())
    subj = NamedNode(p.subject_uri())
    assert list(g.objects(subj, NamedNode(f"{FOAF}nick"))) == []


def test_clear_model_rdf_lists_skips_id_field():
    g = Graph()
    clear_model_rdf_lists(g, Person, EX + "a")


def test_patch_list_field_without_predicate():
    class Bare(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        notes: list[str] = []

    g = Graph()
    sync_to_graph(Bare(slug="a", notes=["x"]), g, mode="patch")


def test_clear_model_skips_non_list_fields():
    class Mixed(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)
        tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)

    p = Mixed(slug="a", nick=["x"], tag={"t"})
    g = p.to_graph()
    clear_model_rdf_lists(g, Mixed, p.subject_uri())
    from triplemodel.store.terms import term_str

    assert {
        term_str(o)
        for o in g.objects(
            NamedNode(p.subject_uri()), NamedNode("http://example.org/tag")
        )
    } == {"t"}


def test_objects_for_field_set():
    class Tagged(Person):
        tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)

    p = Tagged(slug="a", tag={"x", "y"})
    objs = objects_for_field(p.to_graph(), p.subject_uri(), Tagged, "tag")
    assert set(objs) == {"x", "y"}


def test_set_multi_object_predicate():
    class Tagged(Person):
        tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)

    p = Tagged(slug="a", tag={"a", "b"})
    g = p.to_graph()
    subj = NamedNode(p.subject_uri())
    from triplemodel.store.terms import term_str

    assert {
        term_str(o) for o in g.objects(subj, NamedNode("http://example.org/tag"))
    } == {
        "a",
        "b",
    }


def test_export_skips_none_nick_value():
    p = Person.model_construct(slug="a", nick=None)
    g = Graph()
    from triplemodel.io.list_fields import export_model_rdf_lists

    export_model_rdf_lists(g, p, subject=p.subject_uri())
    assert list(g) == []


def test_write_rdf_list_all_none_terms():
    from triplemodel.terms.collection import write_rdf_list

    g = Graph()
    write_rdf_list(g, EX + "a", f"{FOAF}nick", [None, None])
    assert len(g) == 0


def test_list_field_duplicate_warns():
    from unittest.mock import patch

    from pyoxigraph import BlankNode as BNode

    from triplemodel.io.import_ import import_field_value

    g = Graph()
    with patch("triplemodel.io.import_.read_rdf_list", return_value=["only"]):
        with pytest.warns(UserWarning, match="Multiple objects"):
            result = import_field_value(
                g,
                [BNode("a"), BNode("b")],
                Person.model_fields["nick"],
                "nick",
                f"{FOAF}nick",
                EX + "a",
                embed="iri",
                on_duplicate="warn",
            )
    assert result == ["only"]


def test_clear_model_skips_unmapped_list_predicate():
    class Bare(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        notes: list[str] = []

    g = Graph()
    clear_model_rdf_lists(g, Bare, EX + "a")


def test_unmapped_list_field_skipped_on_export():
    class Bare(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        notes: list[str] = []

    g = Graph()
    from triplemodel.io.list_fields import export_model_rdf_lists

    export_model_rdf_lists(g, Bare(slug="a", notes=["x"]), subject=EX + "a")
    assert len(g) == 0


def test_field_values_for_export_list_branch():
    from triplemodel.io.export import _field_values_for_export

    field = Person.model_fields["nick"]
    assert _field_values_for_export("nick", ["a"], field) == []


def test_objects_for_field_empty_list():
    p = Person(slug="a", nick=[])
    g = p.to_graph()
    assert objects_for_field(g, p.subject_uri(), Person, "nick") == []


def test_read_rdf_list_direct():
    p = Person(slug="a", nick=["x", "y"])
    g = p.to_graph()
    head = list(g.objects(NamedNode(p.subject_uri()), NamedNode(f"{FOAF}nick")))[0]
    assert read_rdf_list(g, head, str) == ["x", "y"]


def test_read_rdf_list_malformed_head_raises():
    g = Graph()
    head = BNode("not-a-list")
    g.add((NamedNode(EX + "a"), NamedNode(f"{FOAF}nick"), head))
    with pytest.raises(ValueError, match="not an rdf:List head"):
        read_rdf_list(g, head, str)


def test_from_graph_duplicate_list_heads_warns():
    p = Person(slug="a", nick=["x"])
    g = p.to_graph()
    subj = NamedNode(p.subject_uri())
    g.add((subj, NamedNode(f"{FOAF}nick"), BNode("second-list")))
    g.add(
        (
            BNode("second-list"),
            NamedNode(RDF_FIRST_URI),
            NamedNode("http://example.org/extra"),
        )
    )

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from triplemodel.store.terms import term_str

        restored = Person.from_graph(g, term_str(subj), on_duplicate="warn")
    assert any("Multiple objects" in str(x.message) for x in w)
    assert restored.nick == ["x"]
