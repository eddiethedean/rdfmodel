"""Nested embed models with ``list[T]`` (rdf:List) fields."""

from __future__ import annotations

import pytest
from pyoxigraph import NamedNode

from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.terms.collection import remove_rdf_list
from triplemodel.vocab import FOAF

from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")


EX = "http://example.org/people/"
FOAF_NICK = f"{FOAF}nick"


class TagHolder(TripleModel):
    class Rdf:
        namespace = "http://example.org/tagholder/"
        type_uri = "http://example.org/TagHolder"
        id_field = "slug"

    slug: str = "t1"
    tags: list[str] = rdf_field("http://example.org/tag", default_factory=list)


class PersonIri(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
        id_field = "slug"
        embed = "iri"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    holder: TagHolder | None = rdf_field("http://example.org/tags", default=None)


class PersonBnode(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = module_type_uri("Person_2")
        id_field = "slug"
        embed = "bnode"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    holder: TagHolder | None = rdf_field("http://example.org/tags", default=None)


def test_nested_iri_list_roundtrip():
    holder = TagHolder(tags=["a", "b"])
    p = PersonIri(slug="alice", name="Alice", holder=holder)
    g = p.to_graph()
    restored = PersonIri.from_graph(g, p.subject_uri())
    assert restored.holder is not None
    assert restored.holder.tags == ["a", "b"]


def test_nested_bnode_list_roundtrip():
    holder = TagHolder(tags=["x", "y"])
    p = PersonBnode(slug="bob", name="Bob", holder=holder)
    g = p.to_graph()
    restored = PersonBnode.from_graph(g, p.subject_uri())
    assert restored.holder is not None
    assert restored.holder.tags == ["x", "y"]


def test_patch_updates_nested_iri_list():
    holder = TagHolder(tags=["one"])
    p = PersonIri(slug="alice", name="Alice", holder=holder)
    g = p.to_graph()
    child_uri = NamedNode(holder.subject_uri())

    updated = PersonIri(
        slug="alice",
        name="Alice",
        holder=TagHolder(tags=["one", "two"]),
    )
    sync_to_graph(updated, g, mode="patch")
    restored = PersonIri.from_graph(g, p.subject_uri())
    assert restored.holder is not None
    assert restored.holder.tags == ["one", "two"]
    assert len(list(g.triples((child_uri, None, None)))) >= 1


def test_remove_rdf_list_clears_non_list_bnode_subgraph():
    from pyoxigraph import BlankNode as BNode, Literal, NamedNode
    from triplemodel.store import RdfGraph as Graph

    g = Graph()
    b = BNode()
    g.add((NamedNode(EX + "alice"), NamedNode("http://example.org/tags"), b))
    g.add((b, NamedNode("http://example.org/tag"), Literal("orphan")))
    remove_rdf_list(g, NamedNode(EX + "alice"), "http://example.org/tags")
    assert len(g) == 0


def test_list_subject_from_embed_rows_helpers():
    from pyoxigraph import BlankNode as BNode

    from triplemodel.config import get_rdf_config
    from triplemodel.embed.strategies import export_nested_triples
    from triplemodel.io.list_fields import (
        list_subject_from_embed_rows,
        nested_embed_list_subject,
    )

    b = BNode()
    assert list_subject_from_embed_rows([(b, "p", "o")]) == b
    assert list_subject_from_embed_rows([("http://example.org/s", "p", "o")]) is None

    holder = TagHolder(tags=["z"])
    cfg = get_rdf_config(PersonBnode)
    rows = export_nested_triples(
        EX + "bob",
        "http://example.org/tags",
        holder,
        embed="bnode",
        config=cfg,
    )
    subj = nested_embed_list_subject(
        holder,
        parent_subject=EX + "bob",
        predicate="http://example.org/tags",
        parent_config=cfg,
        embed_rows=rows,
    )
    assert isinstance(subj, BNode)

    with pytest.raises(ValueError, match="Cannot resolve blank-node list subject"):
        nested_embed_list_subject(
            holder,
            parent_subject=EX + "bob",
            predicate="http://example.org/tags",
            parent_config=cfg,
            embed_rows=None,
            graph=None,
        )


def test_predicates_to_patch_all_none_list():
    from triplemodel.io.list_fields import (
        _list_effectively_empty,
        predicates_to_patch_for_model,
    )

    class Tags(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        nick: list[str | None] = rdf_field(FOAF_NICK, default_factory=list)
        tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)

    p = Tags.model_construct(slug="a", nick=[None, None], tag=set())
    preds = predicates_to_patch_for_model(p)
    assert FOAF_NICK in preds
    assert "http://example.org/tag" in preds
    assert _list_effectively_empty([None, None]) is True
    assert _list_effectively_empty(["a"]) is False
    assert _list_effectively_empty("x") is False


def test_iter_nested_list_exports_skips_when_nested_cls_unresolved():
    from unittest.mock import patch

    from triplemodel.io.list_fields import iter_nested_list_exports

    p = PersonIri(slug="a", name="A", holder=TagHolder())
    with (
        patch("triplemodel.io.list_fields.field_cardinality", return_value="nested"),
        patch("triplemodel.io.list_fields.nested_model_type", return_value=None),
    ):
        assert list(iter_nested_list_exports(p, subject=EX + "a")) == []


def test_iter_nested_list_exports_skips_bad_embed_and_unmapped():
    from triplemodel.io.list_fields import iter_nested_list_exports

    class BadEmbedCfg:
        embed = "other"
        id_field = "slug"
        prefixes_dict: dict[str, str] = {}

    class Parent(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            embed = "iri"

        slug: str
        holder: TagHolder

    p = Parent(slug="a", holder=TagHolder())
    from typing import cast

    from triplemodel.config import RdfConfig

    bad_cfg = cast(RdfConfig, BadEmbedCfg())
    assert list(iter_nested_list_exports(p, subject=EX + "a", config=bad_cfg)) == []

    class ParentUnmapped(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"
            embed = "iri"

        slug: str
        holder: TagHolder

    from triplemodel.config import get_rdf_config

    p2 = ParentUnmapped(slug="b", holder=TagHolder())
    cfg = get_rdf_config(ParentUnmapped)
    assert list(iter_nested_list_exports(p2, subject=EX + "b", config=cfg)) == []


def test_stable_bnode_replace_drops_removed_predicate():
    class PersonStable(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = module_type_uri("Person_3")
            id_field = "slug"
            embed = "bnode"
            blank_node_policy = "stable"

        slug: str
        holder: TagHolder | None = rdf_field("http://example.org/tags", default=None)

    holder = TagHolder(tags=["a"])
    p = PersonStable(slug="bob", holder=holder)
    g = p.to_graph()
    n_before = len(g)
    updated = PersonStable(slug="bob", holder=TagHolder(tags=[]))
    sync_to_graph(updated, g, mode="replace")
    assert len(g) <= n_before
    restored = PersonStable.from_graph(g, p.subject_uri())
    assert restored.holder is not None
    assert restored.holder.tags == []


def test_patch_clears_nested_iri_optional_scalar():
    PHONE = "http://example.org/phone"

    class Mailbox(TripleModel):
        class Rdf:
            namespace = "http://example.org/mailbox/"
            type_uri = "http://example.org/Mailbox"
            id_field = "slug"

        slug: str = "m1"
        address: str = rdf_field("http://example.org/address")
        phone: str | None = rdf_field(PHONE, default=None)

    class Person(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = module_type_uri("Person_4")
            id_field = "slug"
            embed = "iri"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)

    mbox = Mailbox(slug="m1", address="a@example.org", phone="+1")
    p = Person(slug="alice", name="Alice", mbox=mbox)
    g = p.to_graph()
    child = NamedNode(mbox.subject_uri())
    assert any(g.triples((child, NamedNode(PHONE), None)))

    updated = Person(
        slug="alice",
        name="Alice",
        mbox=Mailbox(slug="m1", address="a@example.org", phone=None),
    )
    sync_to_graph(updated, g, mode="patch")
    assert list(g.triples((child, NamedNode(PHONE), None))) == []
    restored = Person.from_graph(g, p.subject_uri())
    assert restored.mbox is not None
    assert restored.mbox.phone is None
