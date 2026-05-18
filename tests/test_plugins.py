"""Tests for triplemodel.plugins."""

from __future__ import annotations

from triplemodel.fields.resolver import FieldPredicateResolver, default_resolver
from triplemodel.metadata.predicate_map import clear_predicate_map_cache
from triplemodel.plugins import register_predicate_resolver

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
