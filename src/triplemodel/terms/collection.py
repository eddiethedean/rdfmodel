"""RDF ``rdf:List`` encoding (manual ``rdf:first`` / ``rdf:rest``)."""

from __future__ import annotations

from typing import TypeVar, cast

from pyoxigraph import BlankNode, NamedNode

from triplemodel._typing import ModelFieldScalar, PythonToTermInput
from triplemodel.store.graph import RdfGraph
from triplemodel.store.namespaces import RDF_FIRST, RDF_NIL, RDF_REST
from triplemodel.store.terms import OxTerm, RdfTerm
from triplemodel.terms.bnode import remove_bnode_subgraph
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.iri import subject_node
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=ModelFieldScalar)

_FIRST = NamedNode(RDF_FIRST)
_REST = NamedNode(RDF_REST)
_NIL = NamedNode(RDF_NIL)


def _is_list_head(graph: RdfGraph, head: OxTerm) -> bool:
    return next(graph.objects(head, _FIRST), None) is not None


def _clear_list(graph: RdfGraph, head: BlankNode) -> None:
    current: RdfTerm | None = head
    while current is not None and isinstance(current, BlankNode):
        if not _is_list_head(graph, current):
            break
        first_objs = list(graph.objects(current, _FIRST))
        rest_objs = list(graph.objects(current, _REST))
        graph.remove((current, _FIRST, first_objs[0]))
        if rest_objs:
            graph.remove((current, _REST, rest_objs[0]))
        next_head: OxTerm | None = None
        if rest_objs and rest_objs[0] != _NIL:
            next_head = rest_objs[0]
        current = next_head if isinstance(next_head, BlankNode) else None


def _clear_list_or_bnode_object(graph: RdfGraph, head: OxTerm) -> None:
    if not isinstance(head, BlankNode):
        return
    if _is_list_head(graph, head):
        _clear_list(graph, head)
    else:
        remove_bnode_subgraph(graph, head)


def remove_rdf_list(graph: RdfGraph, subject: RdfTerm, predicate: str) -> None:
    """Remove objects at ``(subject, predicate)``, including lists and embed bnodes."""
    pred_ref = NamedNode(predicate)
    for head in list(graph.objects(subject, pred_ref)):
        _clear_list_or_bnode_object(graph, head)
        graph.remove((subject, pred_ref, head))


def write_rdf_list(
    graph: RdfGraph,
    subject: str | RdfTerm,
    predicate: str,
    values: list[PythonToTermInput | None],
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Replace any existing list at ``(subject, predicate)`` with a new ``rdf:List``."""
    subj = subject if not isinstance(subject, str) else subject_node(subject)
    remove_rdf_list(graph, subj, predicate)
    terms = [python_to_term(v, registry=registry) for v in values if v is not None]
    if not terms:
        return
    cells: list[BlankNode] = [BlankNode() for _ in terms]
    for cell, term in zip(cells, terms, strict=True):
        graph.add((cell, _FIRST, term))
    for cell, nxt in zip(cells, cells[1:] + [None], strict=True):
        rest: RdfTerm = _NIL if nxt is None else nxt
        graph.add((cell, _REST, rest))
    graph.add((subj, predicate, cells[0]))


def read_rdf_list(
    graph: RdfGraph,
    head: OxTerm,
    py_type: type | None,
    *,
    registry: LiteralRegistry = default_registry,
) -> list[ModelFieldScalar]:
    """Read an ``rdf:List`` starting at ``head`` into a Python list."""
    if not _is_list_head(graph, head):
        raise ValueError(
            f"Node {head!r} is not an rdf:List head (missing rdf:first triple)."
        )
    out: list[ModelFieldScalar] = []
    current: OxTerm | None = head
    while current is not None and isinstance(current, BlankNode):
        first_objs = list(graph.objects(current, _FIRST))
        if not first_objs:
            break
        out.append(
            cast(
                ModelFieldScalar,
                term_to_python(first_objs[0], py_type, registry=registry),
            )
        )
        rest_objs = list(graph.objects(current, _REST))
        if not rest_objs or rest_objs[0] == _NIL:
            break
        current = rest_objs[0]
    return out
