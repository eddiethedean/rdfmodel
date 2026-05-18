"""Tests for RDFS subclass dispatch and transitive helpers."""

from __future__ import annotations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from triplemodel import TripleModel, graph_to_model_dispatch, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.rdfs import (
    resolve_model_class_with_rdfs,
    subject_type_closure,
    transitive_objects,
)
from triplemodel.protocols import resolve_model_class

EX = "http://ex.org/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str | None = rdf_field(f"{EX}name", default=None)


class Agent(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Agent"
        id_field = "slug"

    slug: str
    name: str | None = rdf_field(f"{EX}name", default=None)


def _subclass_graph() -> Graph:
    g = Graph()
    Person_t = URIRef(f"{EX}Person")
    Agent_t = URIRef(f"{EX}Agent")
    alice = URIRef(f"{EX}alice")
    g.add((Agent_t, RDFS.subClassOf, Person_t))
    g.add((alice, URIRef(RDF_TYPE), Agent_t))
    g.add((alice, URIRef(f"{EX}name"), Literal("Alice")))
    return g


def test_subject_type_closure():
    g = _subclass_graph()
    alice = URIRef(f"{EX}alice")
    closure = subject_type_closure(g, alice)
    assert f"{EX}Agent" in closure
    assert f"{EX}Person" in closure


def test_resolve_subclass_picks_agent():
    g = _subclass_graph()
    alice = URIRef(f"{EX}alice")
    cls = resolve_model_class_with_rdfs(g, alice)
    assert cls is Agent


def test_graph_to_model_dispatch_agent():
    g = _subclass_graph()
    inst = graph_to_model_dispatch(g, f"{EX}alice")
    assert isinstance(inst, Agent)
    assert inst.name == "Alice"


def test_resolve_exact_type_without_subclass():
    g = _subclass_graph()
    alice = URIRef(f"{EX}alice")
    cls = resolve_model_class(g, alice, use_subclass=False)
    assert cls is Agent


def test_transitive_objects_chain():
    g = Graph()
    a, b, c = URIRef(f"{EX}a"), URIRef(f"{EX}b"), URIRef(f"{EX}c")
    p = URIRef(f"{EX}partOf")
    g.add((a, p, b))
    g.add((b, p, c))
    objs = transitive_objects(g, a, str(p))
    assert str(c) in objs
