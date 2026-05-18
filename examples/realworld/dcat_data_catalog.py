#!/usr/bin/env python3
"""DCAT data catalog: discover datasets and API endpoints in a portal export.

Problem: governments and EU institutions publish metadata as DCAT/DCAT-AP so
users can find datasets and SPARQL/HTTP distributions before downloading data.

Data: examples/realworld/data/dcat_nobel_catalog.ttl
Source: DCAT-AP sample describing Nobel Media linked data (SEMIC / nobelprize.org)
"""

from __future__ import annotations

from typing import cast

from triplemodel import TripleModel, load_models, rdf_field

from _paths import data_file

DCAT = "http://www.w3.org/ns/dcat#"
DCT = "http://purl.org/dc/terms/"


class DataCatalog(TripleModel):
    class Rdf:
        namespace = "http://example.org/catalog/"
        type_uri = f"{DCAT}Catalog"
        id_field = "slug"
        prefixes = {"dcat": DCAT, "dct": DCT}

    slug: str
    title: str = rdf_field(f"{DCT}title")
    description: str | None = rdf_field(f"{DCT}description", default=None)


class Dataset(TripleModel):
    class Rdf:
        namespace = "http://example.org/dataset/"
        type_uri = f"{DCAT}Dataset"
        id_field = "slug"
        prefixes = {"dcat": DCAT, "dct": DCT}

    slug: str
    title: str = rdf_field(f"{DCT}title")
    description: str | None = rdf_field(f"{DCT}description", default=None)
    keywords: set[str] = rdf_field(f"{DCAT}keyword", default_factory=set)


class Distribution(TripleModel):
    class Rdf:
        namespace = "http://example.org/distribution/"
        type_uri = f"{DCAT}Distribution"
        id_field = "slug"
        prefixes = {"dcat": DCAT, "dct": DCT}

    slug: str
    title: str = rdf_field(f"{DCT}title")
    access_url: str = rdf_field(f"{DCAT}accessURL")


def main() -> None:
    path = data_file("dcat_nobel_catalog.ttl")
    bundles = load_models(path, DataCatalog, Dataset, Distribution)
    catalogs = cast(list[DataCatalog], bundles[DataCatalog])
    datasets = cast(list[Dataset], bundles[Dataset])
    distributions = cast(list[Distribution], bundles[Distribution])

    print(f"Catalog: {catalogs[0].title}")
    for ds in datasets:
        print(f"  Dataset: {ds.title}")
        print(f"    Keywords: {', '.join(sorted(ds.keywords))}")
    for dist in distributions:
        print(f"  Distribution: {dist.title}")
        print(f"    accessURL: {dist.access_url}")

    assert any("nobelprize.org/sparql" in d.access_url for d in distributions)
    assert "Nobel prize" in datasets[0].keywords
    print("DCAT catalog parse OK")


if __name__ == "__main__":
    main()
