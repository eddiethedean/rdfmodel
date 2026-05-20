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


def test_open_graph_sqlalchemy_deprecated_maps_to_disk(tmp_path: Path) -> None:
    path = tmp_path / "legacy-store"
    with pytest.warns(DeprecationWarning, match="sqlalchemy"):
        g = open_graph("sqlalchemy", str(path))
    assert isinstance(g, Graph)
    g.close()
    destroy_store(str(path), store="disk")


def test_open_graph_memory_read_only_warns() -> None:
    with pytest.warns(UserWarning, match="ignored for in-memory"):
        g = open_graph("memory", read_only=True, create=False)
    assert isinstance(g, Graph)


def test_open_graph_ignores_unknown_kwargs(tmp_path: Path) -> None:
    path = tmp_path / "kw-store"
    with pytest.warns(UserWarning, match="ignored unsupported"):
        g = open_graph("disk", str(path), foo="bar")
    g.close()
    destroy_store(str(path), store="disk")
