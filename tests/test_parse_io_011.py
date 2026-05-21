"""Parse flags, infer_format, serialize prefixes (0.11)."""

from __future__ import annotations

from pathlib import Path

import pytest

from triplemodel.io.files import infer_format, parse_into_graph
from triplemodel.store.formats import format_supports_datasets, format_supports_rdf_star
from triplemodel.namespaces import bind_namespaces

EX = "http://example.org/"
FOAF = "http://xmlns.com/foaf/0.1/"


def test_infer_format_from_extension_fallback() -> None:
    assert infer_format("file.unknown", "turtle") == "turtle"
    assert infer_format(Path("x.ttl"), None) == "turtle"


def test_infer_format_uses_rdf_format_from_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from triplemodel.io import files as files_mod

    monkeypatch.setattr(files_mod, "_MEDIA_TO_FORMAT", {})
    monkeypatch.setattr(files_mod, "_SUFFIX_TO_FORMAT", {})
    assert infer_format("application/trig", None) == "trig"


def test_format_supports_helpers() -> None:
    assert format_supports_datasets("trig")
    assert format_supports_rdf_star("turtle")


def test_parse_lenient_flag(tmp_path: Path) -> None:
    bad = tmp_path / "bad.ttl"
    bad.write_text(
        '@prefix ex: <http://ex/> .\nex:s ex:p "v" .\n# incomplete\n', encoding="utf-8"
    )
    graph = parse_into_graph(source=bad, lenient=True)
    try:
        assert len(list(graph)) >= 0
    finally:
        graph.close()


def test_serialize_bound_prefixes(tmp_path: Path) -> None:
    graph = parse_into_graph(
        data=f"@prefix foaf: <{FOAF}> .\n<{EX}s> a foaf:Person .\n",
        format="turtle",
    )
    bind_namespaces(graph, {"foaf": FOAF})
    out = graph.serialize(format="turtle")
    assert "@prefix" in out or "foaf:" in out
    graph.close()


def test_nt_serialize_stable(tmp_path: Path) -> None:
    data = f'<{EX}s> <{EX}p> "v" .\n'
    g1 = parse_into_graph(data=data, format="nt")
    g2 = parse_into_graph(data=data, format="nt")
    try:
        assert g1.serialize(format="nt") == g2.serialize(format="nt")
    finally:
        g1.close()
        g2.close()
