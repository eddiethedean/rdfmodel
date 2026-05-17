"""RDF term conversion and literal registry."""

from triplemodel.terms.collection import read_rdf_list, remove_rdf_list, write_rdf_list
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.lang import Lang, LangString
from triplemodel.terms.opaque import OpaqueLiteral
from triplemodel.terms.iri import looks_like_iri, subject_node, subject_ref
from triplemodel.terms.registry import (
    LiteralRegistry,
    converter_for_type,
    default_registry,
    literal_to_python,
    python_to_literal,
    register_literal_type,
)

__all__ = [
    "Lang",
    "LangString",
    "OpaqueLiteral",
    "LiteralRegistry",
    "read_rdf_list",
    "remove_rdf_list",
    "write_rdf_list",
    "converter_for_type",
    "default_registry",
    "literal_to_python",
    "looks_like_iri",
    "python_to_literal",
    "python_to_term",
    "register_literal_type",
    "subject_node",
    "subject_ref",
    "term_to_python",
]
