# Stores, scale, and strict import

TripleModel supports chunked import, on-disk pyoxigraph stores, predicate-map caching, and strict data-quality checks.

## Predicate-map caching

Field → predicate IRIs are cached per model class when using the default resolver. Custom resolvers passed via ``resolver=`` bypass the cache.

## Strict import

On ``class Rdf``:

- ``strict_import = True`` — raise ``ValueError`` when the subject has triples whose predicates are not mapped on the model (except ``rdf:type``).
- ``warn_unmapped_fields = True`` — emit ``UserWarning`` instead of failing.

```python
class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/"
        type_uri = "http://example.org/Person"
        id_field = "slug"
        strict_import = True

    slug: str
    name: str = rdf_field("http://example.org/name")
```

## Chunked import

```python
from triplemodel import iter_graph_to_models

for chunk in iter_graph_to_models(graph, Person, chunk_size=500):
    process(chunk)
```

``graph_to_models(..., chunk_size=500)`` uses the same iterator internally.

## Streaming file load

For large **N-Triples** / **N-Quads** files, use ``load_models_streaming`` with an on-disk store:

```python
people = load_models_streaming(
    "huge.nt",
    Person,
    store="disk",
    store_identifier="/path/to/oxigraph-store",
    chunk_size=500,
)
```

Omit ``store`` to parse into memory. Turtle and TriG still require a full parse; convert to N-Quads for multi-GB inputs.

Legacy ``store="sqlalchemy"`` / ``"berkeleydb"`` emit a ``DeprecationWarning`` and map to ``disk``.

## Store helpers

```python
from triplemodel import open_graph, graph_store_session, store_commit

graph = open_graph("disk", "/path/to/oxigraph-store")
with graph_store_session(graph):
    Person.sync_to_graph(instance, graph)
    store_commit(graph)
```

See ``examples/stores/disk_store.py``. When ``parse_into_store_graph`` creates a temporary directory, call ``graph.close()`` to remove it. For remote SPARQL as the system of record, use {doc}`13-sparql-and-endpoints` and SparqlModel.

## Benchmark

``examples/exit_criteria_08.py`` loads a FOAF-shaped graph (default 100k people; set ``TRIPLEMODEL_BENCH_COUNT`` for CI smoke runs). Set ``TRIPLEMODEL_STORE=disk`` to exercise the on-disk streaming path.

## Plugin hooks

``triplemodel.plugins`` registers custom literals, resources, and predicate resolvers:

```python
from triplemodel.plugins import (
    register_literal_type,
    register_predicate_resolver,
)

register_predicate_resolver(MyResolver)
```

``register_parser``, ``register_serializer``, and ``register_store`` were removed in **0.10.0** (pyoxigraph has no rdflib plugin registry). See {doc}`../api/plugins` and {doc}`../MIGRATION_0.10`.

## Codegen (experimental)

```bash
triplemodel-codegen examples/codegen/sample.ttl -o models.py
```

OWL/RDFS classes and datatype properties become stub ``TripleModel`` subclasses. Output is best-effort only — see limitations in {doc}`../api/codegen`.
