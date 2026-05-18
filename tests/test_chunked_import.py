"""Tests for iter_graph_to_models and chunked graph_to_models."""

from __future__ import annotations

from rdflib import Graph, Literal, URIRef

from triplemodel import TripleModel, graph_to_models, iter_graph_to_models, rdf_field
from triplemodel.config import RDF_TYPE

EX = "http://example.org/"


class ChunkPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def _build_graph(count: int) -> Graph:
    g = Graph()
    for i in range(count):
        subj = URIRef(f"{EX}p{i}")
        g.add((subj, URIRef(RDF_TYPE), URIRef(f"{EX}Person")))
        g.add((subj, URIRef(f"{EX}name"), Literal(f"P{i}")))
    return g


def test_iter_graph_to_models_chunks():
    g = _build_graph(5)
    chunks = list(iter_graph_to_models(g, ChunkPerson, chunk_size=2))
    assert [len(c) for c in chunks] == [2, 2, 1]
    assert sum(len(c) for c in chunks) == 5


def test_graph_to_models_with_chunk_size():
    g = _build_graph(4)
    people = graph_to_models(g, ChunkPerson, chunk_size=2)
    assert len(people) == 4
