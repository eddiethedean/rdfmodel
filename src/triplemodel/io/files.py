"""Parse and serialize RDF documents via rdflib."""

from __future__ import annotations

import io
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar, cast, overload

from pydantic import BaseModel
from rdflib import Graph
from urllib.request import Request, urlopen

from triplemodel.namespaces import bind_namespaces

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


def infer_format(
    hint: str | Path | None,
    explicit_format: str | None = None,
) -> str:
    """Resolve an rdflib serializer/parser format name."""
    if explicit_format:
        return explicit_format
    if hint is None:
        raise ValueError(
            "Cannot infer RDF format: pass format= or a path/URL with a known suffix."
        )
    text = str(hint).lower().strip()
    if text in _MEDIA_TO_FORMAT:
        return _MEDIA_TO_FORMAT[text]
    suffix = Path(text).suffix.lower()
    if suffix in _SUFFIX_TO_FORMAT:
        return _SUFFIX_TO_FORMAT[suffix]
    raise ValueError(f"Cannot infer RDF format from {hint!r}; pass format= explicitly.")


def _is_jsonld_format(fmt: str | None) -> bool:
    return fmt is not None and fmt.lower().replace("_", "-") in ("json-ld", "jsonld")


def is_quad_format(fmt: str) -> bool:
    """Return True when ``fmt`` is a quad-aware rdflib format (TriG, N-Quads)."""
    normalized = fmt.lower().replace("_", "-")
    return normalized in ("trig", "nquads", "n-quads")


def merge_jsonld_kwargs(
    fmt: str | None,
    jsonld_context: dict[str, Any] | str | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Apply default JSON-LD context when serializing or parsing."""
    if not _is_jsonld_format(fmt) or jsonld_context is None:
        return kwargs
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
    """Parse RDF into a new in-memory ``Graph``."""
    if data is None and source is None:
        raise ValueError("parse_into_graph requires source= or data=.")
    hint: str | Path | None = None
    if data is None and source is not None and isinstance(source, (str, Path)):
        hint = source
    fmt = infer_format(hint, format)
    parse_kwargs = merge_jsonld_kwargs(fmt, jsonld_context, dict(rdflib_kwargs))
    graph = Graph()
    if data is not None:
        graph.parse(data=data, format=fmt, publicID=base, **parse_kwargs)
    else:
        graph.parse(source=str(source), format=fmt, publicID=base, **parse_kwargs)
    if bind_prefixes:
        bind_namespaces(graph, dict(bind_prefixes))
    return graph


def fetch_url(url: str, *, timeout: float = 30.0) -> bytes:
    """Download ``url`` and return the response body."""
    from triplemodel import __version__

    request = Request(url, headers={"User-Agent": f"triplemodel/{__version__}"})
    with urlopen(request, timeout=timeout) as response:
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
    """Parse RDF into an in-memory :class:`rdflib.Graph` (alias for :func:`parse_into_graph`)."""
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
        return cast(list[TModel], model_classes[0].parse_file(path, **kwargs))
    lead = model_classes[0]
    cfg = get_rdf_config(lead)
    fmt = infer_format(path, kwargs.get("format"))
    resolved_base = (
        kwargs.get("base") if kwargs.get("base") is not None else cfg.base_uri
    )
    use_dataset = is_quad_format(fmt) or any(
        get_rdf_config(mc).graph_iri for mc in model_classes
    )
    if use_dataset:
        from triplemodel.io.dataset import load_models_from_dataset, parse_into_dataset

        dataset = parse_into_dataset(
            source=path,
            format=fmt,
            base=resolved_base,
            bind_prefixes=cfg.prefixes_dict,
            jsonld_context=cfg.jsonld_context,
            **kwargs,
        )
        return load_models_from_dataset(dataset, *model_classes, **kwargs)
    graph = parse_into_graph(
        source=path,
        format=fmt,
        base=resolved_base,
        bind_prefixes=cfg.prefixes_dict,
        jsonld_context=cfg.jsonld_context,
        **kwargs,
    )
    return load_models_from_graph(graph, *model_classes, **kwargs)


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
    return graph.serialize(  # ty: ignore[no-matching-overload]
        destination=destination,
        format=format,
        **ser_kwargs,
    )
