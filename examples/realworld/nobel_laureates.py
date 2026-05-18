#!/usr/bin/env python3
"""Nobel Prize linked data (1901): load laureates from real vocabulary and names.

Problem: integrate biographical linked open data where resources already have
stable URIs and a published ontology (common in cultural heritage and science).

Data: examples/realworld/data/nobel_laureates_1901.ttl
Source: https://www.nobelprize.org/about/linked-data-examples/
"""

from __future__ import annotations

from triplemodel import TripleModel, rdf_field
from triplemodel.vocab import FOAF

from _paths import data_file

NOBEL = "http://data.nobelprize.org/terms/"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDFS_LABEL = f"{RDFS}label"


class Laureate(TripleModel):
    """Person or organisation receiving a Nobel Prize (nobel:Laureate)."""

    class Rdf:
        namespace = "http://data.nobelprize.org/resource/laureate/"
        type_uri = f"{NOBEL}Laureate"
        id_field = "slug"
        prefixes = {
            "nobel": NOBEL,
            "rdfs": RDFS,
            "foaf": str(FOAF),
        }

    slug: str
    name: str = rdf_field(RDFS_LABEL)
    gender: str | None = rdf_field(f"{FOAF}gender", default=None)


class NobelPrize(TripleModel):
    """Award instance for a category and year (nobel:NobelPrize)."""

    class Rdf:
        namespace = "http://data.nobelprize.org/resource/nobelprize/"
        type_uri = f"{NOBEL}NobelPrize"
        id_field = "slug"
        prefixes = {"nobel": NOBEL, "rdfs": RDFS}

    slug: str
    title: str = rdf_field(RDFS_LABEL)
    year: str = rdf_field(f"{NOBEL}year")


def main() -> None:
    laureates = Laureate.parse_file(data_file("nobel_laureates_1901.ttl"))
    prizes = NobelPrize.parse_file(data_file("nobel_laureates_1901.ttl"))

    print(
        f"Loaded {len(laureates)} laureates and {len(prizes)} prizes from 1901 excerpt"
    )
    for person in sorted(laureates, key=lambda m: m.name):
        print(f"  {person.name} ({person.gender})")

    roentgen_matches = [p for p in laureates if "Röntgen" in p.name]
    assert len(roentgen_matches) == 1
    physics = [p for p in prizes if p.slug == "Physics/1901"][0]
    assert physics.year == "1901"
    assert "Physics" in physics.title

    # Round-trip one laureate through in-memory graph
    roentgen = roentgen_matches[0]
    g = roentgen.to_graph()
    again = Laureate.from_graph(g, roentgen.subject_uri())
    assert again.name == roentgen.name
    print("Round-trip OK for Wilhelm Conrad Röntgen")


if __name__ == "__main__":
    main()
