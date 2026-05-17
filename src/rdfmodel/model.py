"""Base Pydantic model with RDF serialization."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict
from rdflib import Graph

from rdfmodel._config import RdfConfig, get_rdf_config
from rdfmodel._graph import (
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
    models_to_graph,
)


class RdfModel(BaseModel):
    """Pydantic model that can be serialized to and from an RDF graph.

    Subclasses declare RDF metadata on a nested ``Rdf`` class and map fields
    with :func:`~rdfmodel.rdf_field` or ``Annotated[..., Predicate(...)]``.

    Example::

        class Person(RdfModel):
            class Rdf:
                namespace = "http://example.org/people/"
                type_uri = "http://xmlns.com/foaf/0.1/Person"
                id_field = "slug"

            slug: str
            name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
    """

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=False,
    )

    def subject_uri(self, *, uri: str | None = None) -> str:
        """Return the RDF subject IRI for this instance."""
        if uri is not None:
            return uri
        return get_rdf_config(type(self)).subject_uri(self)

    def to_triples(self, *, uri: str | None = None) -> list[tuple[str, str, object]]:
        """Export instance data as (subject, predicate, object) tuples."""
        return model_to_triples(self, uri=uri)

    def to_graph(self, graph: Graph | None = None, *, uri: str | None = None) -> Graph:
        """Serialize this instance into an rdflib ``Graph``."""
        return model_to_graph(self, graph, uri=uri)

    @classmethod
    def from_graph(cls, graph: Graph, uri: str) -> Self:
        """Construct an instance from triples about ``uri``."""
        return graph_to_model(graph, cls, uri)

    @classmethod
    def all_from_graph(
        cls,
        graph: Graph,
        *,
        type_uri: str | None = None,
    ) -> list[Self]:
        """Load every resource of this model's RDF type from ``graph``."""
        return graph_to_models(graph, cls, type_uri=type_uri)

    @classmethod
    def rdf_config(cls) -> RdfConfig:
        """Return resolved RDF configuration for this model class."""
        return get_rdf_config(cls)


__all__ = [
    "RdfModel",
    "model_to_graph",
    "model_to_triples",
    "models_to_graph",
    "graph_to_model",
    "graph_to_models",
]
