"""Batch hydration of reference fields from a shared graph."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from pydantic import BaseModel
from rdflib import Graph

from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.metadata.cardinality import nested_model_type
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)


def _ref_uri(value: object) -> str | None:
    if isinstance(value, ResourceRef):
        return value.iri
    subject_uri_fn = getattr(value, "subject_uri", None)
    if callable(subject_uri_fn):
        try:
            return str(subject_uri_fn())
        except (ValueError, TypeError):
            pass
    if isinstance(value, str) and value.startswith(("http://", "https://", "urn:")):
        return value
    return None


def _nested_cls_for_field(
    model_cls: type[BaseModel],
    field_name: str,
    spec: Mapping[str, type[BaseModel]] | None,
) -> type[BaseModel] | None:
    if spec is not None and field_name in spec:
        return spec[field_name]
    field_info = model_cls.model_fields[field_name]
    return cast(type[BaseModel] | None, nested_model_type(field_info))


def hydrate_refs(
    instances: list[T],
    graph: Graph,
    *field_names: str,
    spec: Mapping[str, type[BaseModel]] | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[T]:
    """Batch-load reference fields from ``graph``, reusing one model per object URI."""
    if not instances:
        return []
    model_cls = type(instances[0])
    if not field_names:
        return list(instances)
    cache: dict[tuple[type[BaseModel], str], BaseModel] = {}
    out: list[T] = []
    for inst in instances:
        updates: dict[str, object] = {}
        for field_name in field_names:
            nested_cls = _nested_cls_for_field(model_cls, field_name, spec)
            if nested_cls is None:
                raise ValueError(
                    f"Field {field_name!r} on {model_cls.__name__} is not a nested "
                    "TripleModel reference; pass spec= for ResourceRef fields."
                )
            raw = getattr(inst, field_name, None)
            if raw is None:
                continue
            uri = _ref_uri(raw)
            if uri is None:
                continue
            key = (nested_cls, uri)
            if key not in cache:
                cache[key] = graph_to_model(
                    graph,
                    nested_cls,
                    uri,
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                    resolver=resolver,
                    registry=registry,
                    de_skolemize=de_skolemize,
                )
            updates[field_name] = cache[key]
        if updates:
            out.append(inst.model_copy(update=updates))
        else:
            out.append(inst)
    return out


def model_join(
    instances: list[T],
    graph: Graph,
    spec: Mapping[str, type[BaseModel]],
    **kwargs: Any,
) -> list[T]:
    """Hydrate reference fields named in ``spec`` (field name → model class)."""
    return hydrate_refs(
        instances,
        graph,
        *spec.keys(),
        spec=spec,
        **kwargs,
    )


__all__ = ["hydrate_refs", "model_join"]
