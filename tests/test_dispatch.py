"""Subclass dispatch by rdf:type."""

from __future__ import annotations

import warnings

from rdflib import Graph, Literal, URIRef

from triplemodel import (
    TripleModel,
    graph_to_model_dispatch,
    rdf_field,
    resolve_model_class,
)
from triplemodel.io.dispatch import all_from_graph_dispatch
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field("foaf:name")


class Agent(Person):
    class Rdf:
        namespace = EX
        type_uri = "http://example.org/Agent"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}

    role: str = rdf_field("http://example.org/role")


def test_resolve_most_specific_class() -> None:
    g = Graph()
    subj = URIRef(f"{EX}alice")
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF_NS}Person")))
    g.add((subj, URIRef(RDF_TYPE), URIRef("http://example.org/Agent")))
    g.add((subj, URIRef("http://xmlns.com/foaf/0.1/name"), Literal("Alice")))
    g.add((subj, URIRef("http://example.org/role"), Literal("admin")))

    cls = resolve_model_class(g, subj)
    assert cls is Agent

    model = graph_to_model_dispatch(g, subj)
    assert isinstance(model, Agent)
    assert model.role == "admin"


def test_all_from_graph_dispatch_dedupes_subject() -> None:
    from unittest.mock import patch

    subj = URIRef(f"{EX}bob")
    g = Graph()
    g.add((subj, URIRef(f"{FOAF_NS}name"), Literal("Bob")))
    g.add((subj, URIRef("http://example.org/role"), Literal("editor")))
    g.add((subj, URIRef(RDF_TYPE), URIRef("http://example.org/Agent")))
    g.add((subj, URIRef(RDF_TYPE), URIRef(f"{FOAF_NS}Person")))

    with patch(
        "triplemodel.protocols.iter_registered_type_uris",
        return_value=frozenset({f"{FOAF_NS}Person", "http://example.org/Agent"}),
    ):
        loaded = all_from_graph_dispatch(g)
    assert len(loaded) == 1


def test_all_from_graph_dispatch_skips_non_node_subjects() -> None:
    from rdflib import Literal

    from triplemodel.config import RDF_TYPE

    g = Graph()
    g.add(
        (Literal("not-a-subject"), URIRef(RDF_TYPE), URIRef("http://example.org/Agent"))
    )
    g.add((URIRef(f"{EX}bob"), URIRef(RDF_TYPE), URIRef("http://example.org/Agent")))
    g.add((URIRef(f"{EX}bob"), URIRef(f"{FOAF_NS}name"), Literal("Bob")))
    g.add((URIRef(f"{EX}bob"), URIRef("http://example.org/role"), Literal("r")))
    loaded = all_from_graph_dispatch(g)
    assert len(loaded) == 1


def test_parse_dispatch() -> None:
    agent = Agent(slug="bob", name="Bob", role="editor")
    ttl = agent.serialize(format="turtle")
    loaded = TripleModel.parse(data=ttl, format="turtle", dispatch=True)
    assert len(loaded) == 1
    assert isinstance(loaded[0], Agent)
    assert loaded[0].role == "editor"


def test_duplicate_type_uri_registration_warns() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class DuplicateA(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = "http://example.org/DuplicateType"
                id_field = "slug"

            slug: str

        class DuplicateB(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = "http://example.org/DuplicateType"
                id_field = "slug"

            slug: str

    assert len(w) == 1
    msg = str(w[0].message)
    assert "DuplicateType" in msg
    assert "DuplicateA" in msg
    assert "DuplicateB" in msg
