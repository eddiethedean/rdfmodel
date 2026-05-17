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

## Scalars vs collections

| Field shape | Multiple objects in graph |
|-------------|---------------------------|
| `str`, `int`, nested model, … | First only; `on_duplicate` applies |
| `set[T]` | All objects imported as a set |
| `list[T]` | RDF list (`rdf:first` / `rdf:rest`) — see guide 09 |

## Sync and cleared fields

When a field is cleared (`None`, empty `set()`, or empty `list`), `sync_to_graph(..., mode="replace"|"patch")` removes owned triples for that predicate. See {doc}`04-updating-graphs`.

For ordered **`rdf:List`** values, use **`list[T]`** instead — see {doc}`09-rdf-lists-and-lang`.
