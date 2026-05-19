"""Concise bounded description (CBD) without rdflib."""

from __future__ import annotations

from pyoxigraph import NamedNode

from triplemodel.store.graph import RdfGraph
from triplemodel.store.terms import RdfTerm, iri_ref, is_named


def cbd_subgraph(
    graph: RdfGraph,
    subject: str | RdfTerm,
    *,
    target_graph: RdfGraph | None = None,
    include_reifications: bool = True,
) -> RdfGraph:
    """Return a new graph with the concise bounded description of ``subject``."""
    _ = include_reifications
    out = target_graph or RdfGraph()
    subj: RdfTerm = subject if not isinstance(subject, str) else iri_ref(subject)
    if not is_named(subj):
        return out
    seen_subjects: set[str] = set()
    queue: list[RdfTerm] = [subj]
    while queue:
        current = queue.pop(0)
        key = str(current.value) if isinstance(current, NamedNode) else str(current)
        if key in seen_subjects:
            continue
        seen_subjects.add(key)
        for s, p, o in graph.triples((current, None, None)):
            out.add((s, p, o))
            if isinstance(o, NamedNode):
                queue.append(o)
    return out
