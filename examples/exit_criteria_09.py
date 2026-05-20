#!/usr/bin/env python3
"""0.10.0 exit criteria: pyoxigraph Store + disk store + API-freeze smoke."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from pyoxigraph import Literal, NamedNode

from triplemodel import Store, TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.stores import open_graph, store_commit
from triplemodel.plugins import register_predicate_resolver
from triplemodel.fields.resolver import FieldPredicateResolver

EX = "http://example.org/exit10/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def _memory_round_trip() -> None:
    g = Store()
    subj = NamedNode(f"{EX}alice")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
    g.add((subj, NamedNode(f"{EX}name"), Literal("Alice")))
    person = Person.from_graph(g, f"{EX}alice")
    assert person.name == "Alice"
    g2 = person.to_graph()
    assert len(g2) >= 2


def _disk_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store_dir = Path(tmp) / "store"
        graph = open_graph("disk", str(store_dir))
        alice = Person(slug="alice", name="Alice")
        alice.sync_to_graph(graph)
        store_commit(graph)
        del graph
        again = Person.all_from_graph(open_graph("disk", str(store_dir)))
        assert len(again) == 1 and again[0].name == "Alice"


def _predicate_resolver_smoke() -> None:
    original: FieldPredicateResolver | None = None
    try:
        from triplemodel.fields import resolver as resolver_mod

        original = resolver_mod.default_resolver

        class Alt(FieldPredicateResolver):
            def resolve_field_predicate(self, field_info, prefixes):
                return f"{EX}name"

            def owned_predicates(self, model_cls, config=None):
                return frozenset({f"{EX}name"})

        register_predicate_resolver(Alt)
    finally:
        if original is not None:
            import triplemodel.fields.resolver as resolver_mod

            resolver_mod.default_resolver = original


def main() -> int:
    _memory_round_trip()
    _disk_round_trip()
    _predicate_resolver_smoke()
    print("0.10.0 exit criteria OK: Store + disk store + plugins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
