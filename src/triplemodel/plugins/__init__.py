"""Extension hooks for custom literals, resources, predicate resolution, and rdflib plugins."""

from __future__ import annotations

from typing import Callable, TypeVar, cast

from rdflib.parser import Parser
from rdflib.plugin import register as _rdflib_register
from rdflib.serializer import Serializer
from rdflib.store import Store

from triplemodel.fields.resolver import FieldPredicateResolver, default_resolver
from triplemodel.protocols import PredicateResolver, register_rdf_resource
from triplemodel.terms.registry import (
    LiteralRegistry,
    default_registry,
    register_literal_type,
)

T = TypeVar("T", bound=PredicateResolver)


def register_predicate_resolver(
    resolver: T | Callable[[], T],
) -> T:
    """Install a package-wide predicate resolver (replaces :data:`default_resolver`)."""
    if isinstance(resolver, type):
        instance = resolver()
    elif callable(resolver):
        instance = cast(Callable[[], T], resolver)()
    else:
        instance = resolver
    if not isinstance(instance, FieldPredicateResolver):
        raise TypeError(
            "register_predicate_resolver expects a FieldPredicateResolver instance or factory."
        )
    import triplemodel.fields.resolver as resolver_mod

    resolver_mod.default_resolver = instance
    from triplemodel.metadata.predicate_map import clear_predicate_map_cache

    clear_predicate_map_cache()
    return instance


def register_parser(name: str, module_path: str, class_name: str) -> None:
    """Register a custom rdflib :class:`~rdflib.parser.Parser` (passthrough to ``rdflib.plugin.register``)."""
    _rdflib_register(name, Parser, module_path, class_name)


def register_serializer(name: str, module_path: str, class_name: str) -> None:
    """Register a custom rdflib :class:`~rdflib.serializer.Serializer`."""
    _rdflib_register(name, Serializer, module_path, class_name)


def register_store(name: str, module_path: str, class_name: str) -> None:
    """Register a custom rdflib :class:`~rdflib.store.Store`."""
    _rdflib_register(name, Store, module_path, class_name)


__all__ = [
    "LiteralRegistry",
    "default_registry",
    "default_resolver",
    "register_literal_type",
    "register_parser",
    "register_predicate_resolver",
    "register_rdf_resource",
    "register_serializer",
    "register_store",
]
