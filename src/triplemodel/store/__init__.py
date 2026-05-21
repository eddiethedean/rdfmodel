"""pyoxigraph-backed RDF store."""

from pyoxigraph import BlankNode, Literal, NamedNode, Quad, Store as OxigraphStore

from triplemodel.store.dataset import RdfDataset
from triplemodel.store.graph import RdfGraph
from triplemodel.store.namespaces import RDF, RDFS, RDF_FIRST, RDF_REST, RDF_NIL, XSD
from triplemodel.store.terms import (
    RdfTerm,
    iri_ref,
    is_blank,
    is_literal,
    is_named,
    term_str,
)

# Public alias: integrators use ``Store`` (wraps pyoxigraph with graph helpers).
Store = RdfGraph

__all__ = [
    "BlankNode",
    "Literal",
    "NamedNode",
    "OxigraphStore",
    "Quad",
    "RDF",
    "RDF_FIRST",
    "RDF_NIL",
    "RDF_REST",
    "RDFS",
    "RdfDataset",
    "RdfGraph",
    "RdfTerm",
    "Store",
    "XSD",
    "iri_ref",
    "is_blank",
    "is_literal",
    "is_named",
    "term_str",
]
