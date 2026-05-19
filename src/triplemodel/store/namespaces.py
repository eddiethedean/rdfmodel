"""RDF / XSD vocabulary IRIs as pyoxigraph named nodes."""

from __future__ import annotations

from pyoxigraph import NamedNode

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD_BASE = "http://www.w3.org/2001/XMLSchema#"

RDF_FIRST = f"{RDF}first"
RDF_REST = f"{RDF}rest"
RDF_NIL = f"{RDF}nil"


class _XSDNamespace:
    """XSD datatype IRIs (``NamedNode``), matching former rdflib ``XSD`` usage."""

    string = NamedNode(f"{XSD_BASE}string")
    boolean = NamedNode(f"{XSD_BASE}boolean")
    integer = NamedNode(f"{XSD_BASE}integer")
    double = NamedNode(f"{XSD_BASE}double")
    decimal = NamedNode(f"{XSD_BASE}decimal")
    date = NamedNode(f"{XSD_BASE}date")
    dateTime = NamedNode(f"{XSD_BASE}dateTime")
    gYear = NamedNode(f"{XSD_BASE}gYear")
    gMonth = NamedNode(f"{XSD_BASE}gMonth")
    gMonthDay = NamedNode(f"{XSD_BASE}gMonthDay")

    def __getitem__(self, key: str) -> NamedNode:
        return NamedNode(f"{XSD_BASE}{key}")


XSD = _XSDNamespace()
