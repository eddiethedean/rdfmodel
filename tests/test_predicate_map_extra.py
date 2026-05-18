"""Extra predicate_map coverage."""

from __future__ import annotations

from triplemodel import TripleModel, rdf_field
from triplemodel.fields.resolver import FieldPredicateResolver
from triplemodel.metadata.predicate_map import field_info_by_predicate

EX = "http://example.org/"


class MapModel(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}T"
        id_field = "slug"

    slug: str
    x: str = rdf_field(f"{EX}x")


class Alt(FieldPredicateResolver):
    def resolve_field_predicate(self, field_info, prefixes):
        return None

    def owned_predicates(self, model_cls, config=None):
        return frozenset()


def test_field_info_skips_unresolved_predicate():
    assert field_info_by_predicate(MapModel, resolver=Alt()) == {}
