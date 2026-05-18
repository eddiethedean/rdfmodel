# Graph algorithms and RDFS

TripleModel **0.7** adds thin wrappers over rdflib graph operations for testing, subgraph extraction, RDFS-aware dispatch, and batch reference hydration. These helpers are **not** a reasoner or ORM — they complement `from_graph` / `graph_to_model_dispatch`.

## When to use which helper

| Goal | Helper |
|------|--------|
| Assert two graphs match in tests | `graphs_equal`, `graph_diff` |
| Compare two model instances after sync | `model_diff` |
| Extract a resource’s bounded description | `cbd_graph`, `cbd_model`, `Person.cbd(...)` |
| Pick `Agent` vs `Person` when `rdfs:subClassOf` is in the graph | `graph_to_model_dispatch` (subclass-aware `resolve_model_class`) |
| Batch-load shared ref targets (e.g. countries) | `hydrate_refs`, `model_join` |
| Walk `rdfs:subClassOf` or transitive predicates | `subclass_uris`, `transitive_objects`, `transitive_subjects` |
| Central prefix + type registry | `VocabularyRegistry` |

## Graph comparison

```python
from triplemodel import graphs_equal, graph_diff, model_diff

assert graphs_equal(g1, g2)
diff = graph_diff(g1, g2)
assert not diff.only_in_a and not diff.only_in_b

changes = model_diff(alice, bob, graph=g)  # optional predicate-level diff
```

`graphs_equal(..., normalize_bnodes=True)` skolemizes blank nodes before `Graph.isomorphic()` — useful when graphs were built separately. For graphs parsed in two `parse()` calls, blank-node identity will not match; see {doc}`08-working-with-graphs` and **Safe graph merge** below.

## Concise bounded description (CBD)

rdflib’s `Graph.cbd` returns the predicate closure around a subject. TripleModel wraps it for import:

```python
from triplemodel import TripleModel, cbd_model

person = cbd_model(Person, graph, subject_uri)
# or
person = Person.cbd(graph, subject_uri)
```

CBD returns a **subgraph**, not a fully flattened tree. Nested `TripleModel` fields still hydrate via `embed` / `ref_field` when you call `from_graph` on the CBD graph. For a Python object graph, prefer `Rdf.embed = "bnode"` (see {doc}`05-nested-models`).

Run `examples/exit_criteria_07.py` for CBD + subclass dispatch.

## RDFS subclass dispatch

Register both superclass and subclass models. When a subject is typed with a subclass IRI, dispatch picks the **most specific** registered class using `rdfs:subClassOf` in the graph:

```python
from triplemodel import graph_to_model_dispatch, register_rdf_resource

register_rdf_resource(Person)
register_rdf_resource(Agent)

agent = graph_to_model_dispatch(graph, alice_uri)
```

`Rdf.resolve_subclass` (default `True` on `RdfConfig`) controls this behavior. Disable with `use_subclass=False` on `resolve_model_class_with_rdfs` for exact `rdf:type` matching only.

## Batch reference hydration

`ref_field` hydrates one nested model per instance per reference — correct but slow when many rows share the same country URI. After a lightweight import:

```python
from triplemodel import hydrate_refs

cities = City.all_from_graph(graph)  # partial country refs
cities = hydrate_refs(cities, graph, "country")
```

For `ResourceRef` fields, pass `spec={"country": Country}`. `model_join(cities, graph, {"country": Country})` is an alias.

See `examples/realworld/wikidata_capitals.py` for the Wikidata capitals pattern.

## Transitive import (optional)

Mark a `set` field as transitive to expand multi-hop object URIs on **import only** (export still writes direct edges):

```python
from triplemodel import rdf_field, Transitive
from typing import Annotated

parts: set[str] = rdf_field("ex:partOf", default_factory=set, transitive=True)
# or Annotated[set[str], Transitive()]
```

## Vocabulary registry

```python
from triplemodel import VocabularyRegistry

reg = VocabularyRegistry()
reg.register(Person)
reg.register(Organization)
reg.bind_vocab(graph)
cls = reg.model_for_subject(graph, subject)
```

This wraps `register_rdf_resource` and the internal `type_uri` index for documented multi-class setups.

## Safe graph merge

`merge_graphs` combines triples as-is. Blank nodes from **separate** `parse()` calls are different nodes even when structurally identical. Prefer:

- One `parse()` / one `load_graph` for combined data, or
- Skolemization / stable blank-node policy via `Rdf.blank_node_policy`, or
- `graphs_equal(..., normalize_bnodes=True)` only for testing.

Details: {doc}`08-working-with-graphs`.

## Catalog patterns (cookbook)

No new APIs — reuse existing `examples/realworld/`:

| Pattern | Example |
|---------|---------|
| DCAT portal graphs | `examples/realworld/dcat_portal.py` |
| `Schema.org` NGO registry | `examples/realworld/schema_org_ngo.py` |
| Nobel / biographical LOD | `examples/realworld/nobel_laureates.py` |

See {doc}`11-real-world-patterns` for `load_models`, `ref_field`, and Wikidata typing.

## Deferred: OWL/RDFS codegen CLI

Experimental **codegen** (OWL/RDFS → stub `TripleModel` classes) is planned for **0.8+**, not 0.7.0.
