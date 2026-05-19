#!/usr/bin/env python3
"""0.6.0 exit criteria: CONSTRUCT via SPARQL helpers (local graph)."""

from __future__ import annotations

from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF

EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


def main() -> None:
    graph = Graph()
    graph.bind("foaf", FOAF)
    alice = NamedNode(f"{EX}alice")
    graph.add((alice, NamedNode(RDF_TYPE), NamedNode(f"{FOAF}Person")))
    graph.add((alice, NamedNode(f"{FOAF}name"), Literal("Alice")))

    people = Person.construct_from_sparql(
        graph,
        """
        CONSTRUCT { ?s ?p ?o }
        WHERE { ?s a foaf:Person . ?s ?p ?o . }
        """,
    )
    assert len(people) == 1
    assert people[0].name == "Alice"

    # Remote endpoint (uncomment to run against DBpedia):
    # people = Person.load_sparql(
    #     "https://dbpedia.org/sparql",
    #     """CONSTRUCT { ?s ?p ?o } WHERE {
    #          ?s a <http://xmlns.com/foaf/0.1/Person> .
    #          ?s <http://xmlns.com/foaf/0.1/name> ?n . ?s ?p ?o
    #        } LIMIT 3""",
    # )

    print("0.6.0 SPARQL CONSTRUCT example OK")


if __name__ == "__main__":
    main()
