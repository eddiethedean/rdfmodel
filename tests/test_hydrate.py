"""Tests for batch reference hydration."""

from __future__ import annotations


from rdflib import Graph, Literal, URIRef

from triplemodel import TripleModel, hydrate_refs, model_join, rdf_field, ref_field
from triplemodel.config import RDF_TYPE

EX = "http://example.org/"
COUNTRY = f"{EX}country/"
CITY = f"{EX}city/"


class Country(TripleModel):
    class Rdf:
        namespace = COUNTRY
        type_uri = f"{COUNTRY}Country"
        id_field = "code"

    code: str
    label: str = rdf_field(f"{EX}label")


class City(TripleModel):
    class Rdf:
        namespace = CITY
        type_uri = f"{CITY}City"
        id_field = "code"

    code: str
    label: str = rdf_field(f"{EX}label")
    country: Country = ref_field(f"{EX}inCountry", model=Country)


def _shared_country_graph() -> Graph:
    g = Graph()
    fr = URIRef(f"{COUNTRY}fr")
    paris = URIRef(f"{CITY}paris")
    london = URIRef(f"{CITY}london")
    for uri, typ, label in (
        (fr, f"{COUNTRY}Country", "France"),
        (paris, f"{CITY}City", "Paris"),
        (london, f"{CITY}City", "London"),
    ):
        g.add((uri, URIRef(RDF_TYPE), URIRef(typ)))
        g.add((uri, URIRef(f"{EX}label"), Literal(label)))
    g.add((paris, URIRef(f"{EX}inCountry"), fr))
    g.add((london, URIRef(f"{EX}inCountry"), fr))
    return g


def test_hydrate_refs_shared_country_identity():
    g = _shared_country_graph()
    cities = [
        City(code="paris", label="Paris", country=Country(code="fr", label="X")),
        City(code="london", label="London", country=Country(code="fr", label="Y")),
    ]
    hydrated = hydrate_refs(cities, g, "country")
    assert hydrated[0].country.label == "France"
    assert hydrated[0].country is hydrated[1].country


def test_model_join():
    g = _shared_country_graph()
    cities = City.all_from_graph(g)
    joined = model_join(cities, g, {"country": Country})
    assert joined[0].country.label == "France"
