"""TripleModel — Pydantic models backed by RDF graphs via rdflib.

Install: ``pip install triplemodel``
"""

from triplemodel.config import (
    RDF,
    RDFS,
    RDF_TYPE,
    XSD,
    EmbedMode,
    GraphMode,
    RdfConfig,
    freeze_prefixes,
    id_from_subject_uri,
    subject_base,
)
from triplemodel.fields import IriId, Predicate, rdf_field
from triplemodel.io import (
    OnDuplicate,
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
    models_to_graph,
    sync_to_graph,
)
from triplemodel.io.ops import graph_set, graph_value, merge_graphs, objects_for_field
from triplemodel.model import TripleModel
from triplemodel.namespaces import bind_namespaces, expand_curie
from triplemodel.protocols import RdfResource, register_rdf_resource
from triplemodel.terms import LiteralRegistry, default_registry, register_literal_type

__version__ = "0.2.0"

__all__ = [
    "EmbedMode",
    "GraphMode",
    "IriId",
    "LiteralRegistry",
    "OnDuplicate",
    "Predicate",
    "RDF",
    "RDFS",
    "RDF_TYPE",
    "XSD",
    "RdfConfig",
    "RdfResource",
    "TripleModel",
    "bind_namespaces",
    "default_registry",
    "expand_curie",
    "freeze_prefixes",
    "graph_set",
    "graph_to_model",
    "graph_to_models",
    "graph_value",
    "id_from_subject_uri",
    "merge_graphs",
    "model_to_graph",
    "model_to_triples",
    "models_to_graph",
    "objects_for_field",
    "rdf_field",
    "register_literal_type",
    "register_rdf_resource",
    "subject_base",
    "sync_to_graph",
    "__version__",
]
