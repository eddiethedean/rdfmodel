"""Tests for batch reference hydration."""

from __future__ import annotations


from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

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
    fr = NamedNode(f"{COUNTRY}fr")
    paris = NamedNode(f"{CITY}paris")
    london = NamedNode(f"{CITY}london")
    for uri, typ, label in (
        (fr, f"{COUNTRY}Country", "France"),
        (paris, f"{CITY}City", "Paris"),
        (london, f"{CITY}City", "London"),
    ):
        g.add((uri, NamedNode(RDF_TYPE), NamedNode(typ)))
        g.add((uri, NamedNode(f"{EX}label"), Literal(label)))
    g.add((paris, NamedNode(f"{EX}inCountry"), fr))
    g.add((london, NamedNode(f"{EX}inCountry"), fr))
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
