"""Public protocols and extension points for TripleModel."""

from __future__ import annotations

from typing import Protocol, cast, runtime_checkable

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from rdflib import Graph, Literal, URIRef
from rdflib.term import Node

from triplemodel.config import GraphMode, RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel.terms.registry import LiteralRegistry as LiteralRegistryImpl

_rdf_resource_classes: set[type] = set()
_type_uri_index: dict[str, type[BaseModel]] = {}


def register_rdf_resource(model_cls: type) -> None:
    """Record a :class:`~triplemodel.TripleModel` subclass for nested-embed detection."""
    _rdf_resource_classes.add(model_cls)
    cfg = get_rdf_config(model_cls)
    if cfg.type_uri:
        _type_uri_index[cfg.type_uri] = cast(type[BaseModel], model_cls)


def iter_registered_type_uris() -> frozenset[str]:
    """Return all ``type_uri`` values registered on model classes."""
    return frozenset(_type_uri_index)


def _mro_depth(model_cls: type) -> int:
    return len(model_cls.__mro__)


def resolve_model_class(graph: Graph, subject: Node) -> type[BaseModel]:
    """Pick the most specific registered class for ``subject``'s ``rdf:type`` values."""
    type_nodes = list(graph.objects(subject, URIRef(RDF_TYPE)))
    candidates: list[type[BaseModel]] = []
    for t in type_nodes:
        cls = _type_uri_index.get(str(t))
        if cls is not None:
            candidates.append(cls)
    if not candidates:
        raise ValueError(
            f"No registered TripleModel class for subject {subject!r} "
            f"(rdf:types: {[str(t) for t in type_nodes]})."
        )
    return cast(type[BaseModel], max(candidates, key=_mro_depth))


def is_rdf_resource_class(tp: type) -> bool:
    """True when ``tp`` is a registered RDF-backed model class."""
    if not _rdf_resource_classes:
        return False
    try:
        return any(issubclass(tp, cls) for cls in _rdf_resource_classes)
    except TypeError:
        return False


@runtime_checkable
class RdfResource(Protocol):
    """Marker protocol for Pydantic models that map to RDF resources."""


@runtime_checkable
class PredicateResolver(Protocol):
    """Resolve field predicates and owned predicate sets for a model class."""

    def resolve_field_predicate(
        self, field_info: FieldInfo, prefixes: dict[str, str]
    ) -> str | None: ...

    def owned_predicates(
        self,
        model_cls: type[BaseModel],
        config: RdfConfig | None = None,
    ) -> frozenset[str]: ...


@runtime_checkable
class LiteralRegistry(Protocol):
    """Pluggable Python ↔ XSD literal conversion."""

    def register_literal_type(
        self,
        py_type: type,
        to_literal: object,
        from_literal: object,
        *,
        datatype: str | None = None,
    ) -> None: ...

    def python_to_literal(
        self,
        value: object,
        py_type: type | None = None,
    ) -> Literal | None: ...

    def literal_to_python(
        self, term: Literal, py_type: type | None
    ) -> object | None: ...


@runtime_checkable
class EmbedStrategy(Protocol):
    """Export/import nested models (IRI or blank-node embedding)."""

    def export(
        self,
        parent_subject: str,
        predicate: str,
        nested: BaseModel,
        *,
        config: RdfConfig | None = None,
    ) -> list[tuple[str | object, str, object]]: ...

    def import_value(
        self,
        graph: Graph,
        term: object,
        nested_cls: type[BaseModel],
    ) -> BaseModel: ...


@runtime_checkable
class GraphWriteMode(Protocol):
    """Write a model instance into a graph (add / replace / patch)."""

    @property
    def mode(self) -> GraphMode: ...

    def apply(
        self,
        graph: Graph,
        model: BaseModel,
        *,
        uri: str | None = None,
        config: RdfConfig,
        bind: bool,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistryImpl | None = None,
        skolemize: bool | None = None,
    ) -> Graph: ...
