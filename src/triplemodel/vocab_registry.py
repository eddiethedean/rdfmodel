"""Vocabulary registry: prefixes, type URIs, and model classes."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel
from rdflib import Graph
from rdflib.term import Node

from triplemodel.config import get_rdf_config
from triplemodel.io.rdfs import resolve_model_class_with_rdfs
from triplemodel.namespaces import bind_namespaces
from triplemodel.protocols import (
    iter_registered_model_classes,
    model_class_for_type_uri,
    register_rdf_resource,
)


@dataclass
class VocabularyRegistry:
    """Maps RDF type IRIs and namespace prefixes to :class:`~triplemodel.TripleModel` classes."""

    type_uri_to_class: dict[str, type[BaseModel]] = field(default_factory=dict)
    prefix_to_uri: dict[str, str] = field(default_factory=dict)

    def register(self, model_cls: type[BaseModel]) -> None:
        """Register a model class and its ``Rdf`` metadata."""
        register_rdf_resource(model_cls)
        cfg = get_rdf_config(model_cls)
        if cfg.type_uri:
            self.type_uri_to_class[cfg.type_uri] = model_cls
        for prefix, uri in cfg.prefixes_dict.items():
            self.prefix_to_uri[prefix] = uri

    def model_for_type_uri(self, type_uri: str) -> type[BaseModel] | None:
        return self.type_uri_to_class.get(type_uri) or model_class_for_type_uri(
            type_uri
        )

    def model_for_subject(
        self,
        graph: Graph,
        subject: Node,
        *,
        use_subclass: bool = True,
    ) -> type[BaseModel]:
        return resolve_model_class_with_rdfs(graph, subject, use_subclass=use_subclass)

    def bind_vocab(self, graph: Graph) -> None:
        """Bind all registered prefixes on ``graph``."""
        bind_namespaces(graph, dict(self.prefix_to_uri))

    @classmethod
    def from_registered(cls) -> VocabularyRegistry:
        """Build a registry snapshot from process-wide registrations."""
        reg = cls()
        for model_cls in iter_registered_model_classes():
            reg.register(model_cls)
        return reg


__all__ = ["VocabularyRegistry"]
