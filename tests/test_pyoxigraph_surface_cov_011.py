"""Coverage for 0.11 pyoxigraph surface edge cases."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from pyoxigraph import (
    BaseDirection,
    DefaultGraph,
    Literal,
    NamedNode,
    Quad,
    QueryResultsFormat,
)

from triplemodel.io.files import infer_format, merge_parse_flags
from triplemodel.io.sparql import run_sparql
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.formats import (
    format_from_hint,
    format_supports_datasets,
    query_results_format_from_hint,
    rdf_format_to_name,
    to_query_results_format,
)
from triplemodel.store.ops import (
    backup_store,
    bulk_load_into_graph,
    dump_store,
    iter_quads_for_pattern,
    load_store,
    optimize_store,
)
from triplemodel.store.query_results import parse_query_results
from triplemodel.store.sparql_result import SparqlResult
from triplemodel.terms.convert import python_to_term
from triplemodel.terms.lang import LangString

EX = "http://example.org/"


def test_infer_format_pyoxigraph_fallback(tmp_path: Path) -> None:
    """Use RdfFormat.from_extension when suffix map misses (uppercase extension)."""
    p = tmp_path / "data.TTL"
    p.write_text(f'<{EX}s> <{EX}p> "v" .\n', encoding="utf-8")
    assert infer_format(p, None) == "turtle"


def test_format_from_hint_and_helpers() -> None:
    assert format_from_hint("application/n-triples", None) == "nt"
    assert format_supports_datasets("nquads") is True
    from pyoxigraph import RdfFormat

    assert rdf_format_to_name(RdfFormat.TURTLE) == "turtle"
    assert to_query_results_format("json") == QueryResultsFormat.JSON
    assert query_results_format_from_hint("r.srj", None) == "sparql-results+json"


def test_merge_parse_flags_overrides() -> None:
    merged = merge_parse_flags({"lenient": False}, lenient=True)
    assert merged["lenient"] is True


def test_run_sparql_dataset_kwargs_coercion() -> None:
    graph = Graph()
    try:
        run_sparql(
            graph,
            "ASK {}",
            default_graph=DefaultGraph(),
            named_graphs=[f"{EX}g1", NamedNode(f"{EX}g2")],
            base_iri=f"{EX}",
        )
        with pytest.raises(TypeError, match="default_graph"):
            run_sparql(graph, "ASK {}", default_graph=123)  # ty: ignore[invalid-argument-type]
        with pytest.raises(TypeError, match="named_graphs"):
            run_sparql(graph, "ASK {}", named_graphs=[123])  # ty: ignore[invalid-argument-type]
    finally:
        graph.close()


def test_parse_query_results_paths(tmp_path: Path) -> None:
    body = json.dumps({"head": {}, "boolean": False}).encode()
    p = tmp_path / "ask.json"
    p.write_bytes(body)
    assert parse_query_results(path=p).askAnswer is False
    assert parse_query_results(source=p).askAnswer is False
    assert parse_query_results(data=body, format="json").askAnswer is False
    with pytest.raises(ValueError, match="requires source="):
        parse_query_results()
    with pytest.raises(ValueError, match="Pass source="):
        parse_query_results(source=Path("x"), data=b"x")


def test_sparql_result_serialize_errors(tmp_path: Path) -> None:
    result = SparqlResult(result_type="SELECT")
    with pytest.raises(ValueError, match="raw"):
        result.serialize()
    graph = Graph()
    try:
        raw = run_sparql(graph, "ASK {}")._raw
        assert raw is not None
        res = SparqlResult(result_type="ASK", ask_answer=True, raw=raw)
        out = tmp_path / "ask.json"
        res.serialize(destination=out, format="json")
        assert out.read_bytes()
    finally:
        graph.close()


def test_store_ops_disk_without_graph(tmp_path: Path) -> None:
    store_dir = tmp_path / "disk"
    graph = Graph()
    graph.store  # in-memory
    ttl = tmp_path / "in.ttl"
    ttl.write_text(f'<{EX}s> <{EX}p> "v" .\n', encoding="utf-8")
    bulk_load_into_graph(graph, ttl, format="nt")
    dump_store(tmp_path / "out.nq", graph=graph)
    with pytest.raises(ValueError, match="store_path"):
        dump_store(tmp_path / "x.nq")
    with pytest.raises(ValueError, match="source= or data="):
        load_store(graph)
    from triplemodel.io.stores import open_graph

    disk = open_graph("disk", str(store_dir))
    try:
        backup_store(tmp_path / "bak", graph=disk)
        optimize_store(graph=disk)
        list(iter_quads_for_pattern(disk, graph_iri=f"{EX}ng"))
    finally:
        disk.close()


def test_langstring_direction_with_lang() -> None:
    term = python_to_term(LangString("x", lang="ar", direction="rtl"))
    from pyoxigraph import Literal as OxLiteral

    assert isinstance(term, OxLiteral)
    assert term.direction == BaseDirection.RTL


def test_iter_quads_named_graph_iri() -> None:
    graph = Graph()
    try:
        list(iter_quads_for_pattern(graph, graph_iri=f"{EX}g"))
    finally:
        graph.close()


def test_ops_bulk_load_data_bytes() -> None:
    graph = Graph()
    try:
        bulk_load_into_graph(
            graph,
            data='@prefix ex: <http://ex/> .\nex:s ex:p "v" .\n',
            format="turtle",
        )
        assert len(list(iter_quads_for_pattern(graph))) >= 1
    finally:
        graph.close()


def test_run_sparql_none_dataset_graphs() -> None:
    from triplemodel.io.sparql import _coerce_query_dataset_kwargs

    assert _coerce_query_dataset_kwargs(
        {"default_graph": None, "named_graphs": None, "base_iri": "http://ex/"}
    ) == {
        "default_graph": None,
        "named_graphs": None,
        "base_iri": "http://ex/",
    }
    graph = Graph()
    try:
        run_sparql(graph, "ASK {}", default_graph=f"{EX}g")
    finally:
        graph.close()


def test_convert_langstring_direction_without_lang_raises() -> None:
    with pytest.raises(ValueError, match="language"):
        python_to_term(LangString("only", direction="ltr"))


def test_formats_unknown_results_format() -> None:
    with pytest.raises(ValueError, match="Unknown SPARQL"):
        to_query_results_format("bogus")


def test_query_results_both_source_and_data() -> None:
    with pytest.raises(ValueError, match="Pass source="):
        parse_query_results(source=Path("x"), data=b"x")


def test_ops_resolve_errors(tmp_path: Path) -> None:
    from triplemodel.store.ops import (
        _coerce_graph_name,
        _resolve_disk_path,
        _resolve_store,
    )

    with pytest.raises(ValueError, match="graph= or store_path"):
        _resolve_store(None, None)
    with pytest.raises(ValueError, match="graph= or store_path"):
        _resolve_disk_path(None, None)
    graph = Graph()
    graph._disk_store_path = str(tmp_path / "d")
    assert _resolve_disk_path(graph, None) == tmp_path / "d"
    assert _coerce_graph_name(None, None) is None
    with pytest.raises(ValueError, match="not both"):
        bulk_load_into_graph(graph, "a.ttl", data=b"x")


def test_ops_load_store_data_and_backup_path(tmp_path: Path) -> None:
    from triplemodel.io.stores import open_graph

    store_dir = tmp_path / "s"
    disk = open_graph("disk", str(store_dir))
    nq = tmp_path / "one.nq"
    dump_store(nq, graph=disk)
    disk.close()
    disk2 = open_graph("disk", str(store_dir))
    try:
        load_store(disk2, data=nq.read_bytes(), format="nquads")
        optimize_store(graph=disk2)
        backup_store(tmp_path / "bak2", graph=disk2)
    finally:
        disk2.close()


def test_list_named_graphs_blank_node() -> None:
    from triplemodel.store.ops import list_named_graphs
    from pyoxigraph import BlankNode

    graph = Graph()
    try:
        graph.store.add_graph(BlankNode("g1"))
        names = list_named_graphs(graph)
        assert any("g1" in n for n in names)
    finally:
        graph.close()


def test_graph_disk_store_path_property() -> None:
    from triplemodel.io.stores import open_graph
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        g = open_graph("disk", tmp)
        try:
            assert g.disk_store_path == tmp
        finally:
            g.close()


def test_lang_base_direction_instance() -> None:
    from triplemodel.terms.lang import _direction_to_base

    assert _direction_to_base(BaseDirection.LTR) == BaseDirection.LTR


def test_sparql_result_construct_serialize_raises() -> None:
    graph = Graph()
    try:
        raw = run_sparql(graph, "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")._raw
        res = SparqlResult(result_type="CONSTRUCT", raw=raw)
        with pytest.raises(TypeError, match="CONSTRUCT"):
            res.serialize()
    finally:
        graph.close()


def test_sparql_result_serialize_to_io(tmp_path: Path) -> None:
    graph = Graph()
    try:
        raw = run_sparql(graph, "ASK {}")._raw
        res = SparqlResult(result_type="ASK", ask_answer=True, raw=raw)
        buf = io.BytesIO()
        res.serialize(destination=buf, format="json")
        assert buf.getvalue()
    finally:
        graph.close()


def test_parse_query_results_bytesio_with_format() -> None:
    body = json.dumps({"head": {}, "boolean": True}).encode()
    assert parse_query_results(source=io.BytesIO(body), format="json").askAnswer is True


def test_resolve_disk_path_ephemeral_and_missing() -> None:
    from triplemodel.store.ops import _resolve_disk_path

    g = Graph()
    g._ephemeral_store_path = "/tmp/ephemeral-test-path"
    assert _resolve_disk_path(g, None) == Path("/tmp/ephemeral-test-path")
    g2 = Graph()
    with pytest.raises(ValueError, match="Disk store operations"):
        _resolve_disk_path(g2, None)


def test_backup_store_via_store_path_only(tmp_path: Path) -> None:
    from triplemodel.io.stores import open_graph

    store_dir = tmp_path / "solo"
    g = open_graph("disk", str(store_dir))
    g.close()
    backup_store(tmp_path / "solo-bak", store_path=str(store_dir))


def test_dump_store_via_store_path(tmp_path: Path) -> None:
    from triplemodel.io.stores import open_graph

    store_dir = tmp_path / "solo2"
    g = open_graph("disk", str(store_dir))
    g.store.add(
        Quad(NamedNode(f"{EX}s"), NamedNode(f"{EX}p"), Literal("v"), DefaultGraph())
    )
    g.close()
    dump_store(tmp_path / "solo2.nq", store_path=str(store_dir))


def test_coerce_graph_name_with_target() -> None:
    from triplemodel.store.ops import _coerce_graph_name

    node = _coerce_graph_name(None, f"{EX}g")
    assert isinstance(node, NamedNode)
    assert str(node.value).endswith("/g")


def test_formats_edge_cases() -> None:
    from triplemodel.store.formats import (
        format_from_hint,
        query_results_format_from_hint,
    )

    assert format_from_hint(None, "turtle") == "turtle"
    assert format_from_hint(None, None) is None
    assert format_from_hint("data.n3", None) == "n3"
    assert format_from_hint(Path("bundle.trig"), None) == "trig"
    with pytest.raises(ValueError, match="Cannot infer SPARQL"):
        query_results_format_from_hint("no-suffix", None)
    with pytest.raises(ValueError, match="Cannot infer SPARQL"):
        query_results_format_from_hint(None, None)


def test_query_results_suffix_hints(tmp_path: Path) -> None:
    from triplemodel.store.formats import query_results_format_from_hint

    assert (
        query_results_format_from_hint(tmp_path / "a.srx", None) == "sparql-results+xml"
    )
    assert query_results_format_from_hint(tmp_path / "b.csv", None) == "text/csv"
    assert (
        query_results_format_from_hint(tmp_path / "c.tsv", None)
        == "text/tab-separated-values"
    )


def test_load_store_rejects_both_source_and_data() -> None:
    graph = Graph()
    try:
        with pytest.raises(ValueError, match="not both"):
            load_store(graph, "x.nq", data=b"{}")
    finally:
        graph.close()


def test_optimize_store_store_path_only(tmp_path: Path) -> None:
    from triplemodel.io.stores import open_graph

    store_dir = tmp_path / "opt"
    g = open_graph("disk", str(store_dir))
    g.close()
    optimize_store(store_path=str(store_dir))


def test_rdf_format_to_name_unknown() -> None:
    from triplemodel.store.formats import rdf_format_to_name

    class FakeFormat:
        pass

    with pytest.raises(ValueError, match="Unsupported"):
        rdf_format_to_name(FakeFormat())  # ty: ignore[invalid-argument-type]
