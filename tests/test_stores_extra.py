"""Extra coverage for store helpers and codegen CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from triplemodel.store import RdfGraph as Graph

from triplemodel.io.stores import destroy_store, open_graph


def test_open_graph_sparql_rejected():
    with pytest.raises(ValueError, match="not supported"):
        open_graph("sparql", "http://example.invalid/")


def test_open_graph_disk(tmp_path: Path):
    path = tmp_path / "rdfstore"
    g = open_graph("disk", str(path))
    assert isinstance(g, Graph)
    g.add(
        (
            "http://example.org/s",
            "http://example.org/p",
            "http://example.org/o",
        )
    )
    assert len(g) == 1


def test_destroy_store_disk(tmp_path: Path):
    path = tmp_path / "rdfstore"
    open_graph("disk", str(path))
    destroy_store(str(path), store="disk")
    assert not path.exists()


def test_open_graph_sqlalchemy_removed():
    with pytest.raises(ValueError, match="not supported"):
        open_graph("sqlalchemy", "sqlite:///x.db")
