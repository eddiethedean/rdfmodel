"""TripleModel — Pydantic models backed by RDF graphs via rdflib.

Install: ``pip install triplemodel``
"""

from triplemodel._config import (
    RDF,
    RDFS,
    RDF_TYPE,
    XSD,
    EmbedMode,
    GraphMode,
    RdfConfig,
    id_from_subject_uri,
    subject_base,
)
from triplemodel._fields import IriId, Predicate, rdf_field
from triplemodel._graph import (
    OnDuplicate,
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
    models_to_graph,
)
from triplemodel._graph_ops import (
    graph_set,
    graph_value,
    merge_graphs,
    objects_for_field,
)
from triplemodel._namespaces import bind_namespaces, expand_curie
from triplemodel._registry import register_literal_type
from triplemodel._sync import sync_to_graph
from triplemodel.model import TripleModel

__version__ = "0.2.0"

__all__ = [
    "EmbedMode",
    "GraphMode",
    "IriId",
    "OnDuplicate",
    "RDF",
    "RDFS",
    "RDF_TYPE",
    "XSD",
    "Predicate",
    "RdfConfig",
    "TripleModel",
    "bind_namespaces",
    "expand_curie",
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
    "subject_base",
    "sync_to_graph",
    "__version__",
]
