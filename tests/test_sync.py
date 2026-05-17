"""Tests for sync_to_graph and graph modes."""

from __future__ import annotations

from rdflib import Graph, URIRef

from triplemodel import TripleModel, rdf_field, sync_to_graph

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


def test_replace_removes_cleared_age():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    sync_to_graph(p2, g, mode="replace")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []


def test_add_leaves_stale_triples():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    p2.sync_to_graph(g, mode="add")
    subj = URIRef(p.subject_uri())
    assert len(list(g.objects(subj, URIRef(f"{FOAF}age")))) == 1


def test_patch_clears_only_none_fields():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    sync_to_graph(p2, g, mode="patch")
    subj = URIRef(p.subject_uri())
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []
    names = list(g.objects(subj, URIRef(f"{FOAF}name")))
    assert any(str(o) == "A" for o in names)


def test_instance_sync_to_graph():
    p = Person(slug="a", name="A", age=25)
    g = Graph()
    p.sync_to_graph(g, mode="replace")
    assert len(g) >= 2


def test_sync_to_graph_defaults_to_replace_when_mode_omitted():
    p = Person(slug="a", name="A", age=25)
    g = Graph()
    sync_to_graph(p, g)
    assert len(g) >= 2


def test_patch_clears_curie_predicate_empty_list():
    class CuriePerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            prefixes = {"foaf": FOAF}

        slug: str
        nick: list[str] = rdf_field("foaf:nick", default_factory=list)

    p = CuriePerson(slug="a", nick=["x"])
    g = p.to_graph()
    sync_to_graph(CuriePerson(slug="a", nick=[]), g, mode="patch")
    subj = URIRef(EX + "a")
    assert list(g.objects(subj, URIRef(f"{FOAF}nick"))) == []


def test_to_graph_add_leaves_stale_triples():
    p = Person(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = Person(slug="a", name="A", age=None)
    p2.to_graph(g)
    subj = URIRef(p.subject_uri())
    assert len(list(g.objects(subj, URIRef(f"{FOAF}age")))) == 1


def test_sync_to_graph_bind_false_skips_prefix_bind():
    p = Person(slug="a", name="A")
    g = Graph()
    sync_to_graph(p, g, mode="replace", bind=False)
    assert len(g) >= 2


def test_patch_preserves_multiple_nick_values():
    class NickPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)

    p = NickPerson(slug="a", nick=["Al", "Alice"])
    g = Graph()
    sync_to_graph(p, g, mode="patch")
    subj = URIRef(EX + "a")
    restored = NickPerson.from_graph(g, str(subj))
    assert restored.nick == ["Al", "Alice"]


def test_patch_updates_nick_without_touching_name():
    class NickPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)

    g = NickPerson(slug="a", name="A", nick=["x"]).to_graph()
    sync_to_graph(NickPerson(slug="a", name="A", nick=["y", "z"]), g, mode="patch")
    subj = URIRef(EX + "a")
    restored = NickPerson.from_graph(g, str(subj))
    assert restored.nick == ["y", "z"]
    assert restored.name == "A"


def test_to_graph_patch_preserves_multiple_values():
    class NickPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        nick: list[str] = rdf_field(f"{FOAF}nick", default_factory=list)

    p = NickPerson(slug="a", nick=["a", "b"])
    g = Graph()
    p.to_graph(g, mode="patch")
    subj = URIRef(EX + "a")
    restored = NickPerson.from_graph(g, str(subj))
    assert restored.nick == ["a", "b"]


ALT_NAME = "http://example.org/altName"


class _AltNameResolver:
    """Maps foaf:name to a custom predicate for extension-point tests."""

    def resolve_field_predicate(self, field_info, prefixes):
        from triplemodel.fields.resolver import default_resolver

        pred = default_resolver.resolve_field_predicate(field_info, prefixes)
        if pred == f"{FOAF}name":
            return ALT_NAME
        return pred

    def owned_predicates(self, model_cls, config=None):
        from triplemodel.fields.resolver import default_resolver

        preds = set(default_resolver.owned_predicates(model_cls, config))
        if f"{FOAF}name" in preds:
            preds.discard(f"{FOAF}name")
            preds.add(ALT_NAME)
        return frozenset(preds)


def test_replace_and_patch_honor_custom_resolver():
    p = Person(slug="a", name="A")
    subj = URIRef(p.subject_uri())
    resolver = _AltNameResolver()

    g = Graph()
    sync_to_graph(p, g, mode="replace", resolver=resolver)
    assert list(g.objects(subj, URIRef(ALT_NAME)))
    assert list(g.objects(subj, URIRef(f"{FOAF}name"))) == []

    g2 = Graph()
    p.to_graph(g2, mode="patch", resolver=resolver)
    assert list(g2.objects(subj, URIRef(ALT_NAME)))
    assert list(g2.objects(subj, URIRef(f"{FOAF}name"))) == []
