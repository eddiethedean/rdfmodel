"""Parse and serialize RDF documents via pyoxigraph-backed graphs."""

from __future__ import annotations

import io
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar, cast, overload
from urllib.parse import urlparse
from urllib.error import HTTPError

from pydantic import BaseModel
from triplemodel.store import RdfGraph as Graph
from urllib.request import Request, urlopen

from triplemodel.namespaces import bind_namespaces
from triplemodel.store.formats import raise_if_unsupported_format

TModel = TypeVar("TModel", bound=BaseModel)
T1 = TypeVar("T1", bound=BaseModel)
T2 = TypeVar("T2", bound=BaseModel)
T3 = TypeVar("T3", bound=BaseModel)

_SUFFIX_TO_FORMAT: dict[str, str] = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".trig": "trig",
    ".nt": "nt",
    ".nq": "nquads",
    ".nquads": "nquads",
    ".rdf": "xml",
    ".xml": "xml",
    ".n3": "n3",
    ".jsonld": "json-ld",
    ".json-ld": "json-ld",
    ".hext": "hext",
    ".hextuples": "hext",
    ".trix": "trix",
    ".lt": "longturtle",
    ".longturtle": "longturtle",
}

_MEDIA_TO_FORMAT: dict[str, str] = {
    "text/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/trig": "trig",
    "application/n-triples": "nt",
    "application/n-quads": "nquads",
    "application/rdf+xml": "xml",
    "text/n3": "n3",
    "application/ld+json": "json-ld",
    "application/hextuples": "hext",
    "application/trix+xml": "trix",
}


def _format_hint_for_suffix(hint: str) -> str:
    """Use URL path (without query/fragment) when inferring format from a URL."""
    text = hint.strip()
    parsed = urlparse(text)
    if parsed.scheme in ("http", "https", "file") and parsed.path:
        return parsed.path
    return text


def infer_format(
    hint: str | Path | None,
    explicit_format: str | None = None,
) -> str:
    """Resolve a parser/serializer format name for pyoxigraph."""
    if explicit_format:
        raise_if_unsupported_format(explicit_format)
        return explicit_format
    if hint is None:
        raise ValueError(
            "Cannot infer RDF format: pass format= or a path/URL with a known suffix."
        )
    text = str(hint).lower().strip()
    if text in _MEDIA_TO_FORMAT:
        fmt = _MEDIA_TO_FORMAT[text]
        raise_if_unsupported_format(fmt)
        return fmt
    suffix_path = _format_hint_for_suffix(text)
    suffix = Path(suffix_path).suffix.lower()
    if suffix in _SUFFIX_TO_FORMAT:
        fmt = _SUFFIX_TO_FORMAT[suffix]
        raise_if_unsupported_format(fmt)
        return fmt
    raise ValueError(f"Cannot infer RDF format from {hint!r}; pass format= explicitly.")


def _normalize_parse_source_data(
    source: str | Path | io.BytesIO | io.StringIO | bytes | None,
    data: str | bytes | None,
) -> tuple[str | Path | None, str | bytes | None]:
    """Route bytes and IO buffers through ``data=``; reject both source and data."""
    if data is not None and source is not None:
        raise ValueError("Pass source= or data=, not both.")
    if data is None and isinstance(source, bytes):
        return None, source
    if data is None and isinstance(source, io.BytesIO):
        return None, source.read()
    if data is None and isinstance(source, io.StringIO):
        return None, source.read().encode("utf-8")
    if source is not None and not isinstance(source, (str, Path)):
        raise TypeError(f"Unsupported parse source type: {type(source)!r}")
    return source, data


def _is_jsonld_format(fmt: str | None) -> bool:
    return fmt is not None and fmt.lower().replace("_", "-") in ("json-ld", "jsonld")


def is_quad_format(fmt: str) -> bool:
    """Return True when ``fmt`` is a quad-aware format (TriG, N-Quads)."""
    normalized = fmt.lower().replace("_", "-")
    return normalized in ("trig", "nquads", "n-quads")


