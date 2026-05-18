"""Extension hooks for custom literals, resources, and predicate resolution.

Full rdflib parser/store registration passthrough is planned for 0.9
(``register_parser`` / ``register_store``). For 0.8, register literals and
use :class:`~triplemodel.fields.resolver.FieldPredicateResolver` via
:func:`register_predicate_resolver`, or pass ``resolver=`` on import/export
helpers without registering globally.
"""

from __future__ import annotations

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


__all__ = [
    "LiteralRegistry",
    "default_registry",
    "default_resolver",
    "register_literal_type",
    "register_predicate_resolver",
    "register_rdf_resource",
]
