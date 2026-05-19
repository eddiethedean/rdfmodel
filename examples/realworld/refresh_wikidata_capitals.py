#!/usr/bin/env python3
"""Refresh wikidata_capitals.ttl from Wikidata Query Service (CC0).

Uses a CONSTRUCT query and TripleModel file I/O (``parse_into_graph``, ``dump_graph``).
Wikidata requires a descriptive ``User-Agent``; this script POSTs via ``urllib`` rather
than ``open_sparql_graph`` so that header is set explicitly (see guide 13).
"""

from __future__ import annotations

import urllib.parse
import urllib.request

from triplemodel.store import RdfGraph as Graph

from triplemodel import __version__
from triplemodel.io.files import dump_graph, parse_into_graph

from _paths import DATA_DIR
from wikidata_capitals import WIKIDATA_PREFIXES

ENDPOINT = "https://query.wikidata.org/sparql"

CONSTRUCT_QUERY = """\
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
CONSTRUCT {
  ?city rdfs:label ?cityLabel .
  ?city wdt:P31 wd:Q174844 .
  ?city wdt:P1082 ?pop .
  ?city wdt:P17 ?country .
  ?country rdfs:label ?countryLabel .
}
WHERE {
  VALUES ?city { wd:Q90 wd:Q84 }
  ?city wdt:P31 wd:Q174844 .
  OPTIONAL { ?city wdt:P1082 ?pop }
  OPTIONAL {
    ?city wdt:P17 ?country .
    ?country rdfs:label ?countryLabel .
    FILTER(LANG(?countryLabel) = "en")
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


def fetch_construct_graph() -> Graph:
    data = urllib.parse.urlencode({"query": CONSTRUCT_QUERY}).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "User-Agent": f"triplemodel-examples/{__version__} (refresh_wikidata_capitals)",
            "Accept": "text/turtle",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode()
    return parse_into_graph(
        data=body,
        format="turtle",
        bind_prefixes=WIKIDATA_PREFIXES,
    )


def main() -> None:
    graph = fetch_construct_graph()
    out = DATA_DIR / "wikidata_capitals.ttl"
    dump_graph(graph, out, format="turtle")
    from wikidata_capitals import CapitalCity

    n = len(CapitalCity.all_from_graph(graph, validate_type=False))
    print(f"Wrote {out} ({n} capital cities)")


if __name__ == "__main__":
    main()
