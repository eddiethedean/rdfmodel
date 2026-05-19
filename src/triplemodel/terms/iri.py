"""IRI detection and RDF subject term helpers."""

from __future__ import annotations

import re

from pyoxigraph import BlankNode, NamedNode

from triplemodel.store.terms import RdfTerm

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def normalize_iri(value: str) -> str:
    """Strip N-Triples angle brackets from an IRI string when present."""
    s = value.strip()
    if len(s) >= 2 and s[0] == "<" and s[-1] == ">":
        return s[1:-1]
    return s


def looks_like_iri(value: str) -> bool:
    """True when ``value`` is an absolute IRI (not a CURIE ``prefix:local``)."""
    if not _SCHEME_RE.match(value):
        return False
    if "://" in value or value.startswith("urn:"):
        return True
    scheme, _, rest = value.partition(":")
    if scheme in ("mailto", "file") and rest:
        return True
    return False


def subject_node(subj: str) -> RdfTerm:
    if looks_like_iri(subj):
        return NamedNode(subj)
    return BlankNode()


def subject_ref(uri: str) -> NamedNode:
    return NamedNode(normalize_iri(uri))
