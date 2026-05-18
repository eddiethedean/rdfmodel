"""Cached predicate maps per TripleModel class (default resolver only)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from triplemodel.config import get_rdf_config
from triplemodel.fields.resolver import default_resolver
from triplemodel.protocols import PredicateResolver


def uses_default_resolver(resolver: PredicateResolver | None) -> bool:
    """True when ``resolver`` is unset or the package default."""
    return resolver is None or resolver is default_resolver


@lru_cache(maxsize=None)
def _predicate_items_default(
    model_cls: type[BaseModel],
) -> tuple[tuple[str, str | None], ...]:
    cfg = get_rdf_config(model_cls)
    prefixes = cfg.prefixes_dict
    items: list[tuple[str, str | None]] = []
    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        pred = default_resolver.resolve_field_predicate(field_info, prefixes)
        items.append((name, pred))
    return tuple(items)


@lru_cache(maxsize=None)
def _owned_predicates_default(model_cls: type[BaseModel]) -> frozenset[str]:
    cfg = get_rdf_config(model_cls)
    return default_resolver.owned_predicates(model_cls, cfg)


def predicate_map_for_class(
    model_cls: type[BaseModel],
    *,
    resolver: PredicateResolver | None = None,
) -> dict[str, str | None]:
    """Field name → resolved predicate IRI (cached for ``default_resolver``)."""
    if uses_default_resolver(resolver):
        return dict(_predicate_items_default(model_cls))
    cfg = get_rdf_config(model_cls)
    prefixes = cfg.prefixes_dict
    r = resolver or default_resolver
    result: dict[str, str | None] = {}
    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        result[name] = r.resolve_field_predicate(field_info, prefixes)
    return result


def owned_predicates_for_class(
    model_cls: type[BaseModel],
    *,
    resolver: PredicateResolver | None = None,
    config=None,
) -> frozenset[str]:
    """Owned predicate IRIs for ``model_cls`` (cached for ``default_resolver``)."""
    if uses_default_resolver(resolver):
        return _owned_predicates_default(model_cls)
    cfg = config or get_rdf_config(model_cls)
    r = resolver or default_resolver
    return r.owned_predicates(model_cls, cfg)


def field_info_by_predicate(
    model_cls: type[BaseModel],
    *,
    resolver: PredicateResolver | None = None,
) -> dict[str, FieldInfo]:
    """Resolved predicate IRI → ``FieldInfo`` (first field wins on duplicate preds)."""
    by_pred: dict[str, FieldInfo] = {}
    for name, pred in predicate_map_for_class(model_cls, resolver=resolver).items():
        if pred is None:
            continue
        field_info = model_cls.model_fields[name]
        by_pred.setdefault(pred, field_info)
    return by_pred


def clear_predicate_map_cache() -> None:
    """Clear cached predicate maps (for tests)."""
    _predicate_items_default.cache_clear()
    _owned_predicates_default.cache_clear()


__all__ = [
    "clear_predicate_map_cache",
    "field_info_by_predicate",
    "owned_predicates_for_class",
    "predicate_map_for_class",
    "uses_default_resolver",
]
