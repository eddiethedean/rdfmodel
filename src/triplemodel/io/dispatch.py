"""Import dispatch by rdf:type across registered model classes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from pydantic import BaseModel
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.term import Node

from triplemodel.config import get_graph_context, get_rdf_config
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.protocols import (
    PredicateResolver as PredicateResolverProtocol,
    iter_registered_model_classes,
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
    """Load all subjects that resolve to a registered model class."""
    from triplemodel.config import get_rdf_config
    from triplemodel.io.skolem import apply_de_skolemize

    if de_skolemize is None:
        do_de = any(
            get_rdf_config(cls).skolemize_import
            for cls in iter_registered_model_classes()
        )
    else:
        do_de = de_skolemize
    graph = apply_de_skolemize(graph, de_skolemize=do_de)

    seen: set[str] = set()
    instances: list[BaseModel] = []
    for subject in sorted(graph.subjects(None, None), key=str):
        if isinstance(subject, Literal) or not isinstance(subject, URIRef):
            continue
        key = str(subject)
        if key in seen:
            continue
        try:
            model_cls = resolve_model_class(graph, subject)
        except ValueError:
            continue
        seen.add(key)
        instances.append(
            graph_to_model(
                graph,
                model_cls,
                subject,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=False,
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

    from triplemodel.io.skolem import apply_de_skolemize

    if de_skolemize is None:
        classes_for_skolem = (
            list(allowed)
            if allowed is not None
            else list(iter_registered_model_classes())
        )
        do_de = any(get_rdf_config(cls).skolemize_import for cls in classes_for_skolem)
    else:
        do_de = de_skolemize

    seen: set[str] = set()
    instances: list[BaseModel] = []
    contexts_de_skolemized: set[object] = set()
    for type_uri in type_uris:
        model_cls = model_class_for_type_uri(type_uri)
        if model_cls is None:
            continue
        cfg = get_rdf_config(model_cls)
        context = get_graph_context(dataset, cfg.graph_iri)
        ctx_id = context.identifier
        if ctx_id not in contexts_de_skolemized:
            apply_de_skolemize(context, de_skolemize=do_de)
            contexts_de_skolemized.add(ctx_id)
        for subject in sorted(context.subjects(None, None), key=str):
            if isinstance(subject, Literal) or not isinstance(subject, URIRef):
                continue
            key = str(subject)
            if key in seen:
                continue
            matching = _contexts_for_subject(dataset, subject)
            if not matching:
                continue
            try:
                type_view = (
                    _union_subject_view(matching, subject)
                    if len(matching) > 1
                    else context
                )
                resolved_cls = resolve_model_class(type_view, subject)
            except ValueError:
                continue
            if allowed is not None and resolved_cls not in allowed:
                continue
            seen.add(key)
            load_context, load_cls = _resolve_dataset_context(
                dataset, subject, matching
            )
            instances.append(
                graph_to_model(
                    load_context,
                    load_cls,
                    subject,
                    config=get_rdf_config(load_cls),
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                    resolver=resolver,
                    registry=registry,
                    de_skolemize=False,
                )
            )
    instances.sort(key=lambda m: m.subject_uri())
    return instances
