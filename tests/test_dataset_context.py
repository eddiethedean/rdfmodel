"""Tests for dataset context and CBD helpers (pyoxigraph backend)."""

from __future__ import annotations

from pyoxigraph import NamedNode
from triplemodel.store import RdfDataset as Dataset, RdfGraph as Graph
from triplemodel.store.cbd import cbd_subgraph


def test_dataset_default_graph():
    ds = Dataset()
    g = ds.default_graph
    assert isinstance(g, Graph)


def test_get_graph_context_named_graph():
    from triplemodel.config import get_graph_context

    ds = Dataset()
    ctx = ds.graph("http://example.org/g1")
    ctx.add(
        (
            NamedNode("http://example.org/s"),
            NamedNode("http://example.org/p"),
            NamedNode("http://example.org/o"),
        )
    )
    view = get_graph_context(ds, "http://example.org/g1")
    assert len(view) == 1


def test_cbd_subgraph_includes_linked_resources():
    g = Graph()
    subj = NamedNode("http://example.org/s")
    child = NamedNode("http://example.org/child")
    g.add((subj, NamedNode("http://example.org/p"), child))
    g.add(
        (child, NamedNode("http://example.org/p2"), NamedNode("http://example.org/o"))
    )
    out = cbd_subgraph(g, subj)
    assert len(out) >= 2


def test_graph_cbd_method():
    g = Graph()
    subj = NamedNode("http://example.org/s")
    g.add((subj, NamedNode("http://example.org/p"), NamedNode("http://example.org/o")))
    out = g.cbd(subj)
    assert len(out) >= 1
