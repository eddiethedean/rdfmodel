# Cookbook

Task-oriented recipes. For tutorials, see the {doc}`../guides/index` user guide.

## Formats and files

- **Serialize / parse** — {doc}`../guides/10-file-io` (`TripleModel.parse`, `.serialize`, `infer_format`)
- **Base URI** for relative IRIs — `Rdf.base_uri` and `parse(..., base=)` in guide 10
- **All rdflib-registered formats** — pass `format=` (Turtle, TriG, JSON-LD, RDF/XML, N3, N-Quads, …)

## SPARQL and Fuseki

- **In-memory SPARQL** — {doc}`../guides/13-sparql-and-endpoints` (`select_models`, `construct_models`, `ask`, `apply_update`)
- **Remote endpoints** — `load_sparql`, `open_sparql_graph`; prefer **CONSTRUCT** for full model round-trip
- **Apache Jena Fuseki** (optional): run Fuseki with your dataset, then:

```python
from triplemodel import load_sparql

QUERY = """
CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 100
"""
people = load_sparql(MyModel, "http://localhost:3030/ds/sparql", QUERY)
```

Use `apply_update` for SPARQL Update against a writable store when rdflib’s `SPARQLUpdateStore` is configured.

## Named graphs (Dataset)

- **TriG / N-Quads** — {doc}`../guides/12-datasets-and-named-graphs`
- **`Rdf.graph_iri`**, `load_dataset`, `model_to_dataset`

## SHACL validation

- Install: `pip install triplemodel[shacl]`
- Pre-export validation — {doc}`../guides/10-file-io` (SHACL section) and `validate_graph`

## Persistent and optional stores

- **SQLAlchemy** — `pip install triplemodel[sqlalchemy]`; see `examples/stores/sqlalchemy_sqlite.py` and {doc}`../guides/15-stores-scale-and-strict`
- **BerkeleyDB** — `triplemodel[berkeleydb]` extra (non-Windows)
- **LevelDB / Kyoto / GraphDB / RDF4J** — use rdflib or vendor SDKs directly (**out of scope** for core; register custom stores via `triplemodel.plugins.register_store`)

## Scale and strict import

- **Chunked load** — `iter_graph_to_models`, `load_models_streaming` (guide 15)
- **Strict mode** — `Rdf.strict_import`, `Rdf.warn_unmapped_fields`

## Custom rdflib plugins

```python
from triplemodel.plugins import register_parser, register_serializer, register_store

register_parser("myfmt", "myapp.plugins", "MyParser")
```

See {doc}`../api/plugins`.

## Real-world datasets

Runnable examples with public vocabularies (Nobel, DCAT, Wikidata, Schema.org):

- Repository: `examples/realworld/`
- Patterns: {doc}`../guides/11-real-world-patterns`

## Experimental codegen

```bash
triplemodel-codegen ontology.ttl -o models.py
```

See {doc}`../api/codegen`.
