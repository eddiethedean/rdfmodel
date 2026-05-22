"""Batch hydration of reference fields from a shared graph."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from pydantic import BaseModel
from triplemodel.store import RdfGraph as Graph

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
    from triplemodel.config import get_rdf_config
    from triplemodel.io.skolem import apply_de_skolemize

    cfg = get_rdf_config(model_cls)
    do_de = cfg.skolemize_import if de_skolemize is None else de_skolemize
    graph = apply_de_skolemize(graph, de_skolemize=do_de)
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
            if isinstance(raw, (list, set)):
                hydrated_items: list[BaseModel] = []
                for item in raw:
                    uri = _ref_uri(item)
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
                            de_skolemize=False,
                        )
                    hydrated_items.append(cache[key])
                if not hydrated_items:
                    continue
                updates[field_name] = (
                    set(hydrated_items) if isinstance(raw, set) else hydrated_items
                )
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
                    de_skolemize=False,
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
