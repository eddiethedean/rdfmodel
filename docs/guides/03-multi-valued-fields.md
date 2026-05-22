# Multi-valued fields

Use **`set[T]`** when a predicate may have **multiple** objects (for example several tags or duplicate `foaf:nick` literals without an RDF list). TripleModel emits one triple per value and collects all objects on import. **`T` must be a scalar type**; `set[TripleModel]` is not supported — use a single nested field instead.

For **ordered `rdf:List`** values, use **`list[T]`** — see {doc}`09-rdf-lists-and-lang`.

## Sets (unordered, unique)

```python
tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)
```

```python
person = Person(slug="a", name="A", tag={"python", "rdf"})
```

On import, duplicate objects in the graph collapse to one set member. Export order is not guaranteed.

- **`None` elements** are skipped on export.
- **Empty set** `set()` exports no triples for that predicate.

## URI references (`set` / `list`)

### `set[ResourceRef]` / `list[ResourceRef]`

Multiple object IRIs on one predicate (unordered set or ordered `rdf:List`):

```python
from triplemodel import ResourceRef, TripleModel, rdf_field

refs: set[ResourceRef] = rdf_field("http://example.org/mentions", default_factory=set)
```

### `ref_field` collections

Link to related `TripleModel` classes without embedding each resource (URI-only objects in the graph):

```python
from triplemodel import TripleModel, ref_field

tags: list[Tag] = ref_field("http://example.org/tagged", model=Tag, default_factory=list)
```

Use **`list[SomeModel]`** with `ref_field` for several URI links on one predicate (not an RDF list — one triple per member). Use **`set[ResourceRef]`** or **`list[ResourceRef]`** for bare IRIs (`list` uses an **`rdf:List`**). Pydantic model instances are not hashable, so `set[TripleModel]` with `ref_field` is rejected at class definition.

Import hydrates each object URI into a `Tag` instance. Export writes one triple per member (`subject`, predicate, object IRI). Use `hydrate_refs(instances, graph, "tags")` to batch-load linked models and reuse one Python instance per shared URI.

`list[TripleModel]` / `set[TripleModel]` **without** `ref_field` remain rejected (use a single nested embed field instead).

## `set[TypedLiteral]` — per-object XSD datatypes

Use **`set[TypedLiteral]`** (or **`list[TypedLiteral]`** for an ordered `rdf:List`) when several objects on one predicate may each carry a **different** ``^^datatype`` IRI. This differs from **`set[int]`** with **`literal_datatype=`**, which forces the same XSD type on every object.

```python
from triplemodel import TypedLiteral, TripleModel, rdf_field
from triplemodel.store.namespaces import XSD

class Measured(TripleModel):
    class Rdf:
        namespace = "http://example.org/"
        id_field = "slug"

    slug: str
    amount: set[TypedLiteral] = rdf_field(
        "http://example.org/amount", default_factory=set
    )

m = Measured(
    slug="m1",
    amount={
        TypedLiteral("1", str(XSD.integer.value)),
        TypedLiteral("1.0", str(XSD.decimal.value)),
    },
)
```

Import keeps both literals (same lexical form, different datatypes). For **`set[TypedLiteral]`**, duplicate **identical** `(value, datatype)` pairs respect `on_duplicate` on `from_graph`. For **`list[TypedLiteral]`** (`rdf:List`), duplicate entries in the list are preserved (no set-style deduplication). For a single scalar with an unknown datatype, use **`OpaqueLiteral`** instead.

## Scalars vs collections

| Field shape | Multiple objects in graph |
|-------------|---------------------------|
| `str`, `int`, nested model, … | First only; `on_duplicate` applies |
| `set[T]` | All objects imported as a set |
| `list[T]` | RDF list (`rdf:first` / `rdf:rest`); multiple list heads → first only — see guide 09 |

## Sync and cleared fields

When a field is cleared (`None`, empty `set()`, or empty `list`), `sync_to_graph(..., mode="replace"|"patch")` removes owned triples for that predicate. See {doc}`04-updating-graphs`.

For ordered **`rdf:List`** values, use **`list[T]`** instead — see {doc}`09-rdf-lists-and-lang`.
