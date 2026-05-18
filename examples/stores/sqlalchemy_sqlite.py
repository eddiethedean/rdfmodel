#!/usr/bin/env python3
"""SQLAlchemy-backed sqlite graph with TripleModel round-trip."""

from __future__ import annotations

import tempfile
from pathlib import Path

from triplemodel import TripleModel, rdf_field
from triplemodel.io.stores import graph_store_session, open_graph, store_commit
from triplemodel.vocab import FOAF

EX = "http://example.org/people/"
FOAF_PERSON = f"{FOAF}Person"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = FOAF_PERSON
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "graph.sqlite"
        ident = f"sqlite:///{db}"
        graph = open_graph("sqlalchemy", ident)
        with graph_store_session(graph):
            alice = Person(slug="alice", name="Alice")
            alice.sync_to_graph(graph)
            store_commit(graph)
        graph2 = open_graph("sqlalchemy", ident)
        people = Person.all_from_graph(graph2)
        assert len(people) == 1 and people[0].name == "Alice"
        print("SQLAlchemy sqlite store round-trip OK")


if __name__ == "__main__":
    main()
