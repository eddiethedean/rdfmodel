# Quickstart

Minimal round-trip in a few lines. For narrative detail, see {doc}`guides/01-getting-started`.

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

alice = Person(slug="alice", name="Alice", age=30)
graph = alice.to_graph()

assert Person.from_graph(graph, alice.subject_uri()) == alice
```

## Serialize to Turtle

```{literalinclude} ../examples/doc/snippets/quickstart_turtle.py
:language: python
:lines: 17-19
```

Output:

```{literalinclude} ../examples/doc/outputs/quickstart_turtle.txt
:language: text
```

## Update an existing graph

Clearing a field requires a sync mode (default `to_graph` only appends):

```python
from triplemodel import sync_to_graph

alice.age = None
sync_to_graph(alice, graph, mode="replace")
```

See {doc}`guides/04-updating-graphs`.

**Next:** {doc}`guides/index`.
