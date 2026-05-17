# Multi-valued fields

Use `list[T]` or `set[T]` when a predicate may have **multiple** objects (for example several `foaf:nick` values). TripleModel emits one triple per value and collects all objects on import. **`T` must be a scalar type** (for example `str`, `int`); `list[TripleModel]` and `set[TripleModel]` are not supported in 0.2 — use a single nested field instead.

## Lists (ordered)

```python
nick: list[str] = rdf_field("http://xmlns.com/foaf/0.1/nick", default_factory=list)
```

```python
person = Person(slug="alice", name="Alice", nick=["Al", "Alice"])
graph = person.to_graph()
restored = Person.from_graph(graph, person.subject_uri())
assert restored.nick == ["Al", "Alice"]
```

- **Order** is preserved for lists.
- **`None` elements** are skipped on export (use `model_construct` if you must build dirty data in tests).
- **Empty list** `[]` exports no `nick` triples.

## Sets (unordered, unique)

```python
tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)
```

```python
person = Person(slug="a", name="A", tag={"python", "rdf"})
```

On import, duplicate objects in the graph collapse to one set member. Export order is not guaranteed.

## Scalars vs collections

| Field shape | Multiple objects in graph |
|-------------|---------------------------|
| `str`, `int`, nested model, … | First only; `on_duplicate` applies |
| `list[T]`, `set[T]` | All objects imported |

```python
Person.from_graph(graph, uri, on_duplicate="error")  # raise on duplicate scalar
```

## Clearing a collection on update

Exporting `nick=[]` writes no new nick triples, but **does not remove** old nick triples in an existing graph unless you use a sync mode — see [Updating graphs](04-updating-graphs.md).

`sync_to_graph(..., mode="patch")` replaces **all** nick values for that subject in one step (not one-at-a-time), so `nick=["a", "b"]` round-trips correctly after a patch.

## Not RDF lists (`rdf:List`)

`list[str]` means “many objects for **one predicate**”, not linked-list `rdf:first` / `rdf:rest` structures. Native RDF list support is on the [roadmap](../ROADMAP.md) for **0.3**.

**Next:** [Updating graphs →](04-updating-graphs.md)
