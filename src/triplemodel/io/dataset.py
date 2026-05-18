"""Dataset and named-graph serialization."""

from __future__ import annotations

import io
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel
from rdflib import Dataset, Graph, URIRef
from rdflib.term import Node

from triplemodel.config import (
    GraphMode,
    RdfConfig,
    get_graph_context,
    get_rdf_config,
    resolve_graph_iri,
)
from triplemodel.io.files import (
    fetch_url,
    infer_format,
    merge_jsonld_kwargs,
)
from triplemodel.io.graph import model_to_graph, models_to_graph
from triplemodel.io.import_ import OnDuplicate, graph_to_model, graph_to_models
from triplemodel.io.sync import sync_to_graph
from triplemodel.namespaces import bind_namespaces
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)
TModel = TypeVar("TModel", bound=BaseModel)


def parse_into_dataset(
    source: str | Path | io.BytesIO | io.StringIO | bytes | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    base: str | None = None,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Dataset:
    """Parse RDF into a new in-memory :class:`rdflib.Dataset`."""
    if data is None and source is None:
        raise ValueError("parse_into_dataset requires source= or data=.")
    hint: str | Path | None = None
    if data is None and source is not None and isinstance(source, (str, Path)):
        hint = source
    fmt = infer_format(hint, format)
    parse_kwargs = merge_jsonld_kwargs(fmt, jsonld_context, dict(rdflib_kwargs))
    dataset = Dataset()
    if data is not None:
        dataset.parse(data=data, format=fmt, publicID=base, **parse_kwargs)
    else:
        dataset.parse(source=str(source), format=fmt, publicID=base, **parse_kwargs)
    if bind_prefixes:
        bind_namespaces(dataset, dict(bind_prefixes))
    return dataset


def parse_url_into_dataset(
    url: str,
    *,
    format: str | None = None,
    base: str | None = None,
    timeout: float = 30.0,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Dataset:
    """Parse RDF from a URL into a :class:`rdflib.Dataset`."""
    fmt = infer_format(url, format)
    body = fetch_url(url, timeout=timeout)
    return parse_into_dataset(
        data=body,
        format=fmt,
        base=base,
        bind_prefixes=bind_prefixes,
        jsonld_context=jsonld_context,
        **rdflib_kwargs,
    )


def load_dataset(
    source: str | Path | io.BytesIO | io.StringIO | bytes | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    base: str | None = None,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Dataset:
    """Parse RDF into an in-memory :class:`rdflib.Dataset` (alias for :func:`parse_into_dataset`)."""
    return parse_into_dataset(
        source=source,
        data=data,
        format=format,
        base=base,
        bind_prefixes=bind_prefixes,
        jsonld_context=jsonld_context,
        **rdflib_kwargs,
    )


def dump_dataset(
    dataset: Dataset,
    destination: str | Path | io.IOBase | None = None,
    *,
    format: str = "trig",
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> str | bytes | None:
    """Serialize ``dataset`` to a string, bytes, or file."""
    ser_kwargs = merge_jsonld_kwargs(format, jsonld_context, dict(rdflib_kwargs))
    return dataset.serialize(  # ty: ignore[no-matching-overload]
        destination=destination,
        format=format,
        **ser_kwargs,
    )


def _context_for_model(
    dataset: Dataset,
    model: BaseModel,
    *,
    config: RdfConfig | None = None,
    graph_iri: str | None = None,
) -> Graph:
    cfg = config or get_rdf_config(type(model))
    resolved_iri = graph_iri if graph_iri is not None else resolve_graph_iri(model, cfg)
    return get_graph_context(dataset, resolved_iri)


def model_to_dataset(
    model: BaseModel,
    dataset: Dataset | None = None,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
    graph_iri: str | None = None,
    mode: GraphMode | None = None,
    bind: bool | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    skolemize: bool | None = None,
) -> Dataset:
    """Add triples for ``model`` to the appropriate named graph in ``dataset``."""
    ds = Dataset() if dataset is None else dataset
    context = _context_for_model(ds, model, config=config, graph_iri=graph_iri)
    should_bind = bind if bind is not None else dataset is None
    model_to_graph(
        model,
        context,
        uri=uri,
        config=config,
        mode=mode,
        bind=should_bind,
        resolver=resolver,
        registry=registry,
        skolemize=skolemize,
    )
    return ds


def models_to_dataset(
    models: Sequence[BaseModel],
    dataset: Dataset | None = None,
    *,
    mode: GraphMode = "add",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> Dataset:
    """Serialize multiple model instances into named graphs by ``resolve_graph_iri``."""
    ds = Dataset() if dataset is None else dataset
    by_graph: dict[str | None, list[BaseModel]] = defaultdict(list)
    for model in models:
        by_graph[resolve_graph_iri(model)].append(model)
    for graph_iri, group in by_graph.items():
        context = get_graph_context(ds, graph_iri)
        models_to_graph(
            group,
            context,
            mode=mode,
            resolver=resolver,
            registry=registry,
        )
    return ds


def sync_to_dataset(
    model: BaseModel,
    dataset: Dataset,
    *,
    uri: str | None = None,
    graph_iri: str | None = None,
    mode: GraphMode | None = None,
    config: RdfConfig | None = None,
    bind: bool = True,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    skolemize: bool | None = None,
) -> Dataset:
    """Sync ``model`` into the resolved named graph within ``dataset``."""
    context = _context_for_model(dataset, model, config=config, graph_iri=graph_iri)
    sync_to_graph(
        model,
        context,
        uri=uri,
        mode=mode,
        config=config,
        bind=bind,
        resolver=resolver,
        registry=registry,
        skolemize=skolemize,
    )
    return dataset


def graph_to_model_from_dataset(
    dataset: Dataset,
    model_cls: type[T],
    uri: str | Node,
    *,
    graph_iri: str | None = None,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> T:
    """Construct an instance from triples in the model's named graph context."""
    cfg = config or get_rdf_config(model_cls)
    resolved_iri = graph_iri if graph_iri is not None else cfg.graph_iri
    context = get_graph_context(dataset, resolved_iri)
    return graph_to_model(
        context,
        model_cls,
        uri,
        config=cfg,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


def graph_to_models_from_dataset(
    dataset: Dataset,
    model_cls: type[T],
    *,
    graph_iri: str | None = None,
    type_uri: str | None = None,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[T]:
    """Load all resources of this type from the model's named graph context."""
    cfg = config or get_rdf_config(model_cls)
    resolved_iri = graph_iri if graph_iri is not None else cfg.graph_iri
    context = get_graph_context(dataset, resolved_iri)
    return graph_to_models(
        context,
        model_cls,
        type_uri=type_uri,
        config=cfg,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


def all_from_dataset(
    dataset: Dataset,
    model_cls: type[T],
    **kwargs: Any,
) -> list[T]:
    """Load every resource of this model's RDF type from its named graph context."""
    return graph_to_models_from_dataset(dataset, model_cls, **kwargs)


def load_models_from_dataset(
    dataset: Dataset,
    *model_classes: type[TModel],
    **kwargs: Any,
) -> dict[type[TModel], list[TModel]]:
    """Load multiple model classes from one dataset (each uses its ``Rdf.graph_iri``)."""
    from triplemodel.model import TripleModel

    result: dict[type[TModel], list[TModel]] = {}
    for model_cls in model_classes:
        if not issubclass(model_cls, TripleModel):
            raise TypeError(f"{model_cls!r} is not a TripleModel subclass.")
        result[model_cls] = cast(
            list[TModel],
            graph_to_models_from_dataset(dataset, model_cls, **kwargs),
        )
    return result


def quads_in_context(
    dataset: Dataset,
    graph_iri: str | None,
) -> Iterator[tuple[Node, Node, Node, Node]]:
    """Iterate quads in a named graph (or default graph when ``graph_iri`` is None)."""
    if graph_iri is None:
        return cast(
            Iterator[tuple[Node, Node, Node, Node]],
            dataset.quads((None, None, None, None)),
        )
    context = dataset.graph(URIRef(graph_iri))
    return cast(
        Iterator[tuple[Node, Node, Node, Node]],
        dataset.quads((None, None, None, context)),
    )


def iter_model_quads(
    model: BaseModel,
    *,
    uri: str | None = None,
    graph_iri: str | None = None,
    config: RdfConfig | None = None,
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> Iterator[tuple[str | Node, str, Any, str | None]]:
    """Yield ``(subject, predicate, object, graph_iri)`` rows for ``model``."""
    from triplemodel.io.export import model_to_triples

    cfg = config or get_rdf_config(type(model))
    resolved_iri = graph_iri if graph_iri is not None else resolve_graph_iri(model, cfg)
    for subj, pred, obj in model_to_triples(
        model, uri=uri, config=cfg, resolver=resolver, registry=registry
    ):
        yield subj, pred, obj, resolved_iri
