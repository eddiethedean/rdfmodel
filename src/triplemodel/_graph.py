"""Build and parse rdflib graphs from Pydantic models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar, get_args, get_origin

from pydantic import BaseModel
from rdflib import Graph, URIRef

from triplemodel._config import RDF_TYPE, RdfConfig, get_rdf_config, id_from_subject_uri
from triplemodel._fields import predicate_for_field, predicate_from_annotation
from triplemodel._types import python_to_term, term_to_python

T = TypeVar("T", bound=BaseModel)


def model_to_triples(
    model: BaseModel,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
) -> list[tuple[str, str, Any]]:
    """Return (subject, predicate, object) tuples for a model instance."""
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    subject = uri or cfg.subject_uri(model)
    triples: list[tuple[str, str, Any]] = []

    if cfg.type_uri:
        triples.append((subject, RDF_TYPE, cfg.type_uri))

    id_field = cfg.id_field
    for name, field_info in cls.model_fields.items():
        if id_field and name == id_field:
            continue
        predicate = predicate_for_field(field_info) or predicate_from_annotation(
            field_info.annotation
        )
        if predicate is None:
            continue
        value = getattr(model, name)
        if value is None:
            continue
        triples.append((subject, predicate, value))

    return triples


def model_to_graph(
    model: BaseModel,
    graph: Graph | None = None,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
) -> Graph:
    """Add triples for ``model`` to ``graph`` (or a new graph) and return it."""
    # rdflib Graph() is falsy when empty — must not use `graph or Graph()`.
    g = Graph() if graph is None else graph
    for subj, pred, obj in model_to_triples(model, uri=uri, config=config):
        g.add((URIRef(subj), URIRef(pred), python_to_term(obj)))
    return g


def models_to_graph(
    models: Sequence[BaseModel],
    graph: Graph | None = None,
) -> Graph:
    """Serialize multiple model instances into one graph."""
    g = Graph() if graph is None else graph
    for model in models:
        model_to_graph(model, g)
    return g


def _unwrap_optional(annotation: Any) -> Any:
    import types
    from typing import Union

    origin = get_origin(annotation)
    if origin is None:
        return annotation
    if origin in (Union, types.UnionType):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        return non_none[0] if len(non_none) == 1 else annotation
    return annotation


def graph_to_model(
    graph: Graph,
    model_cls: type[T],
    uri: str,
    *,
    config: RdfConfig | None = None,
) -> T:
    """Hydrate a single model instance from triples about ``uri``."""
    cfg = config or get_rdf_config(model_cls)
    subject = URIRef(uri)
    data: dict[str, Any] = {}

    if cfg.id_field and cfg.namespace:
        extracted = id_from_subject_uri(cfg.namespace, uri)
        if extracted is not None:
            data[cfg.id_field] = extracted

    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        predicate = predicate_for_field(field_info) or predicate_from_annotation(
            field_info.annotation
        )
        if predicate is None:
            continue
        pred_ref = URIRef(predicate)
        objects = list(graph.objects(subject, pred_ref))
        if not objects:
            continue
        # Multi-valued predicates: first object only until 0.2.0.
        target = _unwrap_optional(field_info.annotation)
        py_type = target if isinstance(target, type) else None
        try:
            data[name] = term_to_python(objects[0], py_type)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Cannot convert object for field {name!r} "
                f"(predicate {predicate!r}, subject {uri!r}): {exc}"
            ) from exc

    return model_cls.model_validate(data)


def graph_to_models(
    graph: Graph,
    model_cls: type[T],
    *,
    type_uri: str | None = None,
    config: RdfConfig | None = None,
) -> list[T]:
    """Load all resources of ``type_uri`` (or the model's configured type) as models."""
    cfg = config or get_rdf_config(model_cls)
    rdf_type = type_uri or cfg.type_uri
    if not rdf_type:
        raise ValueError("type_uri is required when the model has no Rdf.type_uri.")

    instances: list[T] = []
    for subject in graph.subjects(URIRef(RDF_TYPE), URIRef(rdf_type)):
        if isinstance(subject, URIRef):
            instances.append(graph_to_model(graph, model_cls, str(subject), config=cfg))
    return instances
