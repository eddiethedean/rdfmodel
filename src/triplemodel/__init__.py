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
from triplemodel.fields import IriId, InverseOf, Predicate, rdf_field
from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.terms.lang import Lang, LangString
from triplemodel.terms.opaque import OpaqueLiteral
from triplemodel.io import (
    OnDuplicate,
    all_from_graph_dispatch,
    dump_graph,
    dump_model,
    graph_to_model,
    graph_to_model_dispatch,
    graph_to_models,
    infer_format,
    load_models,
    model_to_graph,
    model_to_triples,
    models_to_graph,
    parse_into_graph,
    parse_url_into_graph,
    sync_to_graph,
)
from triplemodel.io.ops import graph_set, graph_value, merge_graphs, objects_for_field
from triplemodel.model import TripleModel
from triplemodel.namespaces import bind_namespaces, expand_curie
from triplemodel.protocols import (
    RdfResource,
    register_rdf_resource,
    resolve_model_class,
)
from triplemodel.validation import validate_graph
from triplemodel.terms import LiteralRegistry, default_registry, register_literal_type

__version__ = "0.4.0"

__all__ = [
    "EmbedMode",
    "GraphMode",
    "IriId",
    "InverseOf",
    "Lang",
    "all_from_graph_dispatch",
    "dump_graph",
    "dump_model",
    "graph_to_model_dispatch",
    "infer_format",
    "load_models",
    "parse_into_graph",
    "parse_url_into_graph",
    "resolve_model_class",
    "validate_graph",
    "LangString",
    "LiteralRegistry",
    "OpaqueLiteral",
    "OnDuplicate",
    "Predicate",
    "ResourceRef",
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
