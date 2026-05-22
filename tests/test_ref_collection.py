"""Multi-valued URI references: set/list ResourceRef and ref_field."""

from __future__ import annotations

import pytest
from pyoxigraph import BlankNode, Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import (
    ResourceRef,
    TripleModel,
    hydrate_refs,
    rdf_field,
    ref_field,
    sync_to_graph,
)
from triplemodel.config import RDF_TYPE
from triplemodel.store.terms import term_str

EX = "http://example.org/"
TAG = f"{EX}tag/"
TOPIC = f"{EX}topic/"


class Tag(TripleModel):
    class Rdf:
        namespace = TAG
        type_uri = f"{TAG}Tag"
        id_field = "slug"

    slug: str
    label: str = rdf_field(f"{EX}label")


class Topic(TripleModel):
    class Rdf:
        namespace = TOPIC
        type_uri = f"{TOPIC}Topic"
        id_field = "slug"

    slug: str
    label: str = rdf_field(f"{EX}label")


class Country(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Country"
        id_field = "code"

    code: str


class City(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}City"
        id_field = "code"

    code: str
    country: Country = ref_field(f"{EX}inCountry", model=Country)


class Post(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Post"
        id_field = "slug"

    slug: str
    refs: set[ResourceRef] = rdf_field(f"{EX}mentions", default_factory=set)
    tags: list[Tag] = ref_field(f"{EX}tagged", model=Tag, default_factory=list)
    ordered: list[ResourceRef] = rdf_field(f"{EX}orderedTag", default_factory=list)


def _tag_graph() -> Graph:
    g = Graph()
    for slug, label in (("a", "Alpha"), ("b", "Beta")):
        uri = NamedNode(f"{TAG}{slug}")
        g.add((uri, NamedNode(RDF_TYPE), NamedNode(f"{TAG}Tag")))
        g.add((uri, NamedNode(f"{EX}label"), Literal(label)))
    return g


def test_set_resource_ref_roundtrip():
    post = Post(
        slug="p1",
        refs={ResourceRef(f"{TAG}a"), ResourceRef(f"{TAG}b")},
    )
    restored = Post.from_graph(post.to_graph(), post.subject_uri())
    assert restored.refs == {
        ResourceRef(f"{TAG}a"),
        ResourceRef(f"{TAG}b"),
    }


def test_set_ref_field_roundtrip():
    g = _tag_graph()
    subj = NamedNode(f"{EX}p1")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Post")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}a")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}b")))
    post = Post.from_graph(g, term_str(subj), validate_type=False)
    assert len(post.tags) == 2
    assert {t.label for t in post.tags} == {"Alpha", "Beta"}


def test_set_ref_field_export():
    post = Post(
        slug="p1",
        tags=[Tag(slug="a", label="A"), Tag(slug="b", label="B")],
    )
    g = post.to_graph()
    objs = list(g.objects(NamedNode(post.subject_uri()), NamedNode(f"{EX}tagged")))
    assert {term_str(o) for o in objs} == {f"{TAG}a", f"{TAG}b"}


def test_list_resource_ref_rdf_list_roundtrip():
    post = Post(
        slug="p1",
        ordered=[ResourceRef(f"{TAG}a"), ResourceRef(f"{TAG}b")],
    )
    restored = Post.from_graph(post.to_graph(), post.subject_uri())
    assert [r.iri for r in restored.ordered] == [f"{TAG}a", f"{TAG}b"]


def test_hydrate_refs_collection_shared_cache():
    g = _tag_graph()
    subj = NamedNode(f"{EX}p1")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Post")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}a")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}b")))
    Post.from_graph(g, term_str(subj), validate_type=False)
    stubs = [
        Post(
            slug="p1",
            tags=[Tag(slug="a", label="x"), Tag(slug="b", label="y")],
        )
    ]
    hydrated = hydrate_refs(stubs, g, "tags")
    assert {t.label for t in hydrated[0].tags} == {"Alpha", "Beta"}


def test_sync_replace_clears_stale_ref_objects():
    post = Post(
        slug="p1",
        tags=[Tag(slug="a", label="A"), Tag(slug="b", label="B")],
    )
    g = post.to_graph()
    post.tags = [Tag(slug="a", label="A")]
    sync_to_graph(post, g, mode="replace")
    objs = list(g.objects(NamedNode(post.subject_uri()), NamedNode(f"{EX}tagged")))
    assert len(objs) == 1
    assert term_str(objs[0]) == f"{TAG}a"


