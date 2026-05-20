"""Blank-node skolemization for :class:`~triplemodel.store.graph.RdfGraph`."""

from __future__ import annotations

import hashlib

from pyoxigraph import BlankNode, NamedNode, Quad

from triplemodel.store.graph import RdfGraph
from triplemodel.store.terms import QuadObject, QuadSubject, term_str

_SKOLEM_BASE = "http://triplemodel.invalid/.well-known/skolem/"


def skolemize_graph(graph: RdfGraph) -> RdfGraph:
    """Replace blank nodes with stable skolem IRIs (new graph)."""
    mapping: dict[str, NamedNode] = {}
    out = RdfGraph()
    for quad in graph.store:
        g = quad.graph_name
        s = _map_subject(quad.subject, mapping)
        p = quad.predicate
        o = _map_object(quad.object, mapping)
        out.store.add(Quad(s, p, o, g))
    out._prefixes = dict(graph._prefixes)
    return out


def de_skolemize_graph(graph: RdfGraph) -> RdfGraph:
    """Replace skolem IRIs under ``_SKOLEM_BASE`` with fresh blank nodes."""
    mapping: dict[str, BlankNode] = {}
    out = RdfGraph()
    for quad in graph.store:
        g = quad.graph_name
        s = _unmap_subject(quad.subject, mapping)
        p = quad.predicate
        o = _unmap_object(quad.object, mapping)
        out.store.add(Quad(s, p, o, g))
    out._prefixes = dict(graph._prefixes)
    return out


def _map_subject(term: QuadSubject, mapping: dict[str, NamedNode]) -> QuadSubject:
    if isinstance(term, BlankNode):
        key = str(term)
        if key not in mapping:
            digest = hashlib.sha256(key.encode()).hexdigest()[:32]
            mapping[key] = NamedNode(f"{_SKOLEM_BASE}{digest}")
        return mapping[key]
    return term


def _map_object(term: QuadObject, mapping: dict[str, NamedNode]) -> QuadObject:
    if isinstance(term, BlankNode):
        key = str(term)
        if key not in mapping:
            digest = hashlib.sha256(key.encode()).hexdigest()[:32]
            mapping[key] = NamedNode(f"{_SKOLEM_BASE}{digest}")
        return mapping[key]
    return term


def _unmap_subject(term: QuadSubject, mapping: dict[str, BlankNode]) -> QuadSubject:
    if isinstance(term, NamedNode) and term_str(term).startswith(_SKOLEM_BASE):
        key = term_str(term)
        if key not in mapping:
            mapping[key] = BlankNode()
        return mapping[key]
    return term


def _unmap_object(term: QuadObject, mapping: dict[str, BlankNode]) -> QuadObject:
    if isinstance(term, NamedNode) and term_str(term).startswith(_SKOLEM_BASE):
        key = term_str(term)
        if key not in mapping:
            mapping[key] = BlankNode()
        return mapping[key]
    return term
