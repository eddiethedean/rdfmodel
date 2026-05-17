"""Blank-node helpers."""

from __future__ import annotations

import hashlib

from rdflib import BNode, Graph


def stable_bnode(key: str) -> BNode:
    """Deterministic blank node id from ``key``."""
    digest = hashlib.sha256(key.encode()).hexdigest()[:32]
    return BNode(digest)


def remove_bnode_subgraph(graph: Graph, node: BNode) -> None:
    """Remove triples where ``node`` is subject or object."""
    for triple in list(graph.triples((node, None, None))):
        graph.remove(triple)
    for triple in list(graph.triples((None, None, node))):
        graph.remove(triple)


def nested_bnode_key(parent_uri: str, predicate: str, nested: object) -> str:
    """Cache key for stable blank-node identity."""
    return f"{parent_uri}|{predicate}|{nested!r}"
