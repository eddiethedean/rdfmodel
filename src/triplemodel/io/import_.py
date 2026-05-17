"""Import RDF graphs into Pydantic models."""

from __future__ import annotations

import warnings
from typing import Literal, TypeVar, cast

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from rdflib import Graph, URIRef, XSD
from rdflib import Literal as RdfLiteral
from rdflib.term import Node

from triplemodel._typing import ModelFieldScalar, ModelFieldValue, ModelInitData
from triplemodel.config import (
    RDF_TYPE,
    EmbedMode,
    RdfConfig,
    get_rdf_config,
    id_from_subject_uri,
)
from triplemodel.embed.strategies import import_nested_value
from triplemodel.fields.metadata import id_field_is_iri_id
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.cardinality import (
    field_cardinality,
    nested_model_type,
    raise_if_nested_collection,
    scalar_python_type,
    union_member_types,
)
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.collection import read_rdf_list
from triplemodel.terms.convert import term_to_python
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)

OnDuplicate = Literal["ignore", "warn", "error"]


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


def _union_conversion_order(term: Node, members: tuple[type, ...]) -> tuple[type, ...]:
    """Prefer union members that match the literal datatype."""
    if not isinstance(term, RdfLiteral) or not members:
        return members
    if term.datatype == XSD.integer and int in members:
        return (int,) + tuple(m for m in members if m is not int)
    if term.datatype in (XSD.string, None) and str in members:
        return (str,) + tuple(m for m in members if m is not str)
    return members


def _term_to_field(
    term: Node,
    py_type: type | None,
    field_name: str,
    predicate: str,
    uri: str,
    *,
    field_info: FieldInfo | None = None,
    registry: LiteralRegistry = default_registry,
) -> ModelFieldScalar:
    members = union_member_types(field_info) if field_info is not None else ()
    types_to_try: tuple[type | None, ...]
    if members:
        types_to_try = _union_conversion_order(term, members)
    elif py_type is not None:
        types_to_try = (py_type,)
    else:
        types_to_try = (None,)
    last_exc: Exception | None = None
    for tp in types_to_try:
        try:
            return cast(ModelFieldScalar, term_to_python(term, tp, registry=registry))
        except (ValueError, TypeError) as exc:
            last_exc = exc
    msg = (
        f"Cannot convert object for field {field_name!r} "
        f"(predicate {predicate!r}, subject {uri!r})"
    )
    raise ValueError(f"{msg}: {last_exc}") from last_exc


def import_field_value(
    graph: Graph,
    objects: list[Node],
    field_info: FieldInfo,
    field_name: str,
    predicate: str,
    uri: str,
    *,
    embed: EmbedMode,
    on_duplicate: OnDuplicate,
    registry: LiteralRegistry = default_registry,
) -> ModelFieldValue:
    """Hydrate a single model field from RDF objects (used by :func:`graph_to_model`)."""
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
            graph,
            term,
            cast(type[BaseModel], nested_cls),
            embed=embed,
            registry=registry,
        )

    if card == "list":
        if len(objects) > 1 and on_duplicate != "ignore":
            _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
        py_type = scalar_python_type(field_info)
        return read_rdf_list(graph, objects[0], py_type, registry=registry)

    if card == "set":
        py_type = scalar_python_type(field_info)
        return {
            _term_to_field(
                o,
                py_type,
                field_name,
                predicate,
                uri,
                field_info=field_info,
                registry=registry,
            )
            for o in objects
        }

    if len(objects) > 1:
        _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
    py_type = scalar_python_type(field_info)
    return _term_to_field(
        objects[0],
        py_type,
        field_name,
        predicate,
        uri,
        field_info=field_info,
        registry=registry,
    )


def graph_to_model(
    graph: Graph,
    model_cls: type[T],
    uri: str | Node,
    *,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> T:
    """Hydrate a single model instance from triples about ``uri``."""
    cfg = config or get_rdf_config(model_cls)
    from triplemodel.io.skolem import apply_de_skolemize

    do_de = cfg.skolemize_import if de_skolemize is None else de_skolemize
    graph = apply_de_skolemize(graph, de_skolemize=do_de)
    r = resolver or default_resolver
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

    data: ModelInitData = {}

    if cfg.id_field:
        extracted = (
            id_from_subject_uri(cfg.namespace, uri_str) if cfg.namespace else None
        )
        if extracted is not None:
            data[cfg.id_field] = extracted
        elif id_field_is_iri_id(model_cls, cfg.id_field):
            data[cfg.id_field] = uri_str

    for name, field_info in model_cls.model_fields.items():
        if cfg.id_field and name == cfg.id_field:
            continue
        predicate = r.resolve_field_predicate(field_info, prefixes)
        if predicate is None:
            continue
        raise_if_nested_collection(field_info)
        pred_ref = URIRef(predicate)
        objects = list(graph.objects(subject, pred_ref))
        if not objects:
            continue
        card = field_cardinality(field_info)
        data[name] = import_field_value(
            graph,
            objects,
            field_info,
            name,
            predicate,
            uri_str,
            embed=cfg.embed,
            on_duplicate=on_duplicate if card in ("scalar", "nested") else "ignore",
            registry=registry,
        )

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
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
) -> list[T]:
    """Load all resources of ``type_uri`` (or the model's configured type) as models."""
    from triplemodel.io.discovery import discover_subject_uris

    cfg = config or get_rdf_config(model_cls)
    rdf_type = type_uri if type_uri is not None else cfg.type_uri

    instances: list[T] = []
    if rdf_type:
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
                        resolver=resolver,
                        registry=registry,
                    )
                )
        return instances

    for subject_uri in discover_subject_uris(graph, model_cls, cfg, resolver=resolver):
        instances.append(
            graph_to_model(
                graph,
                model_cls,
                subject_uri,
                config=cfg,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
            )
        )
    return instances
