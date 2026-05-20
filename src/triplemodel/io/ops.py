"""Thin helpers over pyoxigraph-backed graph operations for TripleModel."""

from __future__ import annotations

from typing import TypeVar, cast

from pydantic import BaseModel
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel.config import get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.cardinality import field_cardinality, scalar_python_type
from triplemodel.terms.collection import read_rdf_list
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.registry import LiteralRegistry, default_registry
from triplemodel._typing import ModelFieldScalar, PythonToTermInput

T = TypeVar("T", bound=BaseModel)


def merge_graphs(*graphs: Graph) -> Graph:
    """Return a new graph containing the union of ``graphs``."""
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
    *,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> ModelFieldScalar | None:
    """Return a single object for a functional-property field, if present."""
    field_info = model_cls.model_fields[field_name]
    py_type = scalar_python_type(field_info)
    cfg = get_rdf_config(model_cls)
    r = resolver or default_resolver
    resolved_pred = r.resolve_field_predicate(field_info, cfg.prefixes_dict)
    if resolved_pred is None:
        raise ValueError(f"Field {field_name!r} has no RDF predicate mapping.")
    objects = list(graph.objects(NamedNode(subject), NamedNode(resolved_pred)))
    if not objects:
        return None
    return cast(
        ModelFieldScalar, term_to_python(objects[0], py_type, registry=registry)
    )


def graph_set(
    graph: Graph,
    subject: str,
    predicate: str,
    value: PythonToTermInput | None,
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Set objects for ``(subject, predicate)`` using remove-then-add semantics."""
    subj = NamedNode(subject)
    pred = NamedNode(predicate)
    for obj in list(graph.objects(subj, pred)):
        graph.remove((subj, pred, obj))
    if value is not None:
        graph.add((subj, pred, python_to_term(value, registry=registry)))


def graph_set_many(
    graph: Graph,
    subject: Node,
    predicate: str,
    values: list[PythonToTermInput],
    *,
    registry: LiteralRegistry = default_registry,
) -> None:
    """Set multiple objects for ``(subject, predicate)`` (remove-then-add)."""
    pred = NamedNode(predicate)
    for obj in list(graph.objects(subject, pred)):
        graph.remove((subject, pred, obj))
    for value in values:
        graph.add((subject, pred, python_to_term(value, registry=registry)))


def objects_for_field(
    graph: Graph,
    uri: str,
    model_cls: type[BaseModel],
    field_name: str,
    *,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> list[ModelFieldScalar]:
    """Return all RDF objects for a model field's predicate."""
    field_info = model_cls.model_fields[field_name]
    cfg = get_rdf_config(model_cls)
    r = resolver or default_resolver
    pred = r.resolve_field_predicate(field_info, cfg.prefixes_dict)
    if pred is None:
        raise ValueError(f"Field {field_name!r} has no RDF predicate mapping.")
    py_type = scalar_python_type(field_info)
    objects = list(graph.objects(NamedNode(uri), NamedNode(pred)))
    if field_cardinality(field_info) == "list":
        if not objects:
            return []
        return read_rdf_list(graph, objects[0], py_type, registry=registry)
    return [
        cast(ModelFieldScalar, term_to_python(o, py_type, registry=registry))
        for o in objects
    ]
