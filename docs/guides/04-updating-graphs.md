# Updating graphs

Re-exporting with `to_graph()` alone **adds** triples; it does not remove stale ones when you clear a field. Use **sync modes** when you mutate a model and need the graph to match.

## Graph modes

| Mode | Behaviour |
|------|-----------|
| `"add"` | Default for `to_graph()`. Append triples only (0.1 behaviour). `sync_to_graph(..., mode="add")` also clears incoming inverse triples for inverse-mapped fields before appending forward triples. |
| `"replace"` | Remove all **owned** triples for the subject, then write current state. |
| `"patch"` | Remove triples only for fields that are `None` or empty `list` / `set`; replace all objects for other mapped predicates (including every value of multi-valued fields). |

**Owned predicates** = every mapped field predicate on the model plus `rdf:type` when `type_uri` is set. Triples with other predicates on the same subject are left untouched.

## Clearing a scalar field

```{literalinclude} ../../examples/doc/snippets/updating_clear_age.py
:language: python
```

Output:

```{literalinclude} ../../examples/doc/outputs/updating_clear_age.txt
:language: text
```

Same via the instance method:

```python
alice.sync_to_graph(graph, mode="replace")
```

## When to use each mode

- **`replace`** — You want the graph slice for this subject to match the model exactly (for owned predicates). Good after editing several fields.
- **`patch`** — You only cleared a few fields (for example set `age=None` or `nick=[]`) and want to drop those predicates without rewriting unrelated triples on the subject.
- **`add`** — Building a graph from scratch or appending new resources. Does not remove stale forward triples on the subject (use `replace` or `patch` for that). `sync_to_graph` with `mode="add"` still reconciles inverse predicates when fields use `inverse=`.

```python
# First write
alice.to_graph(graph)  # mode="add" by default

# Later update
alice.to_graph(graph, mode="replace")
# or
sync_to_graph(alice, graph, mode="replace")
```

## Patch and empty collections

```python
person = Person(slug="a", name="A", nick=["x"])
graph = person.to_graph()

sync_to_graph(Person(slug="a", name="A", nick=[]), graph, mode="patch")
# nick triples removed; name triples kept
```

CURIE predicates in `rdf_field("foaf:nick")` are expanded using `Rdf.prefixes` before removal.

## Triple ownership (SparqlModel)

**TripleModel** owns **mapped predicates** for a subject: sync removes prior `(subject, predicate, ?)` for those predicates, then writes current values.

**SparqlModel** (planned ORM layer) should call `sync_to_graph` for the resource’s owned triples, then apply its own rules: related-resource cascade, orphan cleanup, and what to include in a `put`.

See [Ecosystem](../ECOSYSTEM.md) for the full split.

## Nested resources

With **`embed="iri"`**, `replace` and `patch` remove owned triples on nested child subjects that are no longer linked (for example when `mbox=None` or the child `slug` changes), and remove stale `(?, inverse_predicate, child)` triples when the child had `inverse=` fields. **`embed="bnode"`** is experimental: `replace`/`patch` remove stale blank-node subgraphs and incoming inverse links in the same cases; prefer IRI embed for stable IRIs. See [Nested models](05-nested-models.md).

## Skolemize and shared graphs

`skolemize=True` on `sync_to_graph` affects the whole `Graph` you pass in. **`patch`** runs skolemize after stale cleanup and export; **`replace`** / **`add`** skolemize at the start of `write_model_add` before new triples are appended. When rdflib returns a new graph from `skolemize()`, use the graph returned from `sync_to_graph`.

**Next:** [Nested models →](05-nested-models.md)
