# Cookbook

Task-oriented recipes. For tutorials, see the {doc}`../guides/index` user guide.

## Formats and files

- **Serialize / parse** — {doc}`../guides/10-file-io` (`TripleModel.parse`, `.serialize`, `infer_format`)
- **Base URI** for relative IRIs — `Rdf.base_uri` and `parse(..., base=)` in guide 10
- **Supported formats** — Turtle, TriG, N-Triples, N-Quads, RDF/XML, N3, JSON-LD (pass `format=` explicitly when needed)

## SPARQL and Fuseki

- **In-memory SPARQL** — {doc}`../guides/13-sparql-and-endpoints` (`select_models`, `construct_models`, `ask`, `apply_update`)
- **Remote endpoints** — fetch RDF into a local `Store`, then run CONSTRUCT/SELECT helpers (see guide 13). `load_sparql` / `open_sparql_graph` raise `NotImplementedError` in **0.10.0**.
- **Apache Jena Fuseki** (optional): export or CONSTRUCT from Fuseki, save to a file, then load locally:

```python
from triplemodel import Store, load_graph
from triplemodel.io.sparql import construct_models

# After downloading Turtle/N-Triples from Fuseki (urllib, httpx, etc.):
graph = load_graph("fuseki-export.nt", format="nt")
people = construct_models(
    Person,
    graph,
    """
    CONSTRUCT { ?s ?p ?o }
    WHERE { ?s a foaf:Person . ?s ?p ?o }
    """,
)
```

Use `apply_update` against a **writable local** `Store` after loading data; remote SPARQL Update is out of scope for core TripleModel.

## Named graphs (Dataset)

- **TriG / N-Quads** — {doc}`../guides/12-datasets-and-named-graphs`
- **`Rdf.graph_iri`**, `load_dataset`, `model_to_dataset`

## SHACL validation

- Install: `pip install triplemodel[shacl]`
- Pre-export validation — {doc}`../guides/10-file-io` (SHACL section) and `validate_graph`

## Persistent stores

- **On-disk pyoxigraph** — `open_graph("disk", path)`; call `graph.close()` when using a temporary directory from `parse_into_store_graph`; see `examples/stores/disk_store.py` and {doc}`../guides/15-stores-scale-and-strict`
- **LevelDB / Kyoto / GraphDB / RDF4J** — use vendor SDKs or SparqlModel directly (**out of scope** for core)

## Scale and strict import

- **Chunked load** — `iter_graph_to_models`, `load_models_streaming` (guide 15)
- **Strict mode** — `Rdf.strict_import`, `Rdf.warn_unmapped_fields`

## Custom plugins (literals and resolvers)

```python
from triplemodel.plugins import register_literal_type, register_predicate_resolver
```

Parser/serializer/store registration was removed in **0.10.0** — see {doc}`../api/plugins` and {doc}`../MIGRATION_0.10`.

## Real-world datasets

Runnable examples with public vocabularies (Nobel, DCAT, Wikidata, Schema.org):

- Repository: `examples/realworld/`
- Patterns: {doc}`../guides/11-real-world-patterns`

## Experimental codegen

```bash
triplemodel-codegen ontology.ttl -o models.py
```

See {doc}`../api/codegen`.
