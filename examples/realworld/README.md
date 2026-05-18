# Real-world TripleModel examples

Runnable examples that use **real vocabularies, public datasets, and typical integration problems**—not synthetic `http://example.org/` toys.

| Script | Real-world problem | Data file |
|--------|-------------------|-----------|
| [`nobel_laureates.py`](nobel_laureates.py) | Cultural heritage / biographical **linked open data** (stable URIs + ontology) | [`data/nobel_laureates_1901.ttl`](data/nobel_laureates_1901.ttl) |
| [`dcat_data_catalog.py`](dcat_data_catalog.py) | **Open data portal** metadata (find datasets & API endpoints) | [`data/dcat_nobel_catalog.ttl`](data/dcat_nobel_catalog.ttl) |
| [`wikidata_capitals.py`](wikidata_capitals.py) | **Knowledge-graph** facts (population, country) from Wikidata | [`data/wikidata_capitals.ttl`](data/wikidata_capitals.ttl) |
| [`schema_org_ngos.py`](schema_org_ngos.py) | **Nonprofit / transparency** records using Schema.org | [`data/schema_org_ngos.ttl`](data/schema_org_ngos.ttl) |

Provenance and licenses: [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Run (offline)

From the repository root:

```bash
pip install triplemodel
PYTHONPATH=src python examples/realworld/nobel_laureates.py
PYTHONPATH=src python examples/realworld/dcat_data_catalog.py
PYTHONPATH=src python examples/realworld/wikidata_capitals.py
PYTHONPATH=src python examples/realworld/schema_org_ngos.py
```

## Refresh Wikidata excerpt

Population figures change over time. To update `wikidata_capitals.ttl` from [Wikidata Query Service](https://query.wikidata.org/):

```bash
PYTHONPATH=src python examples/realworld/refresh_wikidata_capitals.py
```

## Live endpoints (optional)

These examples use **bundled files** so CI and tutorials work without network access. Production pipelines often call:

- Nobel Prize SPARQL: `http://data.nobelprize.org/sparql` ([docs](https://www.nobelprize.org/about/linked-data-examples/))
- Wikidata Query Service: `https://query.wikidata.org/`
- EU / national portals publishing **DCAT-AP** catalogs (see [data.europa.eu](https://data.europa.eu/))

Use `TripleModel.parse_url(...)` when you want TripleModel to fetch remote RDF directly.
