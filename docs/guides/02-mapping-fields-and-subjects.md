# Mapping fields and subjects

This guide covers how fields become predicates, how subject IRIs are built and parsed, and how to mark a field as a full IRI id.

## Predicates with `rdf_field`

```python
name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
```

The string is stored as field metadata and used on export and import. You can pass any [Pydantic `Field`](https://docs.pydantic.dev/latest/concepts/fields/) keyword (`default`, `default_factory`, etc.).

## Predicates with `Annotated`

```python
from typing import Annotated
from triplemodel import Predicate

title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]
```

Both styles are equivalent for TripleModel; pick whichever fits your codebase.

## Subject IRIs

With `namespace = "http://example.org/people/"` and `id_field = "slug"`, instance `Person(slug="alice", ...)` gets subject:

```text
http://example.org/people/alice
```

Segments are [percent-encoded](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote) (`bob jones` → `bob%20jones`). Helpers on the package root:

```python
from triplemodel import subject_base, id_from_subject_uri

base = subject_base("http://example.org/people")  # ensures trailing / or #
segment = id_from_subject_uri(
    "http://example.org/people",
    "http://example.org/people/alice",
)  # "alice"
```

### Override the subject per call

```python
custom = "http://example.org/people/alice"
graph = alice.to_graph(uri=custom)
restored = Person.from_graph(graph, custom)
```

Import can only fill `id_field` from the URI when the subject is **under** `Rdf.namespace` (safe prefix match). Off-namespace URIs fail validation unless you supply triples another way.

### Full IRI as id (`IriId`)

When the id **is** the entire subject IRI (not namespace + segment), mark the field:

```python
from typing import Annotated
from triplemodel import IriId, TripleModel, rdf_field

class ExternalResource(TripleModel):
    class Rdf:
        namespace = "http://example.org/"  # still required for `subject_uri()` rules
        type_uri = "http://example.org/External"
        id_field = "uri"

    uri: Annotated[str, IriId()]
    title: str = rdf_field("http://example.org/title")

resource = ExternalResource(
    uri="https://catalog.example.org/item/42",
    title="Widget",
)
assert resource.subject_uri() == "https://catalog.example.org/item/42"
```

You can also store a full `http://`, `https://`, or `urn:` value in a normal `id_field` **without** `IriId` on export (`subject_uri()` returns it verbatim), but **import** requires `IriId` to recover that field from the graph.

## Term conversion (scalars)

| Python type | RDF object (typical) |
|-------------|----------------------|
| `str` (plain text) | `xsd:string` literal |
| `str` with URI scheme (`http://`, `urn:`, `mailto:`, …) | `URIRef` |
| `int`, `float`, `bool` | XSD literal |
| `date`, `datetime` | XSD date / dateTime |
| `None` on optional field | No triple on export |

CURIE-shaped strings like `foaf:name` are **not** treated as IRIs; they stay literals unless you use [Namespaces and CURIEs](06-namespaces-and-curies.md) on the field predicate.

## Inheriting `class Rdf`

If a child class does **not** define `class Rdf`, it inherits the parent’s config. If the child defines `class Rdf:`, it **replaces** the parent entirely — an empty child `Rdf` clears `namespace`, `type_uri`, and `id_field`. Omit `Rdf` on the child when you only add fields.

## Type checking on import

When `type_uri` is set, `from_graph(..., validate_type=True)` (default) requires `(subject, rdf:type, type_uri)` in the graph. Pass `validate_type=False` to skip.

## Duplicate objects on scalar fields

If the graph has **multiple objects** for one scalar predicate, import keeps the first and warns by default (`on_duplicate="warn"`). Use `"error"` or `"ignore"` as needed. Collection fields import **all** values — see [Multi-valued fields](03-multi-valued-fields.md).

**Next:** [Multi-valued fields →](03-multi-valued-fields.md)
