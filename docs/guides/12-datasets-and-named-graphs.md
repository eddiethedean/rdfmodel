# Datasets and named graphs

TripleModel **0.5** maps each model class to an rdflib **named graph** via `Rdf.graph_iri`, then reads and writes through `rdflib.Dataset` (TriG, N-Quads).

## Configure a named graph

```python
class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = "http://xmlns.com/foaf/0.1/Person"
        id_field = "slug"
        graph_iri = "http://example.org/graph/people"  # alias: Rdf.graph

    slug: str
    name: str = rdf_field("foaf:name")
```

When `graph_iri` is omitted, triples use the dataset **default graph** (same as a flat `Graph`).

### Instance override

- Implement `def graph_iri(self) -> str | None` on the model, or
- Set a non-field attribute `_graph_iri` on the instance (not mapped with `rdf_field`).

Class-level `Rdf.graph_iri` is used when no instance override is present.

## Export and import

```python
from triplemodel import models_to_dataset, load_models_from_dataset, parse_into_dataset

people = [Person(slug="alice", name="Alice")]
ds = models_to_dataset(people)
ds.serialize(destination="people.trig", format="trig")

loaded = load_models_from_dataset(parse_into_dataset("people.trig"), Person)
```

Instance helpers mirror `to_graph` / `from_graph`:

| Graph API | Dataset API |
|-----------|-------------|
| `to_graph()` | `to_dataset()` |
| `from_graph(ds, uri)` | `from_dataset(ds, uri)` |
| `all_from_graph(g)` | `all_from_dataset(ds)` |
| `sync_to_graph(g)` | `sync_to_dataset(ds)` |

`parse` / `parse_file` / `parse_url` automatically use a `Dataset` when the format is **TriG** or **N-Quads**, or when the model class defines `Rdf.graph_iri`.

## Multiple classes, multiple graphs

```python
bundles = load_models("portal.trig", Catalog, Dataset, Distribution)
```

Each class is loaded from its own `Rdf.graph_iri` context after a single parse.

## Subclass dispatch on datasets

`parse(..., dispatch=True)` on TriG/N-Quads and `all_from_dataset_dispatch` use the same rules as graph dispatch: each subject is loaded **once** as the most specific registered class for its `rdf:type` values. When a subject appears in several named graphs, types are unioned for class resolution, then the graph matching the model's `Rdf.graph_iri` is used for hydration.

Pass `model_classes=[Person, Catalog]` to load only those exact classes (recommended when unrelated models are registered in the same process).

## Default graph vs union

| Operation | Behavior |
|-----------|----------|
| `from_dataset`, `all_from_dataset` | **One context only** — the model's `graph_iri` or the default graph |
| `dataset.query(...)` (rdflib) | May use the **union** of graphs depending on rdflib version and query form |
| `parse_into_graph` on TriG | Can **lose** named-graph boundaries; use `parse_into_dataset` instead |

TripleModel does not wrap SPARQL until **0.6**; use rdflib directly for ad hoc queries.

## Nested models

When a parent exports an embedded child, nested triples are written to the **parent's** resolved graph context. A child's `graph_iri` applies when that child is exported or loaded on its own (or via `models_to_dataset` grouping).

## Migration from ConjunctiveGraph

rdflib 7 deprecates `ConjunctiveGraph` in favor of **`Dataset`**. In TripleModel:

- Replace `ConjunctiveGraph()` with `Dataset()`.
- Use `parse_into_dataset` / `load_dataset` instead of `parse_into_graph` for TriG and N-Quads.
- `Rdf.base_uri` (`publicID` on parse) is unchanged from 0.4.

See the [rdflib documentation](https://rdflib.readthedocs.io/en/stable/) (`Dataset`, named graphs, and quads).

## Helpers

```python
from triplemodel import (
    get_graph_context,
    iter_model_quads,
    quads_in_context,
    is_quad_format,
)
```

- `get_graph_context(dataset, graph_iri)` — rdflib `Graph` context for I/O
- `iter_model_quads(model)` — `(subject, predicate, object, graph_iri)` rows
- `quads_in_context(dataset, graph_iri)` — iterate quads in one named graph
