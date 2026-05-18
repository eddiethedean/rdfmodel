# Stores, scale, and strict import (0.8)

TripleModel **0.8** adds optional on-disk rdflib stores, chunked import, predicate-map caching, and strict data-quality checks.

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

For large **N-Triples** / **N-Quads** files, use ``load_models_streaming`` with an optional SQLAlchemy store (``pip install triplemodel[sqlalchemy]``):

```python
people = load_models_streaming(
    "huge.nt",
    Person,
    store="sqlalchemy",
    chunk_size=500,
)
```

Turtle and TriG still require a full parse; convert to N-Quads for multi-GB inputs.

## Store helpers

```python
from triplemodel import open_graph, graph_store_session, store_commit

graph = open_graph("sqlalchemy", "sqlite:///data/graph.sqlite")
with graph_store_session(graph):
    Person.sync_to_graph(instance, graph)
    store_commit(graph)
```

See ``examples/stores/sqlalchemy_sqlite.py`` and {doc}`13-sparql-and-endpoints` for remote SPARQL as the system of record.

## Benchmark

``examples/exit_criteria_08.py`` loads a FOAF-shaped graph (default 100k people; set ``TRIPLEMODEL_BENCH_COUNT`` for CI smoke runs).

## Plugin hooks

``triplemodel.plugins`` re-exports ``register_literal_type``, ``register_rdf_resource``, and ``register_predicate_resolver``. Full rdflib parser/store registration is planned for **0.9**.

## Codegen (experimental)

```bash
triplemodel-codegen examples/codegen/sample.ttl -o models.py
```

OWL/RDFS classes and datatype properties become stub ``TripleModel`` subclasses. Output is best-effort only — see limitations in {doc}`../api/codegen`.
