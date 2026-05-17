"""RDFModel — Pydantic models backed by RDF graphs via rdflib.

Install: ``pip install rdfmodel``
"""

from rdfmodel._config import (
    RDF,
    RDFS,
    RDF_TYPE,
    XSD,
    RdfConfig,
    id_from_subject_uri,
    subject_base,
)
from rdfmodel._fields import Predicate, rdf_field
from rdfmodel._graph import (
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
    models_to_graph,
)
from rdfmodel.model import RdfModel

__version__ = "0.1.0"

__all__ = [
    "RDF",
    "RDFS",
    "RDF_TYPE",
    "XSD",
    "Predicate",
    "RdfConfig",
    "RdfModel",
    "graph_to_model",
    "graph_to_models",
    "id_from_subject_uri",
    "model_to_graph",
    "model_to_triples",
    "models_to_graph",
    "rdf_field",
    "subject_base",
    "__version__",
]
