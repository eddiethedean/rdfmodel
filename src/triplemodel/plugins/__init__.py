"""Extension hooks for custom literals, resources, and predicate resolution."""

from __future__ import annotations

import warnings
from typing import Callable, TypeVar, cast

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


def _removed_plugin_api(name: str, *_args: object, **_kwargs: object) -> None:
    warnings.warn(
        f"triplemodel.plugins.{name} was removed in 0.10.0 (pyoxigraph has no plugin registry).",
        DeprecationWarning,
        stacklevel=2,
    )
    raise NotImplementedError(
        f"{name} is not available with the pyoxigraph engine (removed in TripleModel 0.10.0)."
    )


def register_parser(name: str, module_path: str, class_name: str) -> None:
    """Removed in 0.10.0 — pyoxigraph has no parser plugin registry."""
    _removed_plugin_api("register_parser", name, module_path, class_name)


def register_serializer(name: str, module_path: str, class_name: str) -> None:
    """Removed in 0.10.0 — pyoxigraph has no serializer plugin registry."""
    _removed_plugin_api("register_serializer", name, module_path, class_name)


def register_store(name: str, module_path: str, class_name: str) -> None:
    """Removed in 0.10.0 — use :class:`pyoxigraph.Store` directly."""
    _removed_plugin_api("register_store", name, module_path, class_name)


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
