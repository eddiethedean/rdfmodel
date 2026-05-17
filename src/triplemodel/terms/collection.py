"""RDF ``rdf:List`` encoding via rdflib :class:`~rdflib.collection.Collection`."""

from __future__ import annotations

from typing import TypeVar, cast

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF
from rdflib.term import Node

from triplemodel._typing import ModelFieldScalar, PythonToTermInput
from triplemodel.terms.bnode import remove_bnode_subgraph
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=ModelFieldScalar)


def _clear_list_or_bnode_object(graph: Graph, head: Node) -> None:
    """Drop an ``rdf:List`` structure or a nested blank-node subgraph."""
    if not isinstance(head, BNode):
        return
    if (head, RDF.first, None) in graph:
        Collection(graph, head).clear()
    else:
        remove_bnode_subgraph(graph, head)


def remove_rdf_list(graph: Graph, subject: Node, predicate: str) -> None:
    """Remove objects at ``(subject, predicate)``, including lists and embed bnodes."""
    pred_ref = URIRef(predicate)
    for head in list(graph.objects(subject, pred_ref)):
        _clear_list_or_bnode_object(graph, head)
        graph.remove((subject, pred_ref, head))


def write_rdf_list(
    graph: Graph,
    subject: str | Node,
    predicate: str,
    values: list[PythonToTermInput | None],
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Replace any existing list at ``(subject, predicate)`` with a new ``rdf:List``."""
    subj = subject if isinstance(subject, Node) else subject_node(subject)
    remove_rdf_list(graph, subj, predicate)
    terms = [python_to_term(v, registry=registry) for v in values if v is not None]
    if not terms:
        return
    coll = Collection(graph, BNode(), terms)
    graph.add((subj, URIRef(predicate), coll.uri))


def read_rdf_list(
    graph: Graph,
    head: Node,
    py_type: type | None,
    *,
    registry: LiteralRegistry = default_registry,
) -> list[ModelFieldScalar]:
    """Read an ``rdf:List`` starting at ``head`` into a Python list."""
    if (head, RDF.first, None) not in graph:
        raise ValueError(
            f"Node {head!r} is not an rdf:List head (missing rdf:first triple)."
        )
    coll = Collection(graph, head)
    return [
        cast(ModelFieldScalar, term_to_python(term, py_type, registry=registry))
        for term in coll
    ]
