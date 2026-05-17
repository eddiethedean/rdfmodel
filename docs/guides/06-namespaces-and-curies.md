# Namespaces and CURIEs

Compact `prefix:local` predicates keep models readable and produce Turtle `PREFIX` lines when you serialize the graph.

## Declare prefixes on the model

```python
from triplemodel.vocab import FOAF

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
```

`list[str]` maps to an **`rdf:List`**, not multiple `foaf:nick` triples. Use `set[str]` for several objects on one predicate — see {doc}`09-rdf-lists-and-lang`.

On `to_graph()` / `sync_to_graph()` with a **new** graph, prefixes are bound automatically when `bind=True` (default for sync on empty graphs).

## CURIE expansion

Module helper:

```{literalinclude} ../../examples/doc/snippets/mapping_expand_curie.py
:language: python
```

Output:

```{literalinclude} ../../examples/doc/outputs/mapping_expand_curie.txt
:language: text
```

Absolute IRIs pass through unchanged. Unknown prefixes raise `ValueError`.

## Turtle output

```python
graph = person.to_graph()
ttl = graph.serialize(format="turtle")
# PREFIX foaf: <http://xmlns.com/foaf/0.1/> ...
```

TripleModel does not yet ship file `parse` / `serialize` wrappers (**0.4**); use rdflib’s `serialize` as above.

## Manual bind on an existing graph

```python
from triplemodel import bind_namespaces

bind_namespaces(graph, {"foaf": "http://xmlns.com/foaf/0.1/"}, strategy="core")
```

| `strategy` | Effect |
|------------|--------|
| `"core"` | `graph.bind(prefix, namespace)` for each entry |
| `"rdflib"` | Also call rdflib’s `bind_namespaces()` when available |
| `"none"` | No-op |

Pass `bind=False` to `sync_to_graph` when merging into a graph that already has prefix bindings.

## Vocabulary shortcuts

```python
from triplemodel.vocab import FOAF, DCTERMS, SKOS, OWL, RDFS, XSD
```

These re-export rdflib `DefinedNamespace` objects so you can write `f"{FOAF}name"` in full-IRI form and still add `prefixes = {"foaf": str(FOAF)}` for CURIE fields.

**Next:** [Custom literals →](07-custom-literals-and-types.md)
