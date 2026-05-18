"""RDF configuration and vocabulary constants."""

from triplemodel.config.constants import RDF, RDFS, RDF_TYPE, XSD
from triplemodel.config.rdf_config import (
    EmbedMode,
    GraphMode,
    RdfConfig,
    SubjectUriInstance,
    effective_graph_mode,
    freeze_prefixes,
    get_graph_context,
    get_rdf_config,
    id_from_subject_uri,
    resolve_graph_iri,
    subject_base,
)

__all__ = [
    "EmbedMode",
    "GraphMode",
    "RDF",
    "RDFS",
    "RDF_TYPE",
    "RdfConfig",
    "SubjectUriInstance",
    "XSD",
    "effective_graph_mode",
    "freeze_prefixes",
    "get_graph_context",
    "get_rdf_config",
    "id_from_subject_uri",
    "resolve_graph_iri",
    "subject_base",
]
