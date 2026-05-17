# Updating graphs

Re-exporting with `to_graph()` alone **adds** triples; it does not remove stale ones when you clear a field. Use **sync modes** when you mutate a model and need the graph to match.

## Graph modes

| Mode | Behaviour |
|------|-----------|
| `"add"` | Default for `to_graph()`. Append triples only (0.1 behaviour). |
| `"replace"` | Remove all **owned** triples for the subject, then write current state. |
| `"patch"` | Remove triples only for fields that are `None` or empty `list` / `set`; add/update others. |

**Owned predicates** = every mapped field predicate on the model plus `rdf:type` when `type_uri` is set. Triples with other predicates on the same subject are left untouched.

## Clearing a scalar field

```python
from triplemodel import sync_to_graph

alice = Person(slug="alice", name="Alice", age=30)
graph = alice.to_graph()

alice.age = None
sync_to_graph(alice, graph, mode="replace")
# foaf:age triples for alice are gone
```

Same via the instance method:

```python
alice.sync_to_graph(graph, mode="replace")
```

## When to use each mode

- **`replace`** — You want the graph slice for this subject to match the model exactly (for owned predicates). Good after editing several fields.
- **`patch`** — You only cleared a few fields (for example set `age=None` or `nick=[]`) and want to drop those predicates without rewriting unrelated triples on the subject.
- **`add`** — Building a graph from scratch or appending new resources; stale triples are acceptable or impossible.

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

`replace` on a parent clears the parent’s `foaf:mbox` **link** when `mbox=None`. Triples about the child subject may remain in the graph until you delete or sync the child separately. See [Nested models](05-nested-models.md).

**Next:** [Nested models →](05-nested-models.md)
