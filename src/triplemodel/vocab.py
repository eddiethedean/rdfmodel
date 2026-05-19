"""Bundled RDF vocabulary namespace IRIs (pyoxigraph era)."""

from __future__ import annotations


class _VocabNS:
    """Namespace helper supporting ``str(FOAF)`` and ``f\"{FOAF}name\"``."""

    __slots__ = ("_uri",)

    def __init__(self, uri: str) -> None:
        base = uri if uri.endswith(("/", "#")) else uri + "/"
        self._uri = base

    def __str__(self) -> str:
        return self._uri

    def __getitem__(self, name: str) -> str:
        return f"{self._uri}{name}"

    def __getattr__(self, name: str) -> str:
        if name.startswith("_"):
            raise AttributeError(name)
        return f"{self._uri}{name}"


DC = _VocabNS("http://purl.org/dc/elements/1.1/")
DCTERMS = _VocabNS("http://purl.org/dc/terms/")
FOAF = _VocabNS("http://xmlns.com/foaf/0.1/")
OWL = _VocabNS("http://www.w3.org/2002/07/owl#")
RDF = _VocabNS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = _VocabNS("http://www.w3.org/2000/01/rdf-schema#")
SKOS = _VocabNS("http://www.w3.org/2004/02/skos/core#")
XSD = _VocabNS("http://www.w3.org/2001/XMLSchema#")

__all__ = [
    "DC",
    "DCTERMS",
    "FOAF",
    "OWL",
    "RDF",
    "RDFS",
    "SKOS",
    "XSD",
]
