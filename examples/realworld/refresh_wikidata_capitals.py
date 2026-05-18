#!/usr/bin/env python3
"""Refresh wikidata_capitals.ttl from Wikidata Query Service (CC0)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from _paths import DATA_DIR

QUERY = """\
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?city ?cityLabel ?pop ?country ?countryLabel WHERE {
  VALUES ?city { wd:Q90 wd:Q84 wd:Q64 }
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


def fetch_rows() -> list[dict[str, str]]:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": QUERY, "format": "json"}
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "triplemodel-examples/0.4.0 (refresh_wikidata_capitals)"
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    rows: list[dict[str, str]] = []
    for binding in payload["results"]["bindings"]:
        rows.append(
            {
                "city": binding["city"]["value"],
                "cityLabel": binding["cityLabel"]["value"],
                "pop": binding.get("pop", {}).get("value", ""),
                "country": binding.get("country", {}).get("value", ""),
                "countryLabel": binding.get("countryLabel", {}).get("value", ""),
            }
        )
    return rows


def build_turtle(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Wikidata excerpt: capital cities (English label, population, country)",
        "# Entities: Q90 Paris, Q84 London, Q64 Berlin — CC0 1.0",
        "# Generated from Wikidata Query Service; see refresh_wikidata_capitals.py",
        "",
        "@prefix wd: <http://www.wikidata.org/entity/> .",
        "@prefix wdt: <http://www.wikidata.org/prop/direct/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]
    countries: dict[str, str] = {}
    for row in rows:
        qid = row["city"].rsplit("/", 1)[-1]
        lines.append(f"wd:{qid} rdfs:label {json.dumps(row['cityLabel'])}@en ;")
        lines.append("    wdt:P31 wd:Q174844 ;")
        if row["pop"]:
            lines.append(f'    wdt:P1082 "{row["pop"]}"^^xsd:decimal ;')
        if row["country"]:
            cqid = row["country"].rsplit("/", 1)[-1]
            lines.append(f"    wdt:P17 wd:{cqid} .")
            if row["countryLabel"]:
                countries[cqid] = row["countryLabel"]
        else:
            lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")
    for cqid, label in sorted(countries.items()):
        lines.append(f"wd:{cqid} rdfs:label {json.dumps(label)}@en .")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = fetch_rows()
    out = DATA_DIR / "wikidata_capitals.ttl"
    out.write_text(build_turtle(rows), encoding="utf-8")
    print(f"Wrote {out} ({len(rows)} cities)")


if __name__ == "__main__":
    main()
