"""Experimental OWL/RDFS → TripleModel stub codegen."""

from triplemodel.codegen.emit import generate_models_from_graph
from triplemodel.codegen.parse import ontology_graph

__all__ = ["generate_models_from_graph", "ontology_graph"]
