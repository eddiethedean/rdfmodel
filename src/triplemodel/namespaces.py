"""Namespace prefixes, CURIE expansion, and graph binding."""

from __future__ import annotations

import re
from typing import Literal

from rdflib import Graph, Namespace

from triplemodel.terms.iri import looks_like_iri

BindStrategy = Literal["core", "rdflib", "none"]

_CURIE_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):([^:].*)$")


def expand_curie(curie: str, prefixes: dict[str, str]) -> str:
    """Expand ``prefix:local`` to a full IRI; pass through absolute IRIs."""
    if looks_like_iri(curie):
        return curie
    match = _CURIE_RE.match(curie)
    if not match:
        return curie
    prefix, local = match.group(1), match.group(2)
    if prefix not in prefixes:
        raise ValueError(f"Unknown prefix {prefix!r} in CURIE {curie!r}.")
    base = prefixes[prefix]
    if base.endswith(("#", "/")):
        return f"{base}{local}"
    return f"{base}#{local}"


def resolve_predicate(predicate: str, prefixes: dict[str, str]) -> str:
    """Expand a predicate CURIE using ``prefixes`` when applicable."""
    if looks_like_iri(predicate):
        return predicate
    if ":" not in predicate:
        return predicate
    return expand_curie(predicate, prefixes)


def bind_namespaces(
    graph: Graph,
    prefixes: dict[str, str],
    *,
    strategy: BindStrategy = "core",
) -> None:
    """Bind ``prefixes`` on ``graph`` for serialization and SPARQL."""
    if strategy == "none":
        return
    for prefix, uri in prefixes.items():
        graph.bind(prefix, Namespace(uri), override=True, replace=True)
    if strategy == "rdflib":
        bind_all = getattr(graph, "bind_namespaces", None)
        if callable(bind_all):
            bind_all()
