"""Import RDF graphs into Pydantic models."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from typing import TypeVar, cast

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from rdflib import Graph, URIRef, XSD
from rdflib import Literal as RdfLiteral
from rdflib.term import Node

from triplemodel._typing import (
    ModelFieldScalar,
    ModelFieldValue,
    ModelInitData,
    OnDuplicate,
)
from triplemodel.config import (
    RDF_TYPE,
    EmbedMode,
    RdfConfig,
    get_rdf_config,
    id_from_subject_uri,
)
from triplemodel.embed.strategies import import_nested_value
from triplemodel.fields.metadata import (
    id_field_is_iri_id,
    inverse_for_field,
    predicate_for_field,
    transitive_for_field,
)
from triplemodel.io.rdfs import transitive_objects
from triplemodel.namespaces import resolve_predicate
from triplemodel.fields.resolver import default_resolver
from triplemodel.metadata.predicate_map import (
    owned_predicates_for_class,
    predicate_map_for_class,
)
from triplemodel.metadata.cardinality import (
    field_cardinality,
    nested_model_type,
    raise_if_inverse_collection,
    raise_if_nested_collection,
    scalar_python_type,
    union_member_types,
)
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.collection import read_rdf_list
from triplemodel.terms.convert import term_to_python
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)


def _handle_duplicate(
    field_name: str,
    predicate: str,
    uri: str,
    count: int,
    on_duplicate: OnDuplicate,
    *,
    message: str | None = None,
) -> None:
    dup_msg = message or (
        f"Multiple objects ({count}) for field {field_name!r} "
        f"(predicate {predicate!r}, subject {uri!r}); using the first only."
    )
    if on_duplicate == "error":
        raise ValueError(dup_msg)
    if on_duplicate == "warn":
        warnings.warn(dup_msg, stacklevel=3)


def _enforce_subject_predicates(
    graph: Graph,
    subject: Node,
    uri_str: str,
    model_cls: type[BaseModel],
    cfg: RdfConfig,
    *,
    resolver: PredicateResolverProtocol | None = None,
    strict_import: bool | None = None,
    warn_unmapped: bool | None = None,
) -> None:
    """Optionally validate triples on ``subject`` against owned predicates."""
    do_strict = cfg.strict_import if strict_import is None else strict_import
    do_warn = cfg.warn_unmapped_fields if warn_unmapped is None else warn_unmapped
    if not do_strict and not do_warn:
        return
    owned = owned_predicates_for_class(model_cls, resolver=resolver, config=cfg)
    allowed = set(owned) | {RDF_TYPE}
    for _, pred, _ in graph.triples((subject, None, None)):
        pred_str = str(pred)
        if pred_str in allowed:
            continue
        msg = (
            f"Predicate {pred_str!r} on subject {uri_str!r} is not mapped on "
            f"{model_cls.__name__}."
        )
        if do_strict:
            raise ValueError(msg)
        if do_warn:
            warnings.warn(msg, stacklevel=3)


def _handle_forward_inverse_conflict(
    field_name: str,
    forward_predicate: str,
    inverse_predicate: str,
    uri: str,
    on_duplicate: OnDuplicate,
) -> None:
    msg = (
        f"Both forward predicate {forward_predicate!r} and inverse "
        f"{inverse_predicate!r} have values for field {field_name!r} "
        f"(subject {uri!r}); using forward objects only."
    )
    if on_duplicate == "error":
        raise ValueError(msg)
    if on_duplicate == "warn":
        warnings.warn(msg, stacklevel=3)


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
    de_skolemize: bool = False,
) -> ModelFieldValue:
    """Hydrate a single model field from RDF objects (used by :func:`graph_to_model`)."""
    card = field_cardinality(field_info)
    nested_cls = nested_model_type(field_info)

    if not objects:
        if card in ("list", "set"):
            return [] if card == "list" else set()
        return None

    if card in ("nested", "ref") and nested_cls is not None:
        if len(objects) > 1 and on_duplicate != "ignore":
            _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
        term = objects[0]
        if not isinstance(term, Node):
            raise ValueError(f"Cannot import nested field {field_name!r} from {term!r}")
        nested_type = cast(type[BaseModel], nested_cls)
        if card == "ref":
            if not isinstance(term, URIRef):
                raise ValueError(
                    f"Cannot import ref field {field_name!r} from term {term!r}; "
                    "expected a URI resource."
                )
            return graph_to_model(
                graph,
                nested_type,
                term,
                on_duplicate=on_duplicate,
                registry=registry,
                de_skolemize=de_skolemize,
            )
        return import_nested_value(
            graph,
            term,
            nested_type,
            embed=embed,
            on_duplicate=on_duplicate,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    if card == "list":
        if len(objects) > 1 and on_duplicate != "ignore":
            _handle_duplicate(field_name, predicate, uri, len(objects), on_duplicate)
        py_type = scalar_python_type(field_info)
        return read_rdf_list(graph, objects[0], py_type, registry=registry)

    if card == "set":
        py_type = scalar_python_type(field_info)
        if transitive_for_field(field_info):
            pred_uri = predicate_for_field(field_info) or predicate
            object_uris = transitive_objects(graph, uri, pred_uri)
            return {
                _term_to_field(
                    URIRef(o),
                    py_type,
                    field_name,
                    pred_uri,
                    uri,
                    field_info=field_info,
                    registry=registry,
                )
                for o in object_uris
            }
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
    strict_import: bool | None = None,
    warn_unmapped_fields: bool | None = None,
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
    elif validate_type and cfg.instance_of_predicates:
        prefixes = cfg.prefixes_dict
        type_uris = cfg.instance_type_uris
        matched = False
        for pred_raw in cfg.instance_of_predicates:
            pred_ref = URIRef(resolve_predicate(pred_raw, prefixes))
            if type_uris:
                for type_raw in type_uris:
                    type_ref = URIRef(resolve_predicate(type_raw, prefixes))
                    if (subject, pred_ref, type_ref) in graph:
                        matched = True
                        break
            elif list(graph.objects(subject, pred_ref)):
                matched = True
            if matched:
                break
        if not matched:
            raise ValueError(
                f"Subject {uri_str!r} does not match instance_of constraints for "
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

    for name, predicate in predicate_map_for_class(model_cls, resolver=r).items():
        if predicate is None:
            continue
        field_info = model_cls.model_fields[name]
        raise_if_nested_collection(field_info)
        raise_if_inverse_collection(field_info)
        pred_ref = URIRef(predicate)
        forward_objects = list(graph.objects(subject, pred_ref))
        inv_raw = inverse_for_field(field_info)
        inverse_objects: list[Node] = []
        inv_predicate: str | None = None
        if inv_raw is not None:
            inv_predicate = resolve_predicate(inv_raw, prefixes)
            inverse_objects = cast(
                list[Node],
                sorted(
                    graph.subjects(URIRef(inv_predicate), subject),
                    key=str,
                ),
            )
        if forward_objects and inverse_objects and inv_predicate is not None:
            if on_duplicate != "ignore":
                _handle_forward_inverse_conflict(
                    name,
                    predicate,
                    inv_predicate,
                    uri_str,
                    on_duplicate,
                )
        if forward_objects:
            objects = forward_objects
        elif inverse_objects:
            objects = inverse_objects
        else:
            continue
        data[name] = import_field_value(
            graph,
            objects,
            field_info,
            name,
            predicate,
            uri_str,
            embed=cfg.embed,
            on_duplicate=on_duplicate,
            registry=registry,
            de_skolemize=False,
        )

    _enforce_subject_predicates(
        graph,
        subject,
        uri_str,
        model_cls,
        cfg,
        resolver=r,
        strict_import=strict_import,
        warn_unmapped=warn_unmapped_fields,
    )

    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"Cannot validate {model_cls.__name__} from graph for subject {uri_str!r}: {exc}"
        ) from exc


def _subject_uris_for_model(
    graph: Graph,
    model_cls: type[T],
    cfg: RdfConfig,
    *,
    type_uri: str | None = None,
    resolver: PredicateResolverProtocol | None = None,
) -> list[str]:
    from triplemodel.io.discovery import (
        discover_subject_uris,
        discover_subjects_by_instance_of,
    )

    rdf_type = type_uri if type_uri is not None else cfg.type_uri
    if rdf_type:
        return sorted(
            str(s)
            for s in graph.subjects(URIRef(RDF_TYPE), URIRef(rdf_type))
            if isinstance(s, URIRef)
        )
    if cfg.instance_of_predicates:
        return discover_subjects_by_instance_of(graph, cfg)
    return discover_subject_uris(graph, model_cls, cfg, resolver=resolver)


def iter_graph_to_models(
    graph: Graph,
    model_cls: type[T],
    *,
    chunk_size: int = 500,
    type_uri: str | None = None,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    strict_import: bool | None = None,
    warn_unmapped_fields: bool | None = None,
) -> Iterator[list[T]]:
    """Yield chunks of model instances loaded from ``graph``."""
    cfg = config or get_rdf_config(model_cls)
    from triplemodel.io.skolem import apply_de_skolemize

    do_de = cfg.skolemize_import if de_skolemize is None else de_skolemize
    graph = apply_de_skolemize(graph, de_skolemize=do_de)
    uris = _subject_uris_for_model(
        graph, model_cls, cfg, type_uri=type_uri, resolver=resolver
    )

    def _gen() -> Iterator[list[T]]:
        for start in range(0, len(uris), chunk_size):
            chunk_uris = uris[start : start + chunk_size]
            chunk: list[T] = []
            for subject_uri in chunk_uris:
                chunk.append(
                    graph_to_model(
                        graph,
                        model_cls,
                        subject_uri,
                        config=cfg,
                        validate_type=validate_type,
                        on_duplicate=on_duplicate,
                        resolver=resolver,
                        registry=registry,
                        de_skolemize=False,
                        strict_import=strict_import,
                        warn_unmapped_fields=warn_unmapped_fields,
                    )
                )
            yield chunk

    return _gen()


def graph_to_models(
    graph: Graph,
    model_cls: type[T],
    *,
    chunk_size: int | None = None,
    type_uri: str | None = None,
    config: RdfConfig | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    strict_import: bool | None = None,
    warn_unmapped_fields: bool | None = None,
) -> list[T]:
    """Load all resources of ``type_uri`` (or the model's configured type) as models."""
    cfg = config or get_rdf_config(model_cls)
    size = chunk_size if chunk_size is not None else 2**31
    instances: list[T] = []
    for chunk in iter_graph_to_models(
        graph,
        model_cls,
        chunk_size=size,
        type_uri=type_uri,
        config=cfg,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
        strict_import=strict_import,
        warn_unmapped_fields=warn_unmapped_fields,
    ):
        instances.extend(chunk)
    if cfg.type_uri or type_uri:
        instances.sort(key=lambda m: cfg.subject_uri(m))
    return instances
