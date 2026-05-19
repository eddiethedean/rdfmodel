"""RDFS helpers: subclass dispatch, transitive graph walks."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node, term_str

from triplemodel.config import RDFS, RDF_TYPE, get_rdf_config
from triplemodel.protocols import (
    _mro_depth,
    iter_registered_type_uris,
    model_class_for_type_uri,
)

RDFS_SUBCLASS = NamedNode(f"{RDFS}subClassOf")


def subject_type_closure(graph: Graph, subject: Node) -> frozenset[str]:
    """Return ``rdf:type`` IRIs for ``subject`` plus ``rdfs:subClassOf`` ancestors."""
    closure: set[str] = set()
    for direct in graph.objects(subject, NamedNode(RDF_TYPE)):
        closure.add(term_str(direct))
        for ancestor in graph.transitive_objects(direct, RDFS_SUBCLASS):
            closure.add(term_str(ancestor))
    return frozenset(closure)


def subclass_uris(graph: Graph, type_uri: str) -> frozenset[str]:
    """Return ``type_uri`` and all superclasses via ``rdfs:subClassOf``."""
    term = NamedNode(type_uri)
    return frozenset(
        {
            type_uri,
            *(term_str(o) for o in graph.transitive_objects(term, RDFS_SUBCLASS)),
        }
    )


def transitive_objects(
    graph: Graph,
    subject: str | Node,
    predicate: str,
) -> list[str]:
    """Return object IRIs reachable from ``subject`` along ``predicate`` (transitive)."""
    subj = subject if isinstance(subject, Node) else NamedNode(subject)
    pred = NamedNode(predicate)
    return [term_str(o) for o in graph.transitive_objects(subj, pred)]


def transitive_subjects(
    graph: Graph,
    predicate: str,
    obj: str | Node,
) -> list[str]:
    """Return subject IRIs that reach ``obj`` along ``predicate`` (transitive)."""
    object_node = obj if isinstance(obj, Node) else NamedNode(obj)
    pred = NamedNode(predicate)
    return [term_str(s) for s in graph.transitive_subjects(pred, object_node)]


def _is_more_specific(graph: Graph, sub_uri: str, super_uri: str) -> bool:
    """True when ``sub_uri`` is a subclass of ``super_uri`` in ``graph``."""
    return NamedNode(super_uri) in graph.transitive_objects(
        NamedNode(sub_uri), RDFS_SUBCLASS
    )


def _pick_most_specific(
    graph: Graph,
    candidates: list[type[BaseModel]],
) -> type[BaseModel]:
    if len(candidates) == 1:
        return candidates[0]
    typed: list[tuple[str, type[BaseModel]]] = []
    for cls in candidates:
        cfg = get_rdf_config(cls)
        if cfg.type_uri:
            typed.append((cfg.type_uri, cls))
    if not typed:
        return cast(type[BaseModel], max(candidates, key=_mro_depth))
    best: list[type[BaseModel]] = []
    for uri_a, cls_a in typed:
        dominated = False
        for uri_b, cls_b in typed:
            if uri_a == uri_b:
                continue
            if _is_more_specific(graph, uri_b, uri_a):
                dominated = True
                break
        if not dominated:
            best.append(cls_a)
    if len(best) == 1:
        return best[0]
    return cast(type[BaseModel], max(best or candidates, key=_mro_depth))


def resolve_model_class_with_rdfs(
    graph: Graph,
    subject: Node,
    *,
    use_subclass: bool = True,
) -> type[BaseModel]:
    """Pick the most specific registered class for ``subject``'s types."""
    type_nodes = list(graph.objects(subject, NamedNode(RDF_TYPE)))
    if not type_nodes:
        raise ValueError(
            f"No registered TripleModel class for subject {subject!r} (rdf:types: [])."
        )
    if not use_subclass:
        candidates: list[type[BaseModel]] = []
        for t in type_nodes:
            cls = model_class_for_type_uri(term_str(t))
            if cls is not None:
                candidates.append(cls)
        if not candidates:
            raise ValueError(
                f"No registered TripleModel class for subject {subject!r} "
                f"(rdf:types: {[term_str(t) for t in type_nodes]})."
            )
        return _pick_most_specific(graph, candidates)

    closure = subject_type_closure(graph, subject)
    candidates = []
    for type_uri in iter_registered_type_uris():
        if type_uri in closure:
            cls = model_class_for_type_uri(type_uri)
            if cls is not None:
                candidates.append(cls)
    if not candidates:
        raise ValueError(
            f"No registered TripleModel class for subject {subject!r} "
            f"(type closure: {sorted(closure)})."
        )
    return _pick_most_specific(graph, candidates)


__all__ = [
    "resolve_model_class_with_rdfs",
    "subject_type_closure",
    "subclass_uris",
    "transitive_objects",
    "transitive_subjects",
]
