#!/usr/bin/env python3
"""Schema.org NGOs: nonprofit registry records from structured web data.

Problem: transparency portals and search engines publish organization metadata
with schema.org (JSON-LD or RDF); map it into Pydantic for validation and ETL.

Data: examples/realworld/data/schema_org_ngos.ttl
"""

from __future__ import annotations

from triplemodel import TripleModel, models_to_graph, rdf_field
from triplemodel.vocab import XSD

from _paths import data_file

SCHEMA = "https://schema.org/"


class NgoOrganization(TripleModel):
    class Rdf:
        namespace = "https://example.org/org/"
        type_uri = f"{SCHEMA}NGO"
        id_field = "slug"
        prefixes = {"schema": SCHEMA, "xsd": str(XSD)}

    slug: str
    name: str = rdf_field("schema:name")
    url: str = rdf_field("schema:url")
    nonprofit_status: str | None = rdf_field("schema:nonprofitStatus", default=None)
    founding_year: int | None = rdf_field(
        "schema:foundingDate", default=None, literal_datatype="xsd:gYear"
    )


def main() -> None:
    ngos = NgoOrganization.parse_file(data_file("schema_org_ngos.ttl"))
    print(f"Loaded {len(ngos)} NGO records")
    for org in sorted(ngos, key=lambda o: o.name):
        founded = org.founding_year if org.founding_year is not None else "n/a"
        print(f"  {org.name} (founded {founded}) — {org.url}")

    graph = models_to_graph(ngos)
    assert len(list(graph.subjects())) >= len(ngos)
    wwf = next(o for o in ngos if o.slug == "wwf")
    ttl = wwf.serialize(format="turtle")
    assert isinstance(ttl, str)
    assert "schema:name" in ttl or "World Wide Fund" in ttl
    print("Merged graph export OK")


if __name__ == "__main__":
    main()
