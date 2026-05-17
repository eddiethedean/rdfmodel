# Getting started

This guide walks through installing TripleModel, defining a small model, and round-tripping it through an in-memory rdflib `Graph`.

## Install

```bash
pip install triplemodel
```

Requirements: Python **3.10+**, Pydantic v2, rdflib v7.

## Define a model

Subclass `TripleModel` and declare RDF metadata on a nested `Rdf` class. Map each RDF property with `rdf_field()`:

```python
from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)
```

| `Rdf` attribute | Purpose |
|---------------|---------|
| `namespace` | Base IRI; subject = namespace + encoded `id_field` value |
| `type_uri` | Written as `rdf:type` on export; filters `all_from_graph()` |
| `id_field` | Python field used to build the subject IRI |

Fields **without** a predicate (no `rdf_field` / `Predicate`) are ignored on export and import — useful for computed or application-only data.

## Export to a graph

```python
alice = Person(slug="alice", name="Alice", age=30)

graph = alice.to_graph()
print(alice.subject_uri())
```

Output:

```{literalinclude} ../../examples/doc/outputs/getting_started_export.txt
:language: text
```

`to_graph()` returns a new `Graph` when you do not pass one. Optional fields set to `None` (here `age` when omitted) produce **no triple** on export.

## Import from a graph

Load one resource by subject IRI:

```python
restored = Person.from_graph(graph, alice.subject_uri())
assert restored == alice
```

Load every resource with the configured `type_uri`:

```python
people = Person.all_from_graph(graph)
assert len(people) == 1
```

## Module-level functions

You can export without calling instance methods:

```python
from triplemodel import model_to_graph, graph_to_model

graph = model_to_graph(alice)
restored = graph_to_model(graph, Person, alice.subject_uri())
```

## What is not covered yet

TripleModel **0.3.x** works on in-memory graphs. File `parse` / `serialize` helpers are planned for **0.4** — today you can still call `graph.serialize(format="turtle")` from rdflib directly after `to_graph()`.

See the {doc}`guides index <index>` for multi-value fields, sync/update semantics, nested models, and prefixes.

**Next:** [Mapping fields and subjects →](02-mapping-fields-and-subjects.md)
