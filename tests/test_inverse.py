"""Inverse predicate import."""

from __future__ import annotations

from rdflib import Graph, URIRef

from triplemodel import TripleModel, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.fields import owned_predicates

EX = "http://example.org/"


class Employee(TripleModel):
    class Rdf:
        namespace = f"{EX}emp/"
        type_uri = f"{EX}Employee"
        id_field = "slug"

    slug: str
    manager: str | None = rdf_field(
        f"{EX}hasManager",
        inverse=f"{EX}manages",
        default=None,
    )


def test_import_via_inverse_predicate() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    bob_model = Employee.from_graph(g, str(bob))
    assert bob_model.slug == "bob"

    alice_model = Employee.from_graph(g, str(alice))
    assert alice_model.manager == str(bob)


def test_owned_predicates_includes_inverse() -> None:
    preds = owned_predicates(Employee)
    assert f"{EX}manages" in preds
