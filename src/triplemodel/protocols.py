"""Public protocols and extension points for TripleModel."""

from __future__ import annotations

import warnings
from typing import Protocol, cast, runtime_checkable

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel.config import GraphMode, RDF_TYPE, RdfConfig, get_rdf_config
from triplemodel.terms.registry import LiteralRegistry as LiteralRegistryImpl

_rdf_resource_classes: set[type] = set()
_type_uri_index: dict[str, type[BaseModel]] = {}


def register_rdf_resource(model_cls: type) -> None:
    """Record a :class:`~triplemodel.TripleModel` subclass for nested-embed detection."""
    _rdf_resource_classes.add(model_cls)
    cfg = get_rdf_config(model_cls)
    if cfg.type_uri:
        existing = _type_uri_index.get(cfg.type_uri)
        if existing is not None and existing is not model_cls:
            warnings.warn(
                f"Rdf.type_uri {cfg.type_uri!r} already registered on "
                f"{existing.__name__}; replacing with {model_cls.__name__}. "
                "Only one model class per type_uri should be registered per process; "
                "dispatch and parse(..., dispatch=True) use the last registration.",
                stacklevel=2,
            )
        _type_uri_index[cfg.type_uri] = cast(type[BaseModel], model_cls)


def iter_registered_type_uris() -> frozenset[str]:
    """Return all ``type_uri`` values registered on model classes."""
    return frozenset(_type_uri_index)


def model_class_for_type_uri(type_uri: str) -> type[BaseModel] | None:
    """Return the registered model class for ``type_uri``, if any."""
    return _type_uri_index.get(type_uri)


def iter_registered_model_classes() -> frozenset[type[BaseModel]]:
    """Return all registered :class:`~triplemodel.TripleModel` subclasses."""
    return frozenset(_type_uri_index.values())


def iter_model_resource_classes() -> frozenset[type[BaseModel]]:
    """Return every :class:`~triplemodel.TripleModel` subclass that was registered."""
    return frozenset(
        cast(type[BaseModel], cls)
        for cls in _rdf_resource_classes
        if isinstance(cls, type)
    )


def _mro_depth(model_cls: type) -> int:
    return len(model_cls.__mro__)


def resolve_model_class(
    graph: Graph,
    subject: Node,
    *,
    use_subclass: bool | None = None,
) -> type[BaseModel]:
    """Pick the most specific registered class for ``subject``'s ``rdf:type`` values."""
    if use_subclass is not None:
        from triplemodel.io.rdfs import resolve_model_class_with_rdfs

        return resolve_model_class_with_rdfs(graph, subject, use_subclass=use_subclass)
    from triplemodel.io.rdfs import (
        _pick_most_specific,
        subject_type_closure,
    )

    from triplemodel.store.terms import term_str

    direct_types = {term_str(t) for t in graph.objects(subject, NamedNode(RDF_TYPE))}
    closure = subject_type_closure(graph, subject)
    candidates: list[type[BaseModel]] = []
    for type_uri in iter_registered_type_uris():
        cls = model_class_for_type_uri(type_uri)
        if cls is None:
            continue
        cfg = get_rdf_config(cls)
        if cfg.resolve_subclass:
            if type_uri in closure:
                candidates.append(cls)
        elif type_uri in direct_types:
            candidates.append(cls)
    if not candidates:
        raise ValueError(
            f"No registered TripleModel class for subject {subject!r} "
            f"(rdf:types: {sorted(direct_types)})."
        )
    return _pick_most_specific(graph, candidates)


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
