"""Tests for rdflib version compatibility helpers."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph, URIRef
from rdflib.graph import Dataset

from triplemodel._rdflib_compat import dataset_default_graph, graph_cbd


def test_dataset_default_graph_uses_default_graph_attr():
    ds = Dataset()
    g = dataset_default_graph(ds)
    assert isinstance(g, Graph)


def test_dataset_default_graph_falls_back_to_default_context():
    ds = MagicMock()
    ctx = Graph()
    ds.default_graph = None
    ds.default_context = ctx
    g = dataset_default_graph(ds)
    assert g is ctx


def test_dataset_default_graph_raises_when_missing():
    with pytest.raises(RuntimeError, match="default_graph or default_context"):
        dataset_default_graph(object())  # ty: ignore[invalid-argument-type]


def test_graph_cbd_passes_include_reifications_when_supported():
    g = Graph()
    subj = URIRef("http://example.org/s")
    g.add((subj, URIRef("http://example.org/p"), URIRef("http://example.org/o")))
    out = graph_cbd(g, subj, include_reifications=False)
    assert len(out) >= 1


def test_graph_cbd_includes_all_supported_kwargs():
    g = Graph()
    subj = URIRef("http://example.org/s")
    target = Graph()
    expected = Graph()
    params = {
        "resource": inspect.Parameter(
            "resource", inspect.Parameter.POSITIONAL_OR_KEYWORD
        ),
        "target_graph": inspect.Parameter(
            "target_graph", inspect.Parameter.KEYWORD_ONLY, default=None
        ),
        "include_reifications": inspect.Parameter(
            "include_reifications", inspect.Parameter.KEYWORD_ONLY, default=True
        ),
    }
    with patch("triplemodel._rdflib_compat._cbd_parameters", return_value=params):
        mock_cbd = MagicMock(return_value=expected)
        g.cbd = mock_cbd  # ty: ignore[invalid-assignment]
        out = graph_cbd(
            g,
            subj,
            target_graph=target,
            include_reifications=False,
        )
    mock_cbd.assert_called_once_with(
        subj,
        target_graph=target,
        include_reifications=False,
    )
    assert out is expected


def test_graph_cbd_omits_include_reifications_when_unsupported():
    g = Graph()
    subj = URIRef("http://example.org/s")
    target = Graph()
    expected = Graph()
    params = {
        "resource": inspect.Parameter(
            "resource", inspect.Parameter.POSITIONAL_OR_KEYWORD
        ),
        "target_graph": inspect.Parameter(
            "target_graph", inspect.Parameter.KEYWORD_ONLY, default=None
        ),
    }
    with patch("triplemodel._rdflib_compat._cbd_parameters", return_value=params):
        mock_cbd = MagicMock(return_value=expected)
        g.cbd = mock_cbd  # ty: ignore[invalid-assignment]
        out = graph_cbd(g, subj, target_graph=target, include_reifications=True)
    mock_cbd.assert_called_once_with(subj, target_graph=target)
    assert out is expected
