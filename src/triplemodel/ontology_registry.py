"""Ontology hints: subclass closure and inverse predicate pairs from TTL or static registration."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import term_str

from triplemodel.config.constants import OWL, RDFS
from triplemodel.config import get_rdf_config
from triplemodel.fields.metadata import (
    inverse_for_field,
    predicate_for_field,
    predicate_from_annotation,
)
from triplemodel.metadata.cardinality import field_annotation
from triplemodel.namespaces import resolve_predicate

RDFS_SUBCLASS = NamedNode(f"{RDFS}subClassOf")
OWL_INVERSE = NamedNode(f"{OWL}inverseOf")


@dataclass
class OntologyRegistry:
    """Subclass and ``owl:inverseOf`` hints from an ontology graph and/or static registration.

    Use :meth:`subtypes_of` for **descendant** type IRIs (subclasses). For **ancestor**
    types (superclasses of a given class), use :func:`~triplemodel.subclass_uris` on a
    graph that contains ``rdfs:subClassOf`` axioms.
    """

    _graph: Graph | None = None
    _parent_to_children: dict[str, set[str]] = field(default_factory=dict)
    _registered_inverse_forward: dict[str, str] = field(default_factory=dict)
    _registered_inverse_reverse: dict[str, str] = field(default_factory=dict)
    _graph_inverse_forward: dict[str, str] = field(default_factory=dict)
    _graph_inverse_reverse: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_graph(cls, graph: Graph) -> OntologyRegistry:
        """Build a registry backed by ``graph`` (typically parsed OWL/RDFS Turtle)."""
        reg = cls()
        reg.load_graph(graph)
        return reg

    @classmethod
    def from_ttl(
        cls,
        path: str | Path,
        *,
        format: str | None = None,
        base_iri: str | None = None,
    ) -> OntologyRegistry:
        """Parse a Turtle (or other) ontology file into a new registry."""
        graph = Graph()
        graph.parse(
            str(path),
            format=format or "turtle",
            base_iri=base_iri,
        )
        return cls.from_graph(graph)

    def load_graph(self, graph: Graph) -> None:
        """Use ``graph`` for :meth:`subtypes_of` and :meth:`inverse_of` queries."""
        self._graph = graph
        self._graph_inverse_forward.clear()
        self._graph_inverse_reverse.clear()
        self._index_inverse_from_graph(graph)

    def register_subclasses(
        self,
        base_type_uri: str,
        subtype_uris: Iterable[str],
    ) -> None:
        """Register direct ``rdfs:subClassOf`` links without an ontology file."""
        children = self._parent_to_children.setdefault(base_type_uri, set())
        for sub in subtype_uris:
            children.add(sub)

    def register_inverse(self, forward_predicate: str, inverse_predicate: str) -> None:
        """Register an ``owl:inverseOf`` pair (both directions are queryable)."""
        self._registered_inverse_forward[forward_predicate] = inverse_predicate
        self._registered_inverse_reverse[inverse_predicate] = forward_predicate

    def subtypes_of(self, type_uri: str) -> frozenset[str]:
        """Return ``type_uri`` and all registered or inferred **subclass** IRIs."""
        found: set[str] = {type_uri}
        if self._graph is not None:
            term = NamedNode(type_uri)
            for subj in self._graph.transitive_subjects(RDFS_SUBCLASS, term):
                found.add(term_str(subj))
        found.update(self._static_subtype_closure(type_uri))
        return frozenset(found)

    def inverse_of(self, predicate_uri: str) -> str | None:
        """Return the inverse property IRI for ``predicate_uri``, if known."""
        if predicate_uri in self._registered_inverse_forward:
            return self._registered_inverse_forward[predicate_uri]
        if predicate_uri in self._registered_inverse_reverse:
            return self._registered_inverse_reverse[predicate_uri]
        if predicate_uri in self._graph_inverse_forward:
            return self._graph_inverse_forward[predicate_uri]
        if predicate_uri in self._graph_inverse_reverse:
            return self._graph_inverse_reverse[predicate_uri]
        if self._graph is None:
            return None
        pred = NamedNode(predicate_uri)
        for obj in self._graph.objects(pred, OWL_INVERSE):
            return term_str(obj)
        for subj in self._graph.subjects(OWL_INVERSE, pred):
            return term_str(subj)
        return None

    def _static_subtype_closure(self, type_uri: str) -> set[str]:
        """All descendants from :meth:`register_subclasses` edges."""
        result: set[str] = set()
        queue: deque[str] = deque(self._parent_to_children.get(type_uri, ()))
        while queue:
            child = queue.popleft()
            if child in result:
                continue
            result.add(child)
            queue.extend(self._parent_to_children.get(child, ()))
        return result

    def _index_inverse_from_graph(self, graph: Graph) -> None:
        for subj in graph.subjects(OWL_INVERSE, None):
            if not isinstance(subj, NamedNode):
                continue
            for obj in graph.objects(subj, OWL_INVERSE):
                if isinstance(obj, NamedNode):
                    forward = term_str(subj)
                    inverse = term_str(obj)
                    self._graph_inverse_forward[forward] = inverse
                    self._graph_inverse_reverse[inverse] = forward


def apply_hints_to_model(
    model_cls: type[BaseModel],
    registry: OntologyRegistry,
    *,
    mutate: bool = False,
    overwrite: bool = False,
) -> dict[str, str]:
    """Suggest or apply ``inverse=`` metadata from :meth:`OntologyRegistry.inverse_of`.

    Returns ``{field_name: inverse_predicate_uri}`` for each mapped field that received
    a hint. When ``mutate`` is True, updates ``json_schema_extra`` on the class and calls
    ``model_rebuild()`` so :func:`~triplemodel.fields.metadata.inverse_for_field` sees the
    inverse IRI. Skips fields that already declare an inverse unless ``overwrite`` is True.
    """
    cfg = get_rdf_config(model_cls)
    prefixes = cfg.prefixes_dict
    applied: dict[str, str] = {}
    new_fields: dict[str, FieldInfo] = dict(model_cls.model_fields)
    changed = False

    for name, field_info in model_cls.model_fields.items():
        raw = predicate_for_field(field_info) or predicate_from_annotation(
            field_annotation(field_info)
        )
        if raw is None:
            continue
        if inverse_for_field(field_info) is not None and not overwrite:
            continue
        try:
            forward = resolve_predicate(raw, prefixes)
        except ValueError:
            continue
        inv = registry.inverse_of(forward)
        if inv is None:
            continue
        applied[name] = inv
        if mutate:
            extra = field_info.json_schema_extra
            merged: dict[str, object] = (
                dict(cast(Mapping[str, object], extra))
                if isinstance(extra, dict)
                else {}
            )
            merged["rdf_inverse"] = inv
            new_fields[name] = FieldInfo.merge_field_infos(  # ty: ignore[deprecated]
                field_info,
                json_schema_extra=merged,
            )
            changed = True

    if mutate and changed:
        cast(Any, model_cls).model_fields = new_fields
        model_cls.model_rebuild(force=True)
    return applied


__all__ = ["OntologyRegistry", "apply_hints_to_model"]
