"""Thin helpers over rdflib graph operations for TripleModel."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel
from rdflib import Graph, URIRef

from triplemodel._cardinality import scalar_python_type
from triplemodel._fields import predicate_for_field, predicate_from_annotation
from triplemodel._types import python_to_term, term_to_python

T = TypeVar("T", bound=BaseModel)


def merge_graphs(*graphs: Graph) -> Graph:
    """Return a new graph containing the union of ``graphs``.

    Blank node identity is preserved only when graphs share term objects;
    re-parsed files may produce distinct BNodes with the same label.
    """
    merged = Graph()
    for g in graphs:
        for t in g:
            merged.add(t)
    return merged


def graph_value(
    graph: Graph,
    subject: str,
    predicate: str,
    model_cls: type[T],
    field_name: str,
) -> Any:
    """Return a single object for a functional-property field, if present."""
    field_info = model_cls.model_fields[field_name]
    py_type = scalar_python_type(field_info)
    objects = list(graph.objects(URIRef(subject), URIRef(predicate)))
    if not objects:
        return None
    return term_to_python(objects[0], py_type)


def graph_set(
    graph: Graph,
    subject: str,
    predicate: str,
    value: object | None,
) -> None:
    """Set objects for ``(subject, predicate)`` using remove-then-add semantics."""
    subj = URIRef(subject)
    pred = URIRef(predicate)
    for obj in list(graph.objects(subj, pred)):
        graph.remove((subj, pred, obj))
    if value is not None:
        graph.add((subj, pred, python_to_term(value)))


def objects_for_field(
    graph: Graph,
    uri: str,
    model_cls: type[BaseModel],
    field_name: str,
) -> list[Any]:
    """Return all RDF objects for a model field's predicate."""
    field_info = model_cls.model_fields[field_name]
    pred = predicate_for_field(field_info) or predicate_from_annotation(
        field_info.annotation
    )
    if pred is None:
        raise ValueError(f"Field {field_name!r} has no RDF predicate mapping.")
    py_type = scalar_python_type(field_info)
    return [
        term_to_python(o, py_type) for o in graph.objects(URIRef(uri), URIRef(pred))
    ]
