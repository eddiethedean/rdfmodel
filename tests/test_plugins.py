"""Tests for triplemodel.plugins."""

from __future__ import annotations

import pytest

from triplemodel.fields.resolver import FieldPredicateResolver, default_resolver
from triplemodel.metadata.predicate_map import clear_predicate_map_cache
from triplemodel.plugins import (
    register_parser,
    register_predicate_resolver,
    register_serializer,
    register_store,
)

EX = "http://example.org/"


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


def test_register_parser_removed_in_010():
    with pytest.raises(NotImplementedError, match="register_parser"):
        register_parser("x", "m", "C")


def test_register_serializer_removed_in_010():
    with pytest.raises(NotImplementedError, match="register_serializer"):
        register_serializer("x", "m", "C")


def test_register_store_removed_in_010():
    with pytest.raises(NotImplementedError, match="register_store"):
        register_store("x", "m", "C")
