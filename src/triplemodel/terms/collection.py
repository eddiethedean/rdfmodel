"""RDF ``rdf:List`` encoding via rdflib :class:`~rdflib.collection.Collection`."""

from __future__ import annotations

from typing import TypeVar, cast

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.term import Node

from triplemodel._typing import ModelFieldScalar, PythonToTermInput
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=ModelFieldScalar)


def remove_rdf_list(graph: Graph, subject: Node, predicate: str) -> None:
    """Remove ``rdf:List`` structures for ``(subject, predicate)``."""
    pred_ref = URIRef(predicate)
    for head in list(graph.objects(subject, pred_ref)):
        if isinstance(head, BNode):
            Collection(graph, head).clear()
        graph.remove((subject, pred_ref, head))


def write_rdf_list(
    graph: Graph,
    subject: str | Node,
    predicate: str,
    values: list[PythonToTermInput],
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
    coll = Collection(graph, head)
    return [
        cast(ModelFieldScalar, term_to_python(term, py_type, registry=registry))
        for term in coll
    ]
