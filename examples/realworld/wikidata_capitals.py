#!/usr/bin/env python3
"""Wikidata capital cities: typed models over CC0 geographic facts.

Problem: knowledge-graph pipelines (Wikidata, DBpedia) ship billions of triples;
applications need typed slices (population, country) without hand-rolling parsers.

Data: examples/realworld/data/wikidata_capitals.ttl
Source: Wikidata Q90, Q84, Q64 (+ country labels) — CC0 1.0
"""

from __future__ import annotations

from triplemodel import TripleModel, rdf_field
from triplemodel.fields import IriId
from triplemodel.io.files import parse_into_graph

from _paths import data_file

WD = "http://www.wikidata.org/entity/"
WIKIDATA_PREFIXES = {
    "wd": WD,
    "wdt": "http://www.wikidata.org/prop/direct/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


class WikidataItem(TripleModel):
    """Minimal Wikidata item with English label (e.g. country)."""

    class Rdf:
        namespace = WD
        type_uri = ""
        id_field = "qid"
        prefixes = WIKIDATA_PREFIXES

    qid: str = IriId()
    label_en: str = rdf_field("rdfs:label")


class CapitalCity(TripleModel):
    class Rdf:
        namespace = WD
        type_uri = ""
        id_field = "qid"
        prefixes = WIKIDATA_PREFIXES

    qid: str = IriId()
    label_en: str = rdf_field("rdfs:label")
    population: int = rdf_field("wdt:P1082")
    country: str = rdf_field("wdt:P17")


CITY_QIDS = ("Q90", "Q84", "Q64")
COUNTRY_QIDS = ("Q142", "Q145", "Q183")


def main() -> None:
    path = data_file("wikidata_capitals.ttl")
    graph = parse_into_graph(
        source=path,
        bind_prefixes=WIKIDATA_PREFIXES,
    )
    cities = [
        CapitalCity.from_graph(graph, f"{WD}{qid}", validate_type=False)
        for qid in CITY_QIDS
    ]
    countries = {
        f"{WD}{qid}": WikidataItem.from_graph(graph, f"{WD}{qid}", validate_type=False)
        for qid in COUNTRY_QIDS
    }

    print("European capitals (Wikidata excerpt):")
    for city in sorted(cities, key=lambda c: c.population, reverse=True):
        country_name = countries[city.country].label_en
        country_qid = city.country.rsplit("/", 1)[-1]
        print(
            f"  {city.label_en}: population={city.population:,} "
            f"country={country_name} ({country_qid})"
        )

    paris = next(c for c in cities if c.qid.endswith("Q90"))
    assert paris.label_en == "Paris"
    assert paris.population == 2_103_778
    g = paris.to_graph()
    restored = CapitalCity.from_graph(g, paris.subject_uri(), validate_type=False)
    assert restored.population == paris.population
    print("Paris round-trip OK")


if __name__ == "__main__":
    main()
