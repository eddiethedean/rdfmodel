"""Tests for rdflib version compatibility helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rdflib import Graph, URIRef
from rdflib.graph import Dataset

from triplemodel._rdflib_compat import dataset_default_graph, graph_cbd


def test_dataset_default_graph_uses_default_graph_attr():
    ds = Dataset()
    g = dataset_default_graph(ds)
    assert isinstance(g, Graph)


def test_dataset_default_graph_falls_back_to_default_context():
    ds = Dataset()
    object.__setattr__(ds, "default_graph", None)
    g = dataset_default_graph(ds)
    assert g is ds.default_context


def test_graph_cbd_passes_include_reifications_when_supported():
    g = Graph()
    subj = URIRef("http://example.org/s")
    g.add((subj, URIRef("http://example.org/p"), URIRef("http://example.org/o")))
    out = graph_cbd(g, subj, include_reifications=False)
    assert len(out) >= 1


def test_graph_cbd_omits_include_reifications_when_unsupported():
    g = Graph()
    subj = URIRef("http://example.org/s")
    target = Graph()
    expected = Graph()
    with patch(
        "triplemodel._rdflib_compat._CBD_SUPPORTS_REIFICATIONS",
        False,
    ):
        g.cbd = MagicMock(return_value=expected)  # type: ignore[method-assign]
        out = graph_cbd(g, subj, target_graph=target, include_reifications=True)
    g.cbd.assert_called_once_with(subj, target_graph=target)
    assert out is expected
