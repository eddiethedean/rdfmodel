# File I/O (parse and serialize)

TripleModel **0.4** wraps rdflib’s `Graph.parse` and `Graph.serialize` so model classes load and save RDF documents directly.

## Serialize to a string or file

```python
from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF}

    slug: str
    name: str = rdf_field("foaf:name")

person = Person(slug="alice", name="Alice")
ttl = person.serialize(format="turtle")
person.serialize(destination="alice.ttl")
```

## Parse from a string, file, or URL

```python
people = Person.parse(data=ttl, format="turtle")
people = Person.parse_file("alice.ttl")
people = Person.parse_url("https://example.org/data.ttl")
```

Format is inferred from the file suffix when omitted (`.ttl` → Turtle, `.trig` → TriG, and so on).

## Base URI for relative IRIs

Set `Rdf.base_uri` (or pass `base=` to `parse`) so relative IRIs in Turtle resolve correctly (rdflib 7 `publicID` semantics):

```python
class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        base_uri = "http://example.org/people/"
        ...
```

## JSON-LD context

Optional default context on `Rdf.jsonld_context` is passed through when `format="json-ld"`.

## Subclass dispatch

When a document contains several `rdf:type` values and you have registered subclasses, use `dispatch=True`:

```python
instances = TripleModel.parse(data=ttl, format="turtle", dispatch=True)
```

Each subject is loaded as the most specific registered model class. **Note:** `Person.parse(..., dispatch=True)` loads **every** registered `rdf:type` in the graph, not only `Person`; `type_uri=` is ignored when `dispatch=True`.

Low-level helpers: `graph_to_model_dispatch` and `all_from_graph_dispatch` (accept `resolver=`, `registry=`, `de_skolemize=`).

## Import options on class methods

`from_graph`, `all_from_graph`, and `parse` / `parse_file` / `parse_url` accept `resolver=` and `registry=` for custom predicate resolution and literal conversion. `all_from_graph` and `graph_to_models` also accept `de_skolemize=`.

## Inverse predicates

Map `owl:inverseOf`-style data on import with `inverse=` on `rdf_field` or `InverseOf` metadata (not on `list` / `set` fields). Export writes only the forward predicate. On `sync_to_graph(..., mode="replace")` or `mode="patch"`, all incoming inverse triples for inverse fields are cleared before re-export (including reassignment and dropped nested IRI/bnode children). If both forward and inverse triples exist for the same field, import uses the forward objects and warns (or raises with `on_duplicate="error"`).

## SHACL validation (optional)

Install `pip install triplemodel[shacl]`, then validate before export:

```python
person.to_graph(shacl_shapes="shapes.ttl")
person.serialize(format="turtle", shacl_shapes=shapes_graph)
```

## Multi-class load (one parse)

When one Turtle file contains several `rdf:type`s (Nobel laureates and prizes, DCAT catalog and datasets):

```python
from triplemodel import load_graph, load_models, load_models_from_graph

bundles = load_models("catalog.ttl", DataCatalog, Dataset, Distribution)
catalogs = bundles[DataCatalog]

graph = load_graph("catalog.ttl", bind_prefixes=DataCatalog.Rdf.prefixes)
bundles = load_models_from_graph(graph, DataCatalog, Dataset)
```

For a single heterogeneous list by registered `rdf:type`, use `parse_file(..., dispatch=True)` instead.

See {doc}`11-real-world-patterns` for Wikidata typing, `ref_field`, and XSD `gYear`.

## Module helpers

```python
from triplemodel import load_models, dump_model

people = load_models("people.ttl", Person)
dump_model(person, "out.ttl", format="turtle")
```
