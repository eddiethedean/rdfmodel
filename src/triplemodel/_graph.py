"""Build and parse rdflib graphs from Pydantic models."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from typing import Any, Literal, TypeVar

from typing import cast

from pydantic import BaseModel, ValidationError
from rdflib import BNode, Graph, URIRef
from rdflib.term import Node

from triplemodel._cardinality import (
    field_cardinality,
    nested_model_type,
    scalar_python_type,
    unwrap_annotation,
)
from triplemodel._config import (
    RDF_TYPE,
    GraphMode,
    RdfConfig,
    get_rdf_config,
    id_from_subject_uri,
)
from triplemodel._embed import export_nested_triples, import_nested_value
from triplemodel._fields import resolve_field_predicate
from triplemodel._namespaces import bind_namespaces
from triplemodel._types import python_to_term, term_to_python

T = TypeVar("T", bound=BaseModel)

OnDuplicate = Literal["ignore", "warn", "error"]


def _subject_node(subj: str) -> Node:
    if _looks_like_iri(subj):
        return URIRef(subj)
    return BNode(subj)


def _looks_like_iri(value: str) -> bool:
    from triplemodel._types import _looks_like_iri as looks

    return looks(value)


def _field_values_for_export(name: str, value: Any, field_info: Any) -> list[Any]:
    """Normalize a field value to a list of objects to emit as triples."""
    card = field_cardinality(field_info)
    if value is None:
        return []
    if card == "list":
        return [v for v in value if v is not None]
    if card == "set":
        return list(value)
    return [value]


def model_to_triples(
    model: BaseModel,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
) -> list[tuple[str | Node, str, Any]]:
    """Return (subject, predicate, object) tuples for a model instance."""
    cls = type(model)
    cfg = config or get_rdf_config(cls)
    prefixes = cfg.prefixes_dict
    subject = uri or cfg.subject_uri(model)
    triples: list[tuple[str | Node, str, Any]] = []

    if cfg.type_uri:
        triples.append((subject, RDF_TYPE, cfg.type_uri))

    id_field = cfg.id_field
    for name, field_info in cls.model_fields.items():
        if id_field and name == id_field:
            continue
        predicate = resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        value = getattr(model, name)
        card = field_cardinality(field_info)

        if card == "nested":
            if value is None:
                continue
            triples.extend(
                export_nested_triples(
                    subject,
                    predicate,
                    value,
                    embed=cfg.embed,
                    config=cfg,
                )
            )
            continue

        for item in _field_values_for_export(name, value, field_info):
            triples.append((subject, predicate, item))

    return triples


def model_to_graph(
    model: BaseModel,
    graph: Graph | None = None,
    *,
    uri: str | None = None,
    config: RdfConfig | None = None,
    mode: GraphMode = "add",
    bind: bool | None = None,
) -> Graph:
    """Add triples for ``model`` to ``graph`` (or a new graph) and return it."""
    if mode != "add":
        from triplemodel._sync import sync_to_graph

        return sync_to_graph(
            model,
            graph,
            uri=uri,
            mode=mode,
            config=config,
            bind=bind if bind is not None else graph is None,
        )

    g = Graph() if graph is None else graph
    cfg = config or get_rdf_config(type(model))
    if bind if bind is not None else graph is None:
        if cfg.prefixes:
            bind_namespaces(g, cfg.prefixes_dict)

    for subj, pred, obj in model_to_triples(model, uri=uri, config=cfg):
        subj_node = subj if isinstance(subj, Node) else _subject_node(subj)
        g.add((subj_node, URIRef(pred), python_to_term(obj)))
    return g


def models_to_graph(
    models: Sequence[BaseModel],
    graph: Graph | None = None,
    *,
    mode: GraphMode = "add",
) -> Graph:
    """Serialize multiple model instances into one graph."""
    g = Graph() if graph is None else graph
    for model in models:
        model_to_graph(model, g, mode=mode, bind=False)
    return g


def _import_field_value(
    graph: Graph,
    objects: list[Any],
    field_info: Any,
    field_name: str,
    predicate: str,
    uri: str,
    *,
    embed: str,
    on_duplicate: OnDuplicate,
) -> Any:
    from rdflib.term import Node

    card = field_cardinality(field_info)
    nested_cls = nested_model_type(field_info)

    if not objects:
        if card in ("list", "set"):
            return [] if card == "list" else set()
        return None

    if card == "nested" and nested_cls is not None:
        if len(objects) > 1 and on_duplicate != "ignore":
            _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
        term = objects[0]
        if not isinstance(term, Node):
            raise ValueError(f"Cannot import nested field {field_name!r} from {term!r}")
        return import_nested_value(
            graph, term, cast(type[BaseModel], nested_cls), embed=embed
        )

    if card == "list":
        py_type = scalar_python_type(field_info)
        return [_term_to_field(o, py_type, field_name, predicate, uri) for o in objects]

    if card == "set":
        py_type = scalar_python_type(field_info)
        return {_term_to_field(o, py_type, field_name, predicate, uri) for o in objects}

    if len(objects) > 1:
        _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
    py_type = scalar_python_type(field_info)
    return _term_to_field(objects[0], py_type, field_name, predicate, uri)


def _handle_duplicate(
    field_name: str,
    predicate: str,
    uri: str,
    count: int,
    on_duplicate: OnDuplicate,
) -> None:
    dup_msg = (
        f"Multiple objects ({count}) for field {field_name!r} "
        f"(predicate {predicate!r}, subject {uri!r}); using the first only."
    )
    if on_duplicate == "error":
        raise ValueError(dup_msg)
    if on_duplicate == "warn":
        warnings.warn(dup_msg, stacklevel=3)


def _term_to_field(
    term: Any,
    py_type: type | None,
    field_name: str,
    predicate: str,
    uri: str,
) -> Any:
    try:
        return term_to_python(term, py_type)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Cannot convert object for field {field_name!r} "
            f"(predicate {predicate!r}, subject {uri!r}): {exc}"
        ) from exc


def graph_to_model(
    graph: Graph,
    model_cls: type[T],
    uri: str | Node,
    *,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
) -> T:
    """Hydrate a single model instance from triples about ``uri``."""
    cfg = config or get_rdf_config(model_cls)
    prefixes = cfg.prefixes_dict
    subject: Node = uri if isinstance(uri, Node) else URIRef(uri)
    uri_str = str(uri)

    if validate_type and cfg.type_uri:
        type_ref = URIRef(cfg.type_uri)
        if (subject, URIRef(RDF_TYPE), type_ref) not in graph:
            raise ValueError(
                f"Subject {uri_str!r} does not have rdf:type {cfg.type_uri!r} required by "
                f"{model_cls.__name__}."
            )

    data: dict[str, Any] = {}

    if cfg.id_field and cfg.namespace and isinstance(uri, str):
        extracted = id_from_subject_uri(cfg.namespace, uri_str)
        if extracted is not None:
            data[cfg.id_field] = extracted

    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        predicate = resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        pred_ref = URIRef(predicate)
        objects = list(graph.objects(subject, pred_ref))
        if not objects:
            continue
        card = field_cardinality(field_info)
        try:
            data[name] = _import_field_value(
                graph,
                objects,
                field_info,
                name,
                predicate,
                uri_str,
                embed=cfg.embed,
                on_duplicate=on_duplicate if card in ("scalar", "nested") else "ignore",
            )
        except ValueError as exc:
            raise exc

    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"Cannot validate {model_cls.__name__} from graph for subject {uri_str!r}: {exc}"
        ) from exc


def graph_to_models(
    graph: Graph,
    model_cls: type[T],
    *,
    type_uri: str | None = None,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
) -> list[T]:
    """Load all resources of ``type_uri`` (or the model's configured type) as models."""
    cfg = config or get_rdf_config(model_cls)
    rdf_type = type_uri or cfg.type_uri
    if not rdf_type:
        raise ValueError("type_uri is required when the model has no Rdf.type_uri.")

    instances: list[T] = []
    for subject in graph.subjects(URIRef(RDF_TYPE), URIRef(rdf_type)):
        if isinstance(subject, URIRef):
            instances.append(
                graph_to_model(
                    graph,
                    model_cls,
                    str(subject),
                    config=cfg,
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                )
            )
    return instances


# Backward-compatible alias used by tests
def _unwrap_optional(annotation: Any) -> Any:
    return unwrap_annotation(annotation)
