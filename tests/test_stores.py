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
from tests._type_uri import module_type_uri

EX = "http://example.org/"
PERSON_TYPE = module_type_uri("StorePerson")


class StorePerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
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
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(PERSON_TYPE)))
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


def test_open_graph_disk_create_false_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-store"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        open_graph("disk", str(missing), create=False)


def test_open_graph_disk_read_only(tmp_path: Path) -> None:
    store_dir = tmp_path / "ro-store"
    g = open_graph("disk", str(store_dir))
    subj = NamedNode(f"{EX}bob")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(PERSON_TYPE)))
    store_commit(g)
    g.close()
    g_ro = open_graph("disk", str(store_dir), read_only=True)
    try:
        assert len(g_ro) >= 1
    finally:
        g_ro.close()
    destroy_store(str(store_dir), store="disk")


def test_graph_close_destroy_failure(tmp_path: Path, monkeypatch) -> None:
    from triplemodel.io.files import _streaming_store_identifier

    path = tmp_path / "data.nt"
    path.write_text(f"<{EX}x> <{RDF_TYPE}> <{PERSON_TYPE}> .\n", encoding="utf-8")
    ident, ephemeral = _streaming_store_identifier(path, "disk", None)

    def boom(*_args, **_kwargs):
        raise OSError("destroy failed")

    monkeypatch.setattr("triplemodel.io.stores.destroy_store", boom)
    g = open_graph("disk", ident, ephemeral_store_path=ephemeral)
    with pytest.warns(ResourceWarning, match="Failed to remove ephemeral store"):
        g.close()
    g.close()


def test_graph_close_ephemeral(tmp_path: Path) -> None:
    from triplemodel.io.files import _streaming_store_identifier

    path = tmp_path / "data.nt"
    path.write_text(f"<{EX}x> <{RDF_TYPE}> <{PERSON_TYPE}> .\n", encoding="utf-8")
    ident, ephemeral = _streaming_store_identifier(path, "disk", None)
    assert ephemeral is not None
    assert ephemeral == ident
    ephemeral_dir = Path(ephemeral)
    g = open_graph("disk", ident, ephemeral_store_path=ephemeral)
    assert g.ephemeral_store_path == ephemeral
    assert ephemeral_dir.is_dir()
    g.close()
    assert not ephemeral_dir.exists()
