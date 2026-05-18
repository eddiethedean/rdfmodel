"""Import dispatch by rdf:type across registered model classes."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.term import Node

from triplemodel.config import RDF_TYPE, get_graph_context, get_rdf_config
from triplemodel.io.import_ import OnDuplicate, graph_to_model, graph_to_models
from triplemodel.protocols import (
    PredicateResolver as PredicateResolverProtocol,
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
    from triplemodel.protocols import iter_registered_type_uris

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
    for context in dataset.graphs():
        if not any(context.triples((subject, None, None))):
            continue
        model_cls = resolve_model_class(context, subject)
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
    raise ValueError(
        f"No registered TripleModel subject {subject!r} found in dataset contexts."
    )


def all_from_dataset_dispatch(
    dataset: Dataset,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[BaseModel]:
    """Load all subjects whose ``rdf:type`` maps to a registered class (per-class graph)."""
    from triplemodel.protocols import iter_registered_model_classes

    instances: list[BaseModel] = []
    for model_cls in iter_registered_model_classes():
        cfg = get_rdf_config(model_cls)
        context = get_graph_context(dataset, cfg.graph_iri)
        for instance in graph_to_models(
            context,
            model_cls,
            config=cfg,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        ):
            instances.append(instance)
    instances.sort(key=lambda m: m.subject_uri())
    return instances
