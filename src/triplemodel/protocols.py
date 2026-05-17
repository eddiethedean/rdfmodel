"""Public protocols and extension points for TripleModel."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from rdflib import Graph, Literal

from triplemodel.config import GraphMode, RdfConfig
from triplemodel.terms.registry import LiteralRegistry as LiteralRegistryImpl

_rdf_resource_classes: set[type] = set()


def register_rdf_resource(model_cls: type) -> None:
    """Record a :class:`~triplemodel.TripleModel` subclass for nested-embed detection."""
    _rdf_resource_classes.add(model_cls)


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
    ) -> Graph: ...
