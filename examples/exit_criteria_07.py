#!/usr/bin/env python3
"""0.7.0 exit criteria: CBD subgraph import and RDFS subclass dispatch."""

from __future__ import annotations

from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, graph_to_model_dispatch, rdf_field
from triplemodel.config import RDF_TYPE, RDFS
from triplemodel.vocab import FOAF

EX = "http://example.org/people/"
FOAF_PERSON = f"{FOAF}Person"
FOAF_AGENT = f"{FOAF}Agent"
FOAF_NAME = f"{FOAF}name"
FOAF_KNOWS = f"{FOAF}knows"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = FOAF_PERSON
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


class Agent(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = FOAF_AGENT
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


def main() -> None:
    g = Graph()
    g.bind("foaf", FOAF)
    Person_t = NamedNode(FOAF_PERSON)
    Agent_t = NamedNode(FOAF_AGENT)
    g.add((Agent_t, NamedNode(f"{RDFS}subClassOf"), Person_t))

    alice = NamedNode(f"{EX}alice")
    bob = NamedNode(f"{EX}bob")
    g.add((alice, NamedNode(RDF_TYPE), Agent_t))
    g.add((alice, NamedNode(FOAF_NAME), Literal("Alice")))
    g.add((alice, NamedNode(FOAF_KNOWS), bob))
    g.add((bob, NamedNode(FOAF_NAME), Literal("Bob")))

    agent = graph_to_model_dispatch(g, alice)
    assert isinstance(agent, Agent)
    assert agent.name == "Alice"

    from_cbd = Agent.cbd(g, alice)
    assert from_cbd.name == "Alice"

    print("0.7.0 CBD + RDFS subclass dispatch OK")


if __name__ == "__main__":
    main()
