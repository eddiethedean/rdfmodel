"""Tests for store helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.stores import (
    destroy_store,
    graph_store_session,
    open_graph,
    store_commit,
    store_rollback,
)

EX = "http://example.org/"


class StorePerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def test_open_graph_memory():
    g = open_graph("memory")
    assert isinstance(g, Graph)


def test_store_commit_rollback_noop_memory():
    g = open_graph("memory")
    store_commit(g)
    store_rollback(g)


def test_graph_store_session_opens_when_supported():
    g = open_graph("memory")
    with graph_store_session(g) as inner:
        assert inner is g


def test_destroy_store_rejects_memory():
    with pytest.raises(ValueError, match="disk"):
        destroy_store("unused", store="memory")


def test_open_graph_unknown_store():
    with pytest.raises(ValueError, match="Unknown store"):
        open_graph("not-a-store")


def test_disk_round_trip(tmp_path: Path) -> None:
    store_dir = tmp_path / "oxstore"
    g = open_graph("disk", str(store_dir))
    subj = NamedNode(f"{EX}alice")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
    g.add((subj, NamedNode(f"{EX}name"), Literal("Alice")))
    store_commit(g)
    del g
    g2 = open_graph("disk", str(store_dir))
    from triplemodel.io.import_ import graph_to_models

    people = graph_to_models(g2, StorePerson)
    assert len(people) == 1
    assert people[0].name == "Alice"
    del g2
    destroy_store(str(store_dir), store="disk")


def test_coerce_store_name_sqlalchemy_warns() -> None:
    from triplemodel.io.stores import coerce_store_name

    with pytest.warns(DeprecationWarning, match="sqlalchemy"):
        assert coerce_store_name("sqlalchemy") == "disk"
