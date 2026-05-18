# Working with graphs

Patterns for multiple resources, merging graphs, and small helpers that mirror common rdflib access patterns with type awareness.

## Batch export

```python
from triplemodel import models_to_graph

people = [
    Person(slug="alice", name="Alice"),
    Person(slug="bob", name="Bob"),
]
graph = models_to_graph(people)
```

Merge into an **existing** graph (note: an empty `Graph()` is falsy in Python — pass it explicitly):

```python
from rdflib import Graph

existing = Graph()
models_to_graph(people, existing)
```

## Batch import

```python
everyone = Person.all_from_graph(graph)
by_slug = {p.slug: p for p in everyone}
```

Only subjects with `rdf:type` matching `Rdf.type_uri` are returned. Blank-node subjects are skipped. Override the type filter with `type_uri=` when needed.

## File helpers

```python
from triplemodel import load_models, dump_model

people = load_models("people.ttl", Person)
dump_model(people[0], "alice.ttl", format="turtle")
```

See {doc}`10-file-io` for `parse_url`, subclass `dispatch=True`, and SHACL.

## Merge graphs

```python
from triplemodel import merge_graphs

g_alice = Person(slug="alice", name="Alice").to_graph()
g_bob = Person(slug="bob", name="Bob").to_graph()
combined = merge_graphs(g_alice, g_bob)
```

When merging graphs that contain blank nodes, node identity is preserved as rdflib does — do not assume unrelated parses share BNode ids.

## Graph helpers

```python
from triplemodel import graph_value, graph_set, objects_for_field

uri = person.subject_uri()
g = person.to_graph()

name = graph_value(g, uri, f"{FOAF}name", Person, "name")

graph_set(g, uri, f"{FOAF}name", "Alicia")  # remove-then-add for functional property
graph_set(g, uri, f"{FOAF}age", None)       # remove all objects for predicate

nicks = objects_for_field(g, uri, Person, "nick")  # list[str] for list fields
```

These helpers use the model’s predicate resolution (including CURIE expansion from `Rdf.prefixes`).

## Low-level triple access

```python
triples = person.to_triples()
# list of (subject, predicate, object) — subject may be str or BNode for bnode embed
```

```python
from triplemodel import model_to_triples, model_to_graph, graph_to_model
```

Use when building pipelines that are not method-oriented.

## Serialize for debugging

```python
print(person.to_graph().serialize(format="turtle"))
```

## Skolemize and shared graphs

When `Rdf.skolemize_export` / `Rdf.skolemize_import` is enabled (or you pass `skolemize=` / `de_skolemize=` on `to_graph`, `from_graph`, or `sync_to_graph`), rdflib’s `skolemize()` / `de_skolemize()` runs on the **entire** `Graph` you pass in—not only triples owned by the resource you are loading or syncing. If multiple resources share one graph, blank-node handling for one operation can affect unrelated triples. Use a dedicated graph per resource, or disable skolemization, when you need isolation.

## Related guides

- [Graph algorithms and RDFS](14-graph-algorithms-and-rdfs.md) — `graphs_equal`, CBD, safe merge with separate parses
- [Updating graphs](04-updating-graphs.md) — sync after batch load
- [Namespaces and CURIEs](06-namespaces-and-curies.md) — prefixes on merged graphs
- [Getting started](01-getting-started.md) — first model

{doc}`← Guides index <index>`
