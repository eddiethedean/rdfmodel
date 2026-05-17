"""IRI detection and RDF subject term helpers."""

from __future__ import annotations

import re

from rdflib import BNode, URIRef
from rdflib.term import Node

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


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


def subject_node(subj: str) -> Node:
    if looks_like_iri(subj):
        return URIRef(subj)
    return BNode(subj)


def subject_ref(uri: str) -> URIRef:
    return URIRef(uri)
