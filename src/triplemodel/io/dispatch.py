"""Import dispatch by rdf:type across registered model classes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from pydantic import BaseModel
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.term import Node

from triplemodel.config import RDF_TYPE, get_graph_context, get_rdf_config
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.protocols import (
    PredicateResolver as PredicateResolverProtocol,
    iter_registered_type_uris,
    model_class_for_type_uri,
    resolve_model_class,
)
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)


def graph_to_model_dispatch(
    graph: Graph,
    uri: str | Node,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> BaseModel:
    """Hydrate using the most specific registered class for the subject's types."""
    subject: Node = uri if isinstance(uri, Node) else URIRef(uri)
    model_cls = resolve_model_class(graph, subject)
    return graph_to_model(
        graph,
        model_cls,
        subject,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


def all_from_graph_dispatch(
    graph: Graph,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[BaseModel]:
    """Load all subjects whose ``rdf:type`` maps to a registered model class."""
    seen: set[str] = set()
    instances: list[BaseModel] = []
    for type_uri in sorted(iter_registered_type_uris()):
        for subject in sorted(
            graph.subjects(URIRef(RDF_TYPE), URIRef(type_uri)),
            key=str,
        ):
            if isinstance(subject, Literal) or not isinstance(subject, URIRef):
                continue
            key = str(subject)
            if key in seen:
                continue
            seen.add(key)
            instances.append(
                graph_to_model_dispatch(
                    graph,
                    subject,
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                    resolver=resolver,
                    registry=registry,
                    de_skolemize=de_skolemize,
                )
            )
    instances.sort(key=lambda m: m.subject_uri())
    return instances


def _contexts_for_subject(dataset: Dataset, subject: Node) -> list[Graph]:
    return [
        context
        for context in dataset.graphs()
        if any(context.triples((subject, None, None)))
    ]


def _union_subject_view(contexts: list[Graph], subject: Node) -> Graph:
    """Merge ``(subject, ?, ?)`` triples from each context for type resolution."""
    merged = Graph()
    for context in contexts:
        for triple in context.triples((subject, None, None)):
            merged.add(triple)
    return merged


def _resolve_dataset_context(
    dataset: Dataset,
    subject: Node,
    matching: list[Graph],
) -> tuple[Graph, type[BaseModel]]:
    """Pick graph context and model class when ``subject`` appears in ``matching`` contexts."""
    type_view = _union_subject_view(matching, subject)
    model_cls = resolve_model_class(type_view, subject)
    if len(matching) == 1:
        return matching[0], model_cls
    cfg = get_rdf_config(model_cls)
    preferred = get_graph_context(dataset, cfg.graph_iri)
    by_id = {ctx.identifier: ctx for ctx in matching}
    preferred_id = preferred.identifier
    if preferred_id in by_id:
        return by_id[preferred_id], model_cls
    graph_ids = sorted(str(gid) for gid in by_id)
    raise ValueError(
        f"Subject {subject!r} appears in multiple dataset graphs {graph_ids!r}; "
        f"cannot resolve context for {model_cls.__name__} "
        f"(expected graph {preferred_id!r})."
    )


def graph_to_model_dispatch_from_dataset(
    dataset: Dataset,
    uri: str | Node,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> BaseModel:
    """Hydrate using the most specific registered class for the subject's named graph."""
    subject: Node = uri if isinstance(uri, Node) else URIRef(uri)
    matching = _contexts_for_subject(dataset, subject)
    if not matching:
        raise ValueError(
            f"No registered TripleModel subject {subject!r} found in dataset contexts."
        )
    context, model_cls = _resolve_dataset_context(dataset, subject, matching)
    cfg = get_rdf_config(model_cls)
    return graph_to_model(
        context,
        model_cls,
        subject,
        config=cfg,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


def _type_uris_for_dispatch(
    model_classes: Sequence[type[BaseModel]] | None,
) -> list[str]:
    if model_classes is None:
        return sorted(iter_registered_type_uris())
    uris: set[str] = set()
    for model_cls in model_classes:
        type_uri = get_rdf_config(model_cls).type_uri
        if type_uri:
            uris.add(type_uri)
    return sorted(uris)


def all_from_dataset_dispatch(
    dataset: Dataset,
    *,
    model_classes: Sequence[type[BaseModel]] | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[BaseModel]:
    """Load all subjects whose ``rdf:type`` maps to a registered class (per-class graph).

    When ``model_classes`` is set, only those classes are loaded (recommended when the
    process has other registered models from unrelated modules).
    """
    from triplemodel.model import TripleModel

    allowed: set[type[BaseModel]] | None = None
    if model_classes is None:
        type_uris = _type_uris_for_dispatch(None)
    else:
        for model_cls in model_classes:
            if not issubclass(model_cls, TripleModel):
                raise TypeError(f"{model_cls!r} is not a TripleModel subclass.")
        allowed = set(model_classes)
        type_uris = _type_uris_for_dispatch(model_classes)

    seen: set[str] = set()
    instances: list[BaseModel] = []
    for type_uri in type_uris:
        model_cls = model_class_for_type_uri(type_uri)
        if model_cls is None:
            continue
        cfg = get_rdf_config(model_cls)
        context = get_graph_context(dataset, cfg.graph_iri)
        for subject in sorted(
            context.subjects(URIRef(RDF_TYPE), URIRef(type_uri)),
            key=str,
        ):
            if isinstance(subject, Literal) or not isinstance(subject, URIRef):
                continue
            key = str(subject)
            if key in seen:
                continue
            seen.add(key)
            instance = graph_to_model_dispatch_from_dataset(
                dataset,
                subject,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            )
            if allowed is None or type(instance) in allowed:
                instances.append(instance)
    instances.sort(key=lambda m: m.subject_uri())
    return instances
