"""Tests for cached predicate maps."""

from __future__ import annotations

from dataclasses import replace

from triplemodel import TripleModel, rdf_field
from triplemodel.config import get_rdf_config
from triplemodel.fields.resolver import FieldPredicateResolver
from triplemodel.metadata.predicate_map import (
    clear_predicate_map_cache,
    field_info_by_predicate,
    owned_predicates_for_class,
    predicate_map_for_class,
    uses_default_resolver,
)

EX = "http://example.org/"


class CachedPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def test_predicate_map_cached_for_default_resolver():
    clear_predicate_map_cache()
    m1 = predicate_map_for_class(CachedPerson)
    m2 = predicate_map_for_class(CachedPerson)
    assert m1 is not m2
    assert m1 == m2
    assert m1["name"] == f"{EX}name"


def test_predicate_map_bypasses_cache_for_custom_resolver():
    class AltResolver(FieldPredicateResolver):
        def resolve_field_predicate(self, field_info, prefixes):
            return f"{EX}alt"

        def owned_predicates(self, model_cls, config=None):
            return frozenset({f"{EX}alt"})

    alt = AltResolver()
    assert not uses_default_resolver(alt)
    m = predicate_map_for_class(CachedPerson, resolver=alt)
    assert m["name"] == f"{EX}alt"


def test_field_info_by_predicate():
    by_pred = field_info_by_predicate(CachedPerson)
    assert f"{EX}name" in by_pred


def test_owned_predicates_cached():
    clear_predicate_map_cache()
    o1 = owned_predicates_for_class(CachedPerson)
    o2 = owned_predicates_for_class(CachedPerson)
    assert o1 is o2
    assert f"{EX}name" in o1


def test_owned_predicates_honors_config_override():
    clear_predicate_map_cache()
    base = get_rdf_config(CachedPerson)
    custom = replace(base, instance_of=f"{EX}classifiedAs")
    owned_default = owned_predicates_for_class(CachedPerson)
    owned_custom = owned_predicates_for_class(CachedPerson, config=custom)
    assert f"{EX}classifiedAs" not in owned_default
    assert f"{EX}classifiedAs" in owned_custom
