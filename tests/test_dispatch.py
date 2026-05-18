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
from triplemodel import get_graph_context
from triplemodel.io.dispatch import (
    all_from_dataset_dispatch,
    all_from_graph_dispatch,
    graph_to_model_dispatch_from_dataset,
)
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF
from rdflib import Dataset

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"
DISPATCH_GRAPH = "http://example.org/graph/dispatch"


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


class DispatchPerson(TripleModel):
    class Rdf:
        namespace = "http://example.org/dispatch-people/"
        type_uri = "http://example.org/DispatchPerson"
        id_field = "slug"
        graph_iri = DISPATCH_GRAPH
        prefixes = {"foaf": FOAF_NS}

    slug: str
    name: str = rdf_field("foaf:name")


class DispatchAgent(DispatchPerson):
    class Rdf:
        namespace = "http://example.org/dispatch-people/"
        type_uri = "http://example.org/DispatchAgent"
        id_field = "slug"
        graph_iri = DISPATCH_GRAPH
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


def test_all_from_dataset_dispatch_dedupes_subject() -> None:
    from unittest.mock import patch

    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(DispatchPerson)
    register_rdf_resource(DispatchAgent)
    subj = URIRef("http://example.org/dispatch-people/bob")
    ds = Dataset()
    ctx = get_graph_context(ds, DISPATCH_GRAPH)
    ctx.add((subj, URIRef(RDF_TYPE), URIRef("http://example.org/DispatchAgent")))
    ctx.add((subj, URIRef(RDF_TYPE), URIRef("http://example.org/DispatchPerson")))
    ctx.add((subj, URIRef(f"{FOAF_NS}name"), Literal("Bob")))
    ctx.add((subj, URIRef("http://example.org/role"), Literal("editor")))
    with patch(
        "triplemodel.io.dispatch.iter_registered_type_uris",
        return_value=frozenset(
            {"http://example.org/DispatchPerson", "http://example.org/DispatchAgent"}
        ),
    ):
        loaded = all_from_dataset_dispatch(ds)
    assert len(loaded) == 1
    assert isinstance(loaded[0], DispatchAgent)
    assert loaded[0].role == "editor"


def test_parse_dataset_dispatch_dedupes() -> None:
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(DispatchAgent)
    agent = DispatchAgent(slug="bob", name="Bob", role="editor")
    trig = agent.serialize(format="trig")
    loaded = TripleModel.parse(data=trig, format="trig", dispatch=True)
    assert len(loaded) == 1
    assert isinstance(loaded[0], DispatchAgent)


def test_dispatch_from_dataset_unions_types_across_graphs() -> None:
    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(DispatchPerson)
    uri = URIRef("http://example.org/dispatch-people/crossgraph")
    ds = Dataset()
    default_ctx = get_graph_context(ds, None)
    named_ctx = get_graph_context(ds, DISPATCH_GRAPH)
    default_ctx.add((uri, URIRef(f"{FOAF_NS}name"), Literal("Cross")))
    named_ctx.add((uri, URIRef(RDF_TYPE), URIRef("http://example.org/DispatchPerson")))
    named_ctx.add((uri, URIRef(f"{FOAF_NS}name"), Literal("Cross")))
    m = graph_to_model_dispatch_from_dataset(ds, uri)
    assert isinstance(m, DispatchPerson)
    assert m.name == "Cross"


def test_all_from_dataset_dispatch_skips_unregistered_type_uri() -> None:
    from unittest.mock import patch

    agent = DispatchAgent(slug="bob", name="Bob", role="editor")
    ds = agent.to_dataset()
    with patch(
        "triplemodel.io.dispatch.iter_registered_type_uris",
        return_value=frozenset({"http://example.org/NotRegistered"}),
    ):
        loaded = all_from_dataset_dispatch(ds)
    assert loaded == []


def test_all_from_dataset_dispatch_skips_non_uri_subjects() -> None:
    from rdflib import BNode

    from triplemodel.protocols import register_rdf_resource

    register_rdf_resource(DispatchAgent)
    ds = Dataset()
    ctx = get_graph_context(ds, DISPATCH_GRAPH)
    bnode = BNode()
    ctx.add((bnode, URIRef(RDF_TYPE), URIRef("http://example.org/DispatchAgent")))
    ctx.add(
        (
            Literal("not-a-uri-subject"),
            URIRef(RDF_TYPE),
            URIRef("http://example.org/DispatchAgent"),
        )
    )
    loaded = all_from_dataset_dispatch(ds)
    assert loaded == []


def test_iter_registered_model_classes() -> None:
    from triplemodel.protocols import iter_registered_model_classes

    classes = iter_registered_model_classes()
    assert isinstance(classes, frozenset)
    assert DispatchAgent in classes


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