def merge_jsonld_kwargs(
    fmt: str | None,
    jsonld_context: dict[str, Any] | str | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Merge JSON-LD context into kwargs (warned as unsupported at parse/serialize time)."""
    from triplemodel.store.io_warnings import warn_jsonld_context_config

    if not _is_jsonld_format(fmt) or jsonld_context is None:
        return kwargs
    warn_jsonld_context_config(stacklevel=4)
    merged = dict(kwargs)
    if "context" not in merged:
        merged["context"] = jsonld_context
    return merged


def parse_into_graph(
    source: str | Path | io.BytesIO | io.StringIO | bytes | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    base: str | None = None,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Graph:
    """Parse RDF into a new in-memory :class:`~triplemodel.store.RdfGraph`."""
    if data is None and source is None:
        raise ValueError("parse_into_graph requires source= or data=.")
    source, data = _normalize_parse_source_data(source, data)
    hint: str | Path | None = None
    if data is None and source is not None and isinstance(source, (str, Path)):
        hint = source
    fmt = infer_format(hint, format)
    parse_kwargs = merge_jsonld_kwargs(fmt, jsonld_context, dict(rdflib_kwargs))
    graph = Graph()
    if data is not None:
        graph.parse(data=data, format=fmt, publicID=base, **parse_kwargs)
    elif source is not None:
        graph.parse(source=source, format=fmt, publicID=base, **parse_kwargs)
    else:
        raise ValueError("parse_into_graph requires source= or data=.")
    if bind_prefixes:
        bind_namespaces(graph, dict(bind_prefixes))
    return graph


def fetch_url(url: str, *, timeout: float = 30.0) -> bytes:
    """Download ``url`` and return the response body."""
    from triplemodel import __version__

    request = Request(url, headers={"User-Agent": f"triplemodel/{__version__}"})
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", None)
        if status is not None and status >= 400:
            raise HTTPError(
                url,
                status,
                getattr(response, "reason", ""),
                response.headers,
                None,
            )
        return response.read()


def parse_url_into_graph(
    url: str,
    *,
    format: str | None = None,
    base: str | None = None,
    timeout: float = 30.0,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Graph:
    """Parse RDF from a URL."""
    fmt = infer_format(url, format)
    body = fetch_url(url, timeout=timeout)
    return parse_into_graph(
        data=body,
        format=fmt,
        base=base,
        bind_prefixes=bind_prefixes,
        jsonld_context=jsonld_context,
        **rdflib_kwargs,
    )


def load_graph(
    source: str | Path | io.BytesIO | io.StringIO | bytes | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    base: str | None = None,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Graph:
    """Parse RDF into an in-memory graph (alias for :func:`parse_into_graph`)."""
    return parse_into_graph(
        source=source,
        data=data,
        format=format,
        base=base,
        bind_prefixes=bind_prefixes,
        jsonld_context=jsonld_context,
        **rdflib_kwargs,
    )


def load_models_from_graph(
    graph: Graph,
    *model_classes: type[TModel],
    **kwargs: Any,
) -> dict[type[TModel], list[TModel]]:
    """Load multiple model classes from one graph without re-parsing."""
    from triplemodel.io.import_ import graph_to_models
    from triplemodel.model import TripleModel

    result: dict[type[TModel], list[TModel]] = {}
    for model_cls in model_classes:
        if not issubclass(model_cls, TripleModel):
            raise TypeError(f"{model_cls!r} is not a TripleModel subclass.")
        result[model_cls] = cast(
            list[TModel], graph_to_models(graph, model_cls, **kwargs)
        )
    return result


@overload
def load_models(
    path: str | Path,
    model_cls: type[TModel],
    **kwargs: Any,
) -> list[TModel]: ...


@overload
def load_models(
    path: str | Path,
    model_cls1: type[T1],
    model_cls2: type[T2],
    **kwargs: Any,
) -> dict[type[T1] | type[T2], list[T1] | list[T2]]: ...


@overload
def load_models(
    path: str | Path,
    model_cls1: type[T1],
    model_cls2: type[T2],
    model_cls3: type[T3],
    **kwargs: Any,
) -> dict[type[T1] | type[T2] | type[T3], list[T1] | list[T2] | list[T3]]: ...


def load_models(
    path: str | Path,
    *model_classes: type[TModel],
    **kwargs: Any,
) -> list[TModel] | dict[type[TModel], list[TModel]]:
    """Load one or more model classes from a file (single parse for multiple classes)."""
    from triplemodel.config import get_rdf_config
    from triplemodel.model import TripleModel

    if not model_classes:
        raise TypeError("load_models() requires at least one model class.")
    for model_cls in model_classes:
        if not issubclass(model_cls, TripleModel):
            raise TypeError(f"{model_cls!r} is not a TripleModel subclass.")
    if len(model_classes) == 1:
        return cast(
            list[TModel],
            cast(type[TripleModel], model_classes[0]).parse(source=path, **kwargs),
        )
    lead = model_classes[0]
    cfg = get_rdf_config(lead)
    fmt = infer_format(path, kwargs.get("format"))
    resolved_base = (
        kwargs.get("base") if kwargs.get("base") is not None else cfg.base_uri
    )
    use_dataset = is_quad_format(fmt) or any(
        get_rdf_config(mc).graph_iri for mc in model_classes
    )
    from triplemodel.io.import_ import split_load_kwargs

    parse_kwargs, import_kwargs = split_load_kwargs(kwargs)
    if use_dataset:
        from triplemodel.io.dataset import load_models_from_dataset, parse_into_dataset

        dataset = parse_into_dataset(
            source=path,
            format=fmt,
            base=resolved_base,
            bind_prefixes=cfg.prefixes_dict,
            jsonld_context=cfg.jsonld_context,
            **parse_kwargs,
        )
        return load_models_from_dataset(dataset, *model_classes, **import_kwargs)
    graph = parse_into_graph(
        source=path,
        format=fmt,
        base=resolved_base,
        bind_prefixes=cfg.prefixes_dict,
        jsonld_context=cfg.jsonld_context,
        **parse_kwargs,
    )
    return load_models_from_graph(graph, *model_classes, **import_kwargs)


def _streaming_store_identifier(
    path: str | Path,
    store: str,
    explicit: str | None,
) -> tuple[str, str | None]:
    """Return ``(store identifier, ephemeral directory to delete)``."""
    from triplemodel.io.stores import coerce_store_name

    store = coerce_store_name(store, stacklevel=3)
    if explicit:
        return explicit, None
    if store.strip().lower() == "disk":
        import tempfile

        tmp = tempfile.mkdtemp(prefix="triplemodel-")
        return tmp, tmp
    return str(path), None


def parse_into_store_graph(
    path: str | Path,
    *,
    store: str = "disk",
    identifier: str | None = None,
    format: str | None = None,
    base: str | None = None,
    bind_prefixes: Mapping[str, str] | None = None,
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> Graph:
    """Parse a document into a store-backed ``Graph`` (recommended for large N-Triples/N-Quads).

    Defaults to an on-disk :class:`pyoxigraph.Store` (``store='disk'``). Pass ``identifier``
    for a persistent directory, or omit it to use a temporary directory removed by
    :meth:`~triplemodel.store.graph.RdfGraph.close`.
    """
    from triplemodel.io.stores import coerce_store_name, open_graph, store_commit

    store = coerce_store_name(store, stacklevel=2)
    fmt = infer_format(path, format)
    ident, ephemeral = _streaming_store_identifier(path, store, identifier)
    graph = open_graph(store, ident, ephemeral_store_path=ephemeral)
    try:
        parse_kwargs = merge_jsonld_kwargs(fmt, jsonld_context, dict(rdflib_kwargs))
        graph.parse(source=str(path), format=fmt, publicID=base, **parse_kwargs)
        store_commit(graph)
        if bind_prefixes:
            bind_namespaces(graph, dict(bind_prefixes))
        return graph
    except Exception:
        graph.close()
        raise


def load_models_streaming(
    path: str | Path,
    *model_classes: type[TModel],
    store: str | None = None,
    chunk_size: int = 500,
    store_identifier: str | None = None,
    **kwargs: Any,
) -> list[TModel] | dict[type[TModel], list[TModel]]:
    """Load models from a large file using chunked hydration (optional on-disk store).

    For N-Triples / N-Quads, pass ``store='disk'`` (and optional ``store_identifier``) to
    avoid holding the full graph in memory. Omit ``store`` for an in-memory parse.
    Turtle/TriG still require a full parse.
    """
    from triplemodel.config import get_rdf_config
    from triplemodel.io.import_ import iter_graph_to_models, split_load_kwargs
    from triplemodel.model import TripleModel

    if not model_classes:
        raise TypeError("load_models_streaming() requires at least one model class.")
    for model_cls in model_classes:
        if not issubclass(model_cls, TripleModel):
            raise TypeError(f"{model_cls!r} is not a TripleModel subclass.")

    lead = model_classes[0]
    cfg = get_rdf_config(lead)
    fmt = infer_format(path, kwargs.get("format"))
    use_store = store is not None
    resolved_base = (
        kwargs.get("base") if kwargs.get("base") is not None else cfg.base_uri
    )
    parse_kwargs, import_kwargs = split_load_kwargs(kwargs)
    store_name = store or "disk"
    ephemeral_path: str | None = None
    graph: Graph | None = None
    try:
        if use_store:
            ident, ephemeral_path = _streaming_store_identifier(
                path, store_name, store_identifier
            )
            graph = parse_into_store_graph(
                path,
                store=store_name,
                identifier=ident,
                format=fmt,
                base=resolved_base,
                bind_prefixes=cfg.prefixes_dict,
                jsonld_context=cfg.jsonld_context,
                **parse_kwargs,
            )
        else:
            graph = parse_into_graph(
                source=path,
                format=fmt,
                base=resolved_base,
                bind_prefixes=cfg.prefixes_dict,
                jsonld_context=cfg.jsonld_context,
                **parse_kwargs,
            )

        def _load_class(model_cls: type[TModel]) -> list[TModel]:
            instances: list[TModel] = []
            for chunk in iter_graph_to_models(
                graph,
                model_cls,
                chunk_size=chunk_size,
                **import_kwargs,
            ):
                instances.extend(chunk)
            return instances

        if len(model_classes) == 1:
            return _load_class(model_classes[0])
        return {cls: _load_class(cls) for cls in model_classes}
    finally:
        if graph is not None:
            if ephemeral_path is not None and graph.ephemeral_store_path is None:
                graph._ephemeral_store_path = ephemeral_path  # noqa: SLF001
            graph.close()


def dump_model(
    model: BaseModel,
    path: str | Path,
    **kwargs: Any,
) -> str | bytes | None:
    """Write a model instance to an RDF file (alias for ``model.serialize``)."""
    from triplemodel.model import TripleModel

    if not isinstance(model, TripleModel):
        raise TypeError(f"{model!r} is not a TripleModel instance.")
    return model.serialize(destination=path, **kwargs)


def dump_graph(
    graph: Graph,
    destination: str | Path | io.IOBase | None = None,
    *,
    format: str = "turtle",
    jsonld_context: dict[str, Any] | str | None = None,
    **rdflib_kwargs: Any,
) -> str | bytes | None:
    """Serialize ``graph`` to a string, bytes, or file."""
    ser_kwargs = merge_jsonld_kwargs(format, jsonld_context, dict(rdflib_kwargs))
    return graph.serialize(
        destination=destination,
        format=format,
        **ser_kwargs,
    )
