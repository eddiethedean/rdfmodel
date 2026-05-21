# Migrating to TripleModel 0.10.0 (pyoxigraph)

**0.10.0** replaces [rdflib](https://github.com/RDFLib/rdflib) with [pyoxigraph](https://github.com/oxigraph/pyoxigraph) as the sole **runtime** RDF engine. Mapping APIs (`TripleModel`, `rdf_field`, `to_graph`, `from_graph`, `load_models`, …) are unchanged; **graph container types** and a few rdflib-specific hooks are not.

## Dependency

```bash
pip install 'triplemodel>=0.10,<2'
```

Core install no longer pulls in rdflib. (SHACL was removed entirely in **0.11.0** — see [MIGRATION_0.11.md](MIGRATION_0.11.md).)

## Replace `rdflib.Graph` with `triplemodel.Store`

Import the graph type from TripleModel (alias over `RdfGraph`, backed by `pyoxigraph.Store`):

```python
from triplemodel import Store

graph = Store()  # in-memory
person.to_graph(graph)
Person.from_graph(graph, uri)
```

Method names **`to_graph`** / **`from_graph`** are kept for compatibility; they operate on `Store` instances.

On-disk persistence:

```python
from triplemodel.io.stores import open_graph

graph = open_graph("disk", "/path/to/store")
```

## Removed APIs

| Removed | Replacement |
|---------|-------------|
| `register_parser` / `register_serializer` / `register_store` | pyoxigraph built-in parsers; no plugin registry |
| `open_sparql_graph` (rdflib `SPARQLStore`) | Load remote data into a local `Store`, or use SparqlModel |
| `triplemodel[sqlalchemy]` extra | `open_graph("disk", path)` |
| Formats: `hext`, `longTurtle`, `trix` | Turtle, TriG, N-Triples, N-Quads, RDF/XML, N3, JSON-LD |

## SparqlModel

Adopt **`triplemodel>=0.10,<2`** when SparqlModel releases a matching pin (**SM-7**). Do not pass rdflib `Graph` objects from TripleModel helpers into older SparqlModel versions.

## Literal typing

pyoxigraph requires lexical string forms for typed literals; TripleModel handles this on export. Custom `LiteralRegistry` converters should return `pyoxigraph.Literal` values.
