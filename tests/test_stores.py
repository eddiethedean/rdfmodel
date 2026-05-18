"""Tests for store helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, Literal, URIRef

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
    with pytest.raises(ValueError, match="in-memory"):
        destroy_store("unused", store="memory")


def test_open_graph_unknown_store():
    with pytest.raises(ValueError, match="Unknown store"):
        open_graph("not-a-store")


def _sqlalchemy_store_available() -> bool:
    try:
        import os
        import tempfile

        from triplemodel.io.stores import open_graph

        fd, path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        ident = f"sqlite:///{path}"
        g = open_graph("sqlalchemy", ident)
        g.close()
        os.unlink(path)
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _sqlalchemy_store_available(),
    reason="rdflib-sqlalchemy store plugin not installed",
)
def test_sqlalchemy_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "test.sqlite"
    ident = f"sqlite:///{db}"
    g = open_graph("sqlalchemy", ident)
    subj = URIRef(f"{EX}alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{EX}Person")))
    g.add((subj, URIRef(f"{EX}name"), Literal("Alice")))
    store_commit(g)
    g2 = open_graph("sqlalchemy", ident)
    from triplemodel.io.import_ import graph_to_models

    people = graph_to_models(g2, StorePerson)
    assert len(people) == 1
    assert people[0].name == "Alice"
    destroy_store(ident, store="sqlalchemy")
