"""Base Pydantic model with RDF serialization."""

from __future__ import annotations

from typing_extensions import Self

from pydantic import BaseModel, ConfigDict
from rdflib import Graph

from triplemodel._config import GraphMode, RdfConfig, get_rdf_config
from triplemodel._graph import (
    OnDuplicate,
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
)
from triplemodel._sync import sync_to_graph
from triplemodel._typing import TripleRow


class TripleModel(BaseModel):
    """Pydantic model that can be serialized to and from an RDF graph.

    Subclasses declare RDF metadata on a nested ``Rdf`` class and map fields
    with :func:`~triplemodel.rdf_field` or ``Annotated[..., Predicate(...)]``.
    A nested ``Rdf`` on a subclass **replaces** the parent's config entirely;
    do not declare an empty ``class Rdf:`` on a child if you intend to inherit
    the parent's ``namespace``, ``type_uri``, or ``id_field``.

    Example::

        class Person(TripleModel):
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

    def to_triples(self, *, uri: str | None = None) -> list[TripleRow]:
        """Export instance data as (subject, predicate, object) tuples."""
        return model_to_triples(self, uri=uri)

    def to_graph(
        self,
        graph: Graph | None = None,
        *,
        uri: str | None = None,
        mode: GraphMode | None = None,
    ) -> Graph:
        """Serialize this instance into an rdflib ``Graph``.

        When ``mode`` is omitted, uses ``Rdf.graph_mode`` (default ``"add"``).
        """
        return model_to_graph(self, graph, uri=uri, mode=mode)

    def sync_to_graph(
        self,
        graph: Graph,
        *,
        uri: str | None = None,
        mode: GraphMode | None = None,
    ) -> Graph:
        """Update ``graph`` with owned triples for this instance (see ``mode``).

        When ``mode`` is omitted, uses ``Rdf.graph_mode`` if set to something other
        than ``"add"``; otherwise defaults to ``"replace"``.
        """
        return sync_to_graph(self, graph, uri=uri, mode=mode)

    @classmethod
    def from_graph(
        cls,
        graph: Graph,
        uri: str,
        *,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
    ) -> Self:
        """Construct an instance from triples about ``uri``."""
        return graph_to_model(
            graph,
            cls,
            uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
        )

    @classmethod
    def all_from_graph(
        cls,
        graph: Graph,
        *,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
    ) -> list[Self]:
        """Load every resource of this model's RDF type from ``graph``."""
        return graph_to_models(
            graph,
            cls,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
        )

    @classmethod
    def rdf_config(cls) -> RdfConfig:
        """Return resolved RDF configuration for this model class."""
        return get_rdf_config(cls)


__all__ = ["TripleModel"]
