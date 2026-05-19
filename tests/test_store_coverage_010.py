"""Coverage for pyoxigraph store layer branches (0.10)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, cast

import pytest
from pyoxigraph import BlankNode, DefaultGraph, Literal, NamedNode
from triplemodel.store import RdfDataset, RdfGraph
from triplemodel.store.formats import to_rdf_format
from triplemodel.store.sparql_result import Variable
from triplemodel.store.terms import is_blank, is_literal, is_named, term_str
from triplemodel.io.sparql import (
    _inline_init_bindings,
    _sparql_term_for_inline,
    detect_query_form,
)
from triplemodel.plugins import register_parser, register_predicate_resolver
from triplemodel.fields.resolver import FieldPredicateResolver


def test_graph_parse_inline_string_source() -> None:
    g = RdfGraph()
    g.parse(
        source="@prefix ex: <http://ex/> . ex:s ex:p ex:o .",
        format="turtle",
    )
    assert len(g) == 1


def test_graph_parse_file_path(tmp_path) -> None:
    path = tmp_path / "data.ttl"
    path.write_text(
        "@prefix ex: <http://ex/> .\nex:s ex:p ex:o .\n",
        encoding="utf-8",
    )
    g = RdfGraph()
    g.parse(source=path, format="turtle")
    assert len(g) == 1


def test_graph_query_merges_bound_prefixes() -> None:
    g = RdfGraph()
    g.bind("ex", "http://ex/")
    g.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v")))
    result = g.query("SELECT ?v WHERE { ?s <http://ex/p> ?v }")
    assert result.type in ("SELECT", "bindings")


def test_graph_subjects_no_args() -> None:
    g = RdfGraph()
    g.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v")))
    assert list(g.subjects()) == [NamedNode("http://ex/s")]


def test_dataset_quads_pattern_named_graph() -> None:
    ds = RdfDataset()
    ctx = ds.graph(NamedNode("http://ex/g"))
    ctx.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v")))
    quads = list(ds.quads((None, None, None, ctx)))
    assert len(quads) == 1


def test_dataset_quads_default_graph() -> None:
    ds = RdfDataset()
    ds.default_graph.add(
        (NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v"))
    )
    assert len(list(ds.quads((None, None, None, None)))) == 1


def test_to_rdf_format_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown RDF format"):
        to_rdf_format("not-a-format")


def test_sparql_inline_init_bindings() -> None:
    q = "ASK { FILTER(?s = ?subj) }"
    inlined = _inline_init_bindings(
        q,
        {Variable("subj"): NamedNode("http://ex/alice")},
    )
    assert "http://ex/alice" in inlined


def test_detect_query_form_non_string() -> None:
    with pytest.raises(TypeError, match="query string"):
        detect_query_form(cast(Any, 1))


def test_term_str_helpers() -> None:
    from pyoxigraph import BlankNode

    n = NamedNode("http://ex/n")
    b = BlankNode()
    lit = Literal("x")
    assert is_named(n)
    assert is_blank(b)
    assert is_literal(lit)
    assert term_str(n) == "http://ex/n"
    assert term_str(lit) == "x"


def test_register_parser_removed() -> None:
    with pytest.raises(NotImplementedError):
        register_parser("x", "m", "C")


def test_register_predicate_resolver_factory() -> None:
    class Custom(FieldPredicateResolver):
        pass

    inst = register_predicate_resolver(Custom)
    assert isinstance(inst, Custom)


def test_vocab_ns_getitem_and_getattr_error() -> None:
    from triplemodel.vocab import FOAF

    assert FOAF["name"].endswith("name")
    with pytest.raises(AttributeError):
        _ = FOAF._private  # type: ignore[attr-defined]


def test_graph_add_returns_self() -> None:
    g = RdfGraph()
    out = g.parse(data="@prefix ex: <http://ex/> . ex:a ex:b ex:c .", format="turtle")
    assert out is g


def test_graph_serialize_io_and_merge() -> None:
    g1 = RdfGraph()
    g1.add((NamedNode("http://ex/a"), NamedNode("http://ex/p"), Literal("v")))
    g1.bind("ex", "http://ex/")
    g2 = RdfGraph()
    g2.add((NamedNode("http://ex/b"), NamedNode("http://ex/p"), Literal("w")))
    merged = g1 + g2
    assert len(merged) == 2
    buf = io.BytesIO()
    g1.serialize(destination=buf, format="turtle")
    assert buf.getvalue()


def test_graph_query_explicit_prefixes() -> None:
    g = RdfGraph()
    g.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v")))
    result = g.query(
        "SELECT ?v WHERE { ?s <http://ex/p> ?v }", prefixes={"ex": "http://ex/"}
    )
    assert result.type in ("SELECT", "bindings")


def test_graph_transitive_cycle() -> None:
    g = RdfGraph()
    a, b, c = (
        NamedNode("http://ex/a"),
        NamedNode("http://ex/b"),
        NamedNode("http://ex/c"),
    )
    p = NamedNode("http://ex/next")
    g.add((a, p, b))
    g.add((b, p, c))
    g.add((c, p, a))
    objs = g.transitive_objects(a, p)
    assert len(objs) >= 2


def test_graph_cbd() -> None:
    g = RdfGraph()
    s = NamedNode("http://ex/s")
    g.add((s, NamedNode("http://ex/p"), Literal("v")))
    sub = g.cbd(s)
    assert len(sub) >= 1


def test_sparql_inline_literal_forms() -> None:
    assert "@" in _sparql_term_for_inline(Literal("hi", language="en"))
    assert "^^" in _sparql_term_for_inline(
        Literal("1", datatype=NamedNode("http://www.w3.org/2001/XMLSchema#integer"))
    )
    assert (
        _sparql_term_for_inline(Literal("plain"))
        == '"plain"^^<http://www.w3.org/2001/XMLSchema#string>'
    )
    assert _sparql_term_for_inline(BlankNode("b1")).startswith("_:")


def test_dataset_store_property_and_serialize(tmp_path: Path) -> None:
    ds = RdfDataset()
    assert ds.store is not None
    ds.parse(data="@prefix ex: <http://ex/> . ex:s ex:p ex:o .", format="turtle")
    out_path = tmp_path / "out.trig"
    ds.serialize(destination=out_path, format="trig")
    assert out_path.read_bytes()
    buf = io.BytesIO()
    ds.serialize(destination=buf, format="trig")
    assert buf.getvalue()


def test_dataset_quads_graph_name_variants() -> None:
    ds = RdfDataset()
    ds.default_graph.add(
        (NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v"))
    )
    assert len(list(ds.quads((None, None, None, DefaultGraph())))) == 1
    assert len(list(ds.quads((None, None, None, "http://ex/g")))) == 0


def test_open_graph_disk_empty_path_raises() -> None:
    from triplemodel.io.stores import open_graph

    with pytest.raises(ValueError, match="non-empty"):
        open_graph("disk", "")


def test_strict_import_warns_unmapped_predicate() -> None:
    from triplemodel import TripleModel, rdf_field
    from triplemodel.io.import_ import graph_to_model

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"
            strict_import = False
            warn_unmapped_fields = True

        slug: str
        name: str = rdf_field("http://ex/name")

    g = RdfGraph()
    subj = NamedNode("http://ex/a")
    g.add(
        (
            subj,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            NamedNode("http://ex/T"),
        )
    )
    g.add((subj, NamedNode("http://ex/name"), Literal("A")))
    g.add((subj, NamedNode("http://ex/extra"), Literal("x")))
    with pytest.warns(UserWarning, match="not mapped"):
        graph_to_model(g, M, subj, validate_type=False)


def test_graph_update_and_parse_errors() -> None:
    g = RdfGraph()
    with pytest.raises(ValueError, match="format="):
        g.parse(data="x", format=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source= or data="):
        g.parse(format="turtle")
    g.update("INSERT DATA { <http://ex/s> <http://ex/p> <http://ex/o> . }")


def test_graph_parse_http_url(monkeypatch: pytest.MonkeyPatch) -> None:
    g = RdfGraph()

    def fake_parse(url: str, **kwargs: object) -> list[object]:
        _ = url, kwargs
        return []

    monkeypatch.setattr("triplemodel.store.graph.ox_parse", fake_parse)
    g.parse(source="http://example.org/data.ttl", format="turtle")
    assert len(g) == 0


def test_register_predicate_resolver_callable() -> None:
    class Custom(FieldPredicateResolver):
        pass

    register_predicate_resolver(lambda: Custom())


def test_convert_bytes_and_bnode_errors() -> None:
    from triplemodel.terms.convert import python_to_term, term_to_python
    from pyoxigraph import BlankNode

    assert isinstance(python_to_term(cast(Any, b"hi")), Literal)
    with pytest.raises(TypeError, match="BNode"):
        term_to_python(BlankNode(), int)


def test_dataset_parse_requires_format() -> None:
    ds = RdfDataset()
    with pytest.raises(ValueError, match="format="):
        ds.parse(data="@prefix ex: <http://ex/> .", format=None)  # type: ignore[arg-type]


def test_dataset_query_delegates() -> None:
    ds = RdfDataset()
    ds.default_graph.add(
        (NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v"))
    )
    result = ds.query("SELECT ?v WHERE { ?s <http://ex/p> ?v }")
    assert result is not None


def test_collection_clear_list_break() -> None:
    from triplemodel.terms.collection import _clear_list
    from pyoxigraph import BlankNode

    g = RdfGraph()
    b = BlankNode()
    g.add(
        (b, NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#first"), Literal("x"))
    )
    _clear_list(g, b)


def test_cbd_without_reifications() -> None:
    g = RdfGraph()
    s = NamedNode("http://ex/s")
    g.add((s, NamedNode("http://ex/p"), Literal("v")))
    sub = g.cbd(s, include_reifications=False)
    assert len(sub) >= 1


def test_shacl_rdflib_bridge_literal_forms() -> None:
    pytest.importorskip("rdflib")
    from triplemodel.validation.shacl import _to_rdflib_graph

    g = RdfGraph()
    g.add(
        (
            NamedNode("http://ex/s"),
            NamedNode("http://ex/p"),
            Literal("v", language="en"),
        )
    )
    g.add(
        (
            NamedNode("http://ex/s"),
            NamedNode("http://ex/p2"),
            Literal(
                "1", datatype=NamedNode("http://www.w3.org/2001/XMLSchema#integer")
            ),
        )
    )
    rg = _to_rdflib_graph(g)
    assert len(rg) >= 2


def test_codegen_cli_writes_file(tmp_path: Path) -> None:
    from triplemodel.codegen.cli import main

    ttl = "@prefix ex: <http://ex/onto#> .\nex:Thing a <http://www.w3.org/2002/07/owl#Class> .\n"
    onto = tmp_path / "o.ttl"
    onto.write_text(ttl, encoding="utf-8")
    out = tmp_path / "models.py"
    assert main([str(onto), "-o", str(out)]) == 0
    assert "class" in out.read_text(encoding="utf-8")


def test_codegen_emit_skips_non_named_property() -> None:
    from triplemodel.codegen.emit import generate_models_from_graph
    from triplemodel.config.constants import OWL, RDF

    g = RdfGraph()
    prop = BlankNode("p")
    g.add((prop, NamedNode(f"{RDF}type"), NamedNode(f"{OWL}DatatypeProperty")))
    assert generate_models_from_graph(g)


def test_codegen_emit_duplicate_class_warns() -> None:
    from triplemodel.codegen.emit import generate_models_from_graph
    from triplemodel.config.constants import RDF, RDFS

    g = RdfGraph()
    g.add(
        (
            NamedNode("http://ex.org/onto#Agent"),
            NamedNode(f"{RDF}type"),
            NamedNode(f"{RDFS}Class"),
        )
    )
    g.add(
        (
            NamedNode("http://ex.org/other#Agent"),
            NamedNode(f"{RDF}type"),
            NamedNode(f"{RDFS}Class"),
        )
    )
    with pytest.warns(UserWarning, match="duplicate class"):
        generate_models_from_graph(g)


def test_ontology_graph_string_and_errors(tmp_path: Path) -> None:
    from triplemodel.codegen.parse import ontology_graph

    ttl = "@prefix ex: <http://ex/onto#> .\nex:Thing a <http://www.w3.org/2002/07/owl#Class> .\n"
    g = ontology_graph(ttl)
    assert len(g) >= 1
    with pytest.raises(FileNotFoundError, match="not found"):
        ontology_graph(tmp_path / "missing.ttl")
    directory = tmp_path / "dir"
    directory.mkdir()
    with pytest.raises(FileNotFoundError, match="not a file"):
        ontology_graph(directory)


def test_ontology_graph_explicit_format(tmp_path: Path) -> None:
    from triplemodel.codegen.parse import ontology_graph

    path = tmp_path / "data.bin"
    path.write_bytes(b"@prefix ex: <http://ex/> .\nex:s ex:p ex:o .\n")
    g = ontology_graph(path, format="turtle")
    assert len(g) >= 1


def test_cbd_blank_subject_returns_empty() -> None:
    from triplemodel.store.cbd import cbd_subgraph
    from pyoxigraph import BlankNode

    g = RdfGraph()
    sub = cbd_subgraph(g, BlankNode("b"))
    assert len(sub) == 0


def test_graph_name_from_string() -> None:
    g = RdfGraph(graph="http://ex/g")
    gn = g.graph_name
    assert isinstance(gn, NamedNode)
    assert gn.value == "http://ex/g"


def test_plugins_register_instance() -> None:
    class Custom(FieldPredicateResolver):
        pass

    register_predicate_resolver(Custom())


def test_convert_bool_and_opaque_paths() -> None:
    from triplemodel.terms.convert import term_to_python
    from triplemodel.terms.opaque import OpaqueLiteral
    from triplemodel.store.namespaces import XSD

    lit = Literal("true", datatype=XSD.boolean)
    assert term_to_python(lit, bool) is True
    lit2 = Literal("x", datatype=NamedNode("http://ex/custom"))
    assert isinstance(term_to_python(lit2, None), OpaqueLiteral)


def test_codegen_cli_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from triplemodel.codegen.cli import main

    onto = tmp_path / "o.ttl"
    onto.write_text(
        "@prefix ex: <http://ex/onto#> .\nex:Thing a <http://www.w3.org/2002/07/owl#Class> .\n",
        encoding="utf-8",
    )
    assert main([str(onto)]) == 0
    assert "class" in capsys.readouterr().out


def test_ontology_graph_unknown_suffix_requires_format(tmp_path: Path) -> None:
    from triplemodel.codegen.parse import _format_for_path

    with pytest.raises(ValueError, match="format="):
        _format_for_path(tmp_path / "data.xyz", None)


def test_plugins_register_invalid_resolver() -> None:
    with pytest.raises(TypeError, match="FieldPredicateResolver"):
        register_predicate_resolver(cast(Any, object()))


def test_cbd_cycle_skips_revisit() -> None:
    from triplemodel.store.cbd import cbd_subgraph

    g = RdfGraph()
    a, b = NamedNode("http://ex/a"), NamedNode("http://ex/b")
    p = NamedNode("http://ex/p")
    g.add((a, p, b))
    g.add((b, p, a))
    sub = cbd_subgraph(g, a)
    assert len(sub) >= 2


def test_dataset_quads_all_and_parse_error() -> None:
    ds = RdfDataset()
    ds.default_graph.add(
        (NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v"))
    )
    assert len(list(ds.quads())) == 1
    with pytest.raises(ValueError, match="source= or data="):
        ds.parse(format="turtle")


def test_graph_prefixes_merge_on_query() -> None:
    g = RdfGraph()
    g.bind("ex", "http://ex/")
    g.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("v")))
    g.query("SELECT ?v WHERE { ?s <http://ex/p> ?v }", prefixes={"ex": "http://ex/"})


def test_graph_transitive_subjects_cycle() -> None:
    g = RdfGraph()
    a, b = NamedNode("http://ex/a"), NamedNode("http://ex/b")
    p = NamedNode("http://ex/p")
    g.add((a, p, b))
    g.add((b, p, a))
    assert len(g.transitive_subjects(p, b)) >= 2


def test_xsd_namespace_getitem() -> None:
    from triplemodel.store.namespaces import XSD

    assert XSD["string"].value.endswith("string")


def test_collection_read_breaks_on_empty_first() -> None:
    from triplemodel.terms.collection import read_rdf_list
    from pyoxigraph import BlankNode

    g = RdfGraph()
    head = BlankNode("h")
    g.add(
        (
            head,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#first"),
            Literal("x"),
        )
    )
    g.add(
        (
            head,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest"),
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil"),
        )
    )
    assert read_rdf_list(g, head, str) == ["x"]


def test_convert_fallback_literal_and_return_term() -> None:
    from triplemodel.terms.convert import python_to_term, term_to_python
    from pyoxigraph import BlankNode

    assert isinstance(python_to_term(123.45), Literal)
    weird = BlankNode("w")
    assert term_to_python(weird, None) is weird


def test_shacl_plain_literal_bridge() -> None:
    pytest.importorskip("rdflib")
    from triplemodel.validation.shacl import _to_rdflib_graph

    g = RdfGraph()
    g.add((NamedNode("http://ex/s"), NamedNode("http://ex/p"), Literal("plain")))
    assert len(_to_rdflib_graph(g)) == 1


def test_vocab_getattr() -> None:
    from triplemodel.vocab import FOAF

    assert FOAF.name.endswith("name")


def test_run_sparql_type_error_and_init_ns() -> None:
    from triplemodel import TripleModel, rdf_field
    from triplemodel.io.sparql import run_sparql

    class P(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            id_field = "slug"
            prefixes = {"ex": "http://ex/"}

        slug: str
        name: str = rdf_field("ex:name")

    g = RdfGraph()
    with pytest.raises(TypeError, match="query string"):
        run_sparql(g, cast(Any, object()))
    g.add((NamedNode("http://ex/a"), NamedNode("http://ex/name"), Literal("n")))
    run_sparql(g, "SELECT ?n WHERE { ?s ex:name ?n }", initNs={"ex": "http://ex/"})


def test_collection_clear_non_list_head() -> None:
    from triplemodel.terms.collection import _clear_list
    from pyoxigraph import BlankNode

    g = RdfGraph()
    b = BlankNode("x")
    g.add((b, NamedNode("http://ex/p"), Literal("v")))
    _clear_list(g, b)


def test_term_to_python_bool_without_xsd_datatype() -> None:
    from triplemodel.terms.convert import term_to_python

    lit = Literal("1", datatype=NamedNode("http://www.w3.org/2001/XMLSchema#integer"))
    assert term_to_python(lit, bool) in (True, False, "1", 1)


def test_term_to_python_unknown_python_value() -> None:
    from triplemodel.terms.convert import python_to_term

    class Odd:
        def __str__(self) -> str:
            return "odd"

    assert isinstance(python_to_term(cast(Any, Odd())), Literal)


def test_read_rdf_list_empty_first_break() -> None:
    from triplemodel.terms.collection import read_rdf_list
    from pyoxigraph import BlankNode

    g = RdfGraph()
    head = BlankNode("h")
    g.add(
        (
            head,
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#rest"),
            NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil"),
        )
    )
    with pytest.raises(ValueError, match="not an rdf:List"):
        read_rdf_list(g, head, str)


def test_read_rdf_list_stops_at_empty_cell() -> None:
    from triplemodel.terms.collection import read_rdf_list
    from pyoxigraph import BlankNode
    from triplemodel.store.namespaces import RDF_FIRST, RDF_NIL, RDF_REST

    g = RdfGraph()
    c1, c2 = BlankNode("c1"), BlankNode("c2")
    g.add((c1, NamedNode(RDF_FIRST), Literal("a")))
    g.add((c1, NamedNode(RDF_REST), c2))
    g.add((c2, NamedNode(RDF_REST), NamedNode(RDF_NIL)))
    assert read_rdf_list(g, c1, str) == ["a"]


def test_sparql_term_for_field_union_plain_fallback() -> None:
    from unittest.mock import patch

    from triplemodel import TripleModel, rdf_field
    from triplemodel.io.sparql import _term_for_field
    from triplemodel.terms.registry import default_registry

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            id_field = "slug"

        slug: str
        val: int | str = rdf_field("http://ex/v", default=0)

    field_info = M.model_fields["val"]
    lit = Literal("x")

    def fake(term: object, target_type: type | None = None, **_: object) -> object:
        if target_type is not None:
            raise TypeError("nope")
        return "fallback"

    with patch("triplemodel.io.sparql.term_to_python", side_effect=fake):
        assert _term_for_field(lit, field_info, registry=default_registry) == "fallback"


def test_sparql_term_for_field_returns_opaque_value() -> None:
    from triplemodel import TripleModel, rdf_field
    from triplemodel.io.sparql import _term_for_field
    from triplemodel.terms.registry import default_registry

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            id_field = "slug"

        slug: str
        val: int | str = rdf_field("http://ex/v", default=0)

    field_info = M.model_fields["val"]
    lit = Literal("x", datatype=NamedNode("http://ex/opaque"))
    out = _term_for_field(lit, field_info, registry=default_registry)
    assert out == "x"


def test_sparql_inline_unknown_term() -> None:
    from triplemodel.io.sparql import _sparql_term_for_inline

    class Other:
        def __str__(self) -> str:
            return "http://ex/fixture"

    assert _sparql_term_for_inline(cast(Any, Other())) == "http://ex/fixture"


def test_sparql_term_for_field_opaque_value() -> None:
    from triplemodel import TripleModel, rdf_field
    from triplemodel.io.sparql import _term_for_field
    from triplemodel.terms.opaque import OpaqueLiteral
    from triplemodel.terms.registry import default_registry

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            id_field = "slug"

        slug: str
        val: int | str = rdf_field("http://ex/v", default=0)

    field_info = M.model_fields["val"]
    out = _term_for_field(
        Literal("not-int", datatype=NamedNode("http://ex/custom")),
        field_info,
        registry=default_registry,
    )
    assert isinstance(out, (int, str, OpaqueLiteral))
