#!/usr/bin/env python3
"""Wikidata capital cities: typed models over CC0 geographic facts.

Problem: knowledge-graph pipelines (Wikidata, DBpedia) ship billions of triples;
applications need typed slices (population, country) without hand-rolling parsers.

Data: examples/realworld/data/wikidata_capitals.ttl
Source: Wikidata Q90, Q84 (+ country labels) — CC0 1.0
"""

from __future__ import annotations

from typing import Annotated

from triplemodel import TripleModel, load_graph, rdf_field, ref_field
from triplemodel.fields import IriId

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

    qid: Annotated[str, IriId()]
    label_en: str | None = rdf_field("rdfs:label", default=None)


class CapitalCity(TripleModel):
    class Rdf:
        namespace = WD
        type_uri = ""
        instance_of = "wdt:P31"
        instance_type_uri = f"{WD}Q174844"
        id_field = "qid"
        prefixes = WIKIDATA_PREFIXES

    qid: Annotated[str, IriId()]
    label_en: str | None = rdf_field("rdfs:label", default=None)
    population: int = rdf_field("wdt:P1082")
    country: WikidataItem = ref_field("wdt:P17", model=WikidataItem)


def main() -> None:
    path = data_file("wikidata_capitals.ttl")
    graph = load_graph(source=path, bind_prefixes=WIKIDATA_PREFIXES)
    cities = CapitalCity.all_from_graph(graph, validate_type=False)

    assert CapitalCity.ask_sparql(
        graph,
        "ASK { wd:Q90 wdt:P1082 ?pop . FILTER(?pop > 2000000) }",
    )
    paris_rows = CapitalCity.select_from_sparql(
        graph,
        """
        SELECT ?city WHERE {
          ?city wdt:P31 wd:Q174844 .
          FILTER(?city = wd:Q90)
        }
        """,
        subject_var="city",
        hydrate=True,
    )
    assert len(paris_rows) == 1 and paris_rows[0].qid.endswith("Q90")

    print("European capitals (Wikidata excerpt):")
    for city in sorted(cities, key=lambda c: c.population, reverse=True):
        country_qid = city.country.qid
        print(
            f"  {city.label_en}: population={city.population:,} "
            f"country={city.country.label_en} ({country_qid})"
        )

    paris = next(c for c in cities if c.qid.endswith("Q90"))
    assert paris.label_en == "Paris"
    assert paris.population == 2_103_778
    assert paris.country.label_en == "France"
    g = paris.to_graph()
    restored = CapitalCity.from_graph(g, paris.subject_uri(), validate_type=False)
    assert restored.population == paris.population
    assert restored.country.qid.endswith("Q142")
    print("Paris round-trip OK (country link preserved; labels live in source graph)")


if __name__ == "__main__":
    main()
