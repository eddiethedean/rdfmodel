"""Tests for triplemodel.plugins."""

from __future__ import annotations

import sys
import types

import pytest
from rdflib import Graph
from rdflib.parser import Parser
from rdflib.plugin import get
from rdflib.serializer import Serializer
from rdflib.store import Store

from triplemodel.fields.resolver import FieldPredicateResolver, default_resolver
from triplemodel.metadata.predicate_map import clear_predicate_map_cache
from triplemodel.plugins import (
    register_parser,
    register_predicate_resolver,
    register_serializer,
    register_store,
)

EX = "http://example.org/"
_PARSER = "triplemodel-test-parser"
_SERIALIZER = "triplemodel-test-serializer"
_STORE = "triplemodel-test-memory"


def test_register_predicate_resolver_replaces_default():
    clear_predicate_map_cache()
    original = default_resolver

    class Alt(FieldPredicateResolver):
        def resolve_field_predicate(self, field_info, prefixes):
            return f"{EX}alt"

        def owned_predicates(self, model_cls, config=None):
            return frozenset({f"{EX}alt"})

    try:
        inst = register_predicate_resolver(Alt)
        assert inst is not None
        from triplemodel.fields.resolver import default_resolver as current

        assert current is inst
    finally:
        import triplemodel.fields.resolver as mod

        mod.default_resolver = original
        clear_predicate_map_cache()


def test_register_parser_serializer_store_passthrough():
    from tests import _rdflib_plugin_fixtures as fixtures

    mod = types.ModuleType("triplemodel_test_rdflib_plugins")
    mod.MinimalTestParser = fixtures.MinimalTestParser  # ty: ignore[unresolved-attribute]
    mod.MinimalTestSerializer = fixtures.MinimalTestSerializer  # ty: ignore[unresolved-attribute]
    sys.modules[mod.__name__] = mod

    register_parser(_PARSER, mod.__name__, "MinimalTestParser")
    register_serializer(_SERIALIZER, mod.__name__, "MinimalTestSerializer")
    register_store(_STORE, "rdflib.plugins.stores.memory", "Memory")

    assert get(_PARSER, Parser) is not None
    assert get(_SERIALIZER, Serializer) is not None
    assert get(_STORE, Store) is not None

    g = Graph()
    g.parse(
        data='<http://ex/s> <http://ex/p> "v" .',
        format=_PARSER,
    )
    assert len(g) == 1

    g2 = Graph(store=_STORE)
    assert g2.store is not None


def test_register_predicate_resolver_factory_and_instance():
    clear_predicate_map_cache()
    original = default_resolver

    class Alt(FieldPredicateResolver):
        def resolve_field_predicate(self, field_info, prefixes):
            return f"{EX}factory"

        def owned_predicates(self, model_cls, config=None):
            return frozenset()

    def factory() -> Alt:
        return Alt()

    try:
        inst = register_predicate_resolver(factory)
        assert isinstance(inst, Alt)
        register_predicate_resolver(Alt())
        from triplemodel.fields.resolver import default_resolver as current

        assert isinstance(current, Alt)
    finally:
        import triplemodel.fields.resolver as mod

        mod.default_resolver = original
        clear_predicate_map_cache()


def test_register_predicate_resolver_type_error():
    with pytest.raises(TypeError, match="FieldPredicateResolver"):
        register_predicate_resolver(object())  # ty: ignore[invalid-argument-type]
