"""Import dispatch by rdf:type across registered model classes."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef
from rdflib.term import Node

from triplemodel.config import RDF_TYPE
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.protocols import resolve_model_class
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)


def graph_to_model_dispatch(
    graph: Graph,
    uri: str | Node,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
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
        registry=registry,
        de_skolemize=de_skolemize,
    )


def all_from_graph_dispatch(
    graph: Graph,
    *,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
) -> list[BaseModel]:
    """Load all subjects whose ``rdf:type`` maps to a registered model class."""
    from triplemodel.protocols import iter_registered_type_uris

    seen: set[str] = set()
    instances: list[BaseModel] = []
    for type_uri in iter_registered_type_uris():
        for subject in graph.subjects(URIRef(RDF_TYPE), URIRef(type_uri)):
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
                    registry=registry,
                    de_skolemize=de_skolemize,
                )
            )
    return instances
