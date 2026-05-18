"""Additional store and plugin coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph

from triplemodel.codegen.cli import main
from triplemodel.io.stores import destroy_store, open_graph
from triplemodel.plugins import register_predicate_resolver


def test_open_graph_sparql_delegates():
    with patch("triplemodel.io.sparql.open_sparql_graph") as mock_open:
        mock_open.return_value = Graph()
        g = open_graph("sparql", "http://example.invalid/sparql", read_only=True)
        mock_open.assert_called_once()
        assert isinstance(g, Graph)


def test_destroy_store_no_destroy_method():
    graph = MagicMock()
    graph.store.destroy = None
    with patch("triplemodel.io.stores.Graph", return_value=graph):
        with pytest.raises(ValueError, match="does not support destroy"):
            destroy_store("id", store="sqlalchemy")


def test_register_predicate_resolver_type_error():
    with pytest.raises(TypeError, match="FieldPredicateResolver"):
        register_predicate_resolver(object())  # ty: ignore[invalid-argument-type]


def test_register_predicate_resolver_factory():
    from triplemodel.fields.resolver import FieldPredicateResolver, default_resolver
    from triplemodel.metadata.predicate_map import clear_predicate_map_cache

    class Alt(FieldPredicateResolver):
        def resolve_field_predicate(self, field_info, prefixes):
            return "http://example.org/p"

        def owned_predicates(self, model_cls, config=None):
            return frozenset()

    original = default_resolver
    try:
        register_predicate_resolver(lambda: Alt())
        from triplemodel.fields.resolver import default_resolver as current

        assert isinstance(current, Alt)
    finally:
        import triplemodel.fields.resolver as mod

        mod.default_resolver = original
        clear_predicate_map_cache()


def test_codegen_cli_stdout(tmp_path):
    onto = tmp_path / "o.ttl"
    onto.write_text(
        "@prefix ex: <http://example.org/onto#> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "ex:Person a owl:Class .\n",
        encoding="utf-8",
    )
    assert main([str(onto)]) == 0


def test_predicate_map_custom_owned():
    from triplemodel import TripleModel, rdf_field
    from triplemodel.fields.resolver import FieldPredicateResolver
    from triplemodel.metadata.predicate_map import owned_predicates_for_class

    EX = "http://example.org/"

    class M(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}T"
            id_field = "slug"

        slug: str
        x: str = rdf_field(f"{EX}x")

    class Alt(FieldPredicateResolver):
        def resolve_field_predicate(self, field_info, prefixes):
            return f"{EX}p"

        def owned_predicates(self, model_cls, config=None):
            return frozenset({f"{EX}p"})

    owned = owned_predicates_for_class(M, resolver=Alt())
    assert f"{EX}p" in owned
