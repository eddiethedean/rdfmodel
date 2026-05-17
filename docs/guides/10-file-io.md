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

Each subject is loaded as the most specific registered model class.

## Inverse predicates

Map `owl:inverseOf`-style data on import with `inverse=` on `rdf_field` or `InverseOf` metadata. Export writes only the forward predicate.

## SHACL validation (optional)

Install `pip install triplemodel[shacl]`, then validate before export:

```python
person.to_graph(shacl_shapes="shapes.ttl")
person.serialize(format="turtle", shacl_shapes=shapes_graph)
```

## Module helpers

```python
from triplemodel import load_models, dump_model

people = load_models("people.ttl", Person)
dump_model(person, "out.ttl", format="turtle")
```
