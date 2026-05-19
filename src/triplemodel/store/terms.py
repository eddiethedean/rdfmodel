"""Term helpers for pyoxigraph."""

from __future__ import annotations

from typing import TypeAlias, cast

from pyoxigraph import BlankNode, Literal, NamedNode, Triple

RdfTerm = NamedNode | BlankNode | Literal
OxTerm: TypeAlias = NamedNode | BlankNode | Literal | Triple
QuadSubject: TypeAlias = NamedNode | BlankNode | Triple
QuadPredicate: TypeAlias = NamedNode
QuadObject: TypeAlias = NamedNode | BlankNode | Literal | Triple


def iri_ref(value: str) -> NamedNode:
    """Build a named node from an IRI string."""
    return NamedNode(value)


def _coerce_term(value: str | OxTerm) -> RdfTerm:
    if isinstance(value, (NamedNode, BlankNode, Literal)):
        return value
    if isinstance(value, Triple):
        raise TypeError("Triple term cannot be coerced to a literal RDF term.")
    return iri_ref(value)


def as_quad_subject(value: str | OxTerm) -> QuadSubject:
    """Coerce a subject term for :class:`~pyoxigraph.Quad` construction."""
    if isinstance(value, Triple):
        return value
    return cast(QuadSubject, _coerce_term(value))


def as_quad_predicate(value: str | OxTerm) -> QuadPredicate:
    """Coerce a predicate term for :class:`~pyoxigraph.Quad` construction."""
    return cast(QuadPredicate, _coerce_term(value))


def as_quad_object(value: str | OxTerm) -> QuadObject:
    """Coerce an object term for :class:`~pyoxigraph.Quad` construction."""
    if isinstance(value, Triple):
        return value
    return cast(QuadObject, _coerce_term(value))


def pattern_subject(value: str | OxTerm | None) -> QuadSubject | None:
    if value is None:
        return None
    return as_quad_subject(value)


def pattern_predicate(value: str | OxTerm | None) -> QuadPredicate | None:
    if value is None:
        return None
    return as_quad_predicate(value)


def pattern_object(value: str | OxTerm | None) -> QuadObject | None:
    if value is None:
        return None
    return as_quad_object(value)


def term_str(term: OxTerm) -> str:
    """String form of a term (IRI, blank node id, literal value, or RDF-star triple)."""
    if isinstance(term, Triple):
        return str(term)
    if isinstance(term, NamedNode):
        return str(term.value)
    if isinstance(term, BlankNode):
        return str(term)
    return str(term.value)


def term_key(term: OxTerm | QuadSubject) -> str:
    """Stable string key for deduplication (includes RDF-star triple terms)."""
    return term_str(term)


def is_named(term: RdfTerm) -> bool:
    return isinstance(term, NamedNode)


def is_blank(term: RdfTerm) -> bool:
    return isinstance(term, BlankNode)


def is_literal(term: RdfTerm) -> bool:
    return isinstance(term, Literal)
