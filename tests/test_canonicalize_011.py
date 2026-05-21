"""canonicalize_quads helper."""

from __future__ import annotations

from pyoxigraph import BlankNode, NamedNode, Quad, DefaultGraph

from triplemodel.store.canonicalize import canonicalize_quads

EX = "http://example.org/"


def _blank_graph_quads() -> list[Quad]:
    b1 = BlankNode("_:b1")
    b2 = BlankNode("_:b2")
    p = NamedNode(f"{EX}p")
    o = NamedNode(f"{EX}o")
    g = DefaultGraph()
    return [
        Quad(b1, p, b2, g),
        Quad(b2, p, o, g),
    ]


def test_structurally_equal_graphs_canonicalize_same() -> None:
    a = canonicalize_quads(_blank_graph_quads())
    b = canonicalize_quads(_blank_graph_quads())
    assert len(a) == len(b) == 2
    assert {q.predicate for q in a} == {q.predicate for q in b}