def test_embedded_set_without_ref_field_raises():
    import pytest

    with pytest.raises(ValueError, match="not supported"):

        class Team(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}Team"
                id_field = "slug"

            slug: str
            members: set[Tag] = rdf_field(f"{EX}member", default_factory=set)


def test_set_ref_field_on_triple_model_raises():
    import pytest

    with pytest.raises(ValueError, match="not hashable"):

        class Bad(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}Bad"
                id_field = "slug"

            slug: str
            tags: set[Tag] = ref_field(f"{EX}tagged", model=Tag, default_factory=set)


def test_import_ref_resource_rejects_bnode():
    from triplemodel.io.import_ import _import_ref_resource
    from triplemodel.terms.registry import default_registry

    with pytest.raises(ValueError, match="URI resource"):
        _import_ref_resource(
            Graph(),
            BlankNode(),
            Tag,
            "tags",
            f"{EX}tagged",
            f"{EX}p1",
            on_duplicate="first",
            registry=default_registry,
            de_skolemize=False,
        )


def test_ref_collection_element_type_scalar_ref_is_none():
    from triplemodel.metadata.cardinality import ref_collection_element_type

    assert ref_collection_element_type(Post.model_fields["refs"]) is None
    assert ref_collection_element_type(Post.model_fields["slug"]) is None
    assert ref_collection_element_type(City.model_fields["country"]) is None


def test_ref_collection_inner_not_triple_model_returns_none():
    from triplemodel.metadata.cardinality import ref_collection_element_type

    class LinkHolder(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}LinkHolder"
            id_field = "slug"

        slug: str
        links: list[ResourceRef] = ref_field(
            f"{EX}link", model=Tag, default_factory=list
        )

    assert ref_collection_element_type(LinkHolder.model_fields["links"]) is None


def test_import_set_ref_collection_branch(monkeypatch):
    from triplemodel.io import import_ as import_mod
    from triplemodel.metadata.cardinality import field_cardinality as real_cardinality

    tags_field = Post.model_fields["tags"]

    def _cardinality(fi):
        if fi is tags_field:
            return "set"
        return real_cardinality(fi)

    g = _tag_graph()
    subj = NamedNode(f"{EX}p1")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Post")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}a")))
    g.add((subj, NamedNode(f"{EX}tagged"), NamedNode(f"{TAG}b")))
    monkeypatch.setattr(import_mod, "field_cardinality", _cardinality)
    result = import_mod.import_field_value(
        g,
        [NamedNode(f"{TAG}a"), NamedNode(f"{TAG}b")],
        Post.model_fields["tags"],
        "tags",
        f"{EX}tagged",
        term_str(subj),
        embed="iri",
        on_duplicate="first",
    )
    assert isinstance(result, list)
    assert len(result) == 2


def test_hydrate_refs_skips_items_without_uri(monkeypatch):
    from triplemodel.io import hydrate as hydrate_mod

    monkeypatch.setattr(hydrate_mod, "_ref_uri", lambda _v: None)
    g = _tag_graph()
    stubs = [Post(slug="p1", tags=[Tag(slug="a", label="stub")])]
    assert hydrate_refs(stubs, g, "tags") == stubs


def test_export_ref_collection_none_field():
    post = Post.model_construct(slug="p1", tags=None)
    assert not [t for t in post.to_triples() if t[1] == f"{EX}tagged"]


def test_export_ref_collection_skips_none_entries():
    post = Post.model_construct(
        slug="p1",
        tags=[Tag(slug="a", label="A"), None, Tag(slug="b", label="B")],
    )
    objs = list(
        post.to_graph().objects(NamedNode(post.subject_uri()), NamedNode(f"{EX}tagged"))
    )
    assert len(objs) == 2


def test_ref_field_list_collection_allowed_at_class_init():
    class Linked(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Linked"
            id_field = "slug"

        slug: str
        tags: list[Tag] = ref_field(f"{EX}tagged", model=Tag, default_factory=list)

    assert Linked.model_fields["tags"].annotation is not None
