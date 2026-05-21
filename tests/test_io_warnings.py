"""Coverage for pyoxigraph parse/serialize kwargs warnings."""

from __future__ import annotations

import pytest

from triplemodel.store import RdfGraph
from triplemodel.store.io_warnings import (
    warn_ignored_parse_kwargs,
    warn_ignored_serialize_kwargs,
    warn_jsonld_context_config,
)


def test_warn_ignored_parse_supported_kwargs() -> None:
    out = warn_ignored_parse_kwargs(
        {
            "lenient": True,
            "without_named_graphs": True,
            "rename_blank_nodes": False,
            "base": "http://example.org/",
        }
    )
    assert out["lenient"] is True
    assert out["without_named_graphs"] is True
    assert out["rename_blank_nodes"] is False
    assert out["base_iri"] == "http://example.org/"


def test_warn_ignored_parse_legacy_publicid() -> None:
    out = warn_ignored_parse_kwargs({"publicID": "http://example.org/base/"})
    assert out == {}


def test_warn_ignored_parse_unsupported() -> None:
    with pytest.warns(UserWarning, match="ignored unsupported"):
        out = warn_ignored_parse_kwargs({"context": {"@vocab": "http://ex/"}})
    assert out == {}


def test_warn_ignored_serialize_supported_and_unsupported() -> None:
    out = warn_ignored_serialize_kwargs({"base_iri": "http://example.org/"})
    assert out["base_iri"] == "http://example.org/"
    with pytest.warns(UserWarning, match="ignored unsupported"):
        assert warn_ignored_serialize_kwargs({"context": 1}) == {}


def test_warn_jsonld_context_config() -> None:
    with pytest.warns(UserWarning, match="jsonld_context"):
        warn_jsonld_context_config()


def test_graph_parse_lenient_kwarg() -> None:
    g = RdfGraph()
    ttl = "@prefix ex: <http://ex/> .\nex:s ex:p ex:o .\n"
    g.parse(data=ttl, format="turtle", lenient=True)
    assert len(g) == 1


def test_graph_serialize_base_iri_kwarg() -> None:
    g = RdfGraph()
    g.parse(data="@prefix ex: <http://ex/> .\nex:s ex:p ex:o .\n", format="turtle")
    with pytest.warns(UserWarning, match="ignored unsupported"):
        text = g.serialize(format="turtle", context={"x": 1})
    assert "http://ex/s" in text
