# SPARQL and remote endpoints

TripleModel adds thin helpers around a local `Store.query` / `Store.update`. There is no Python query DSL — write SPARQL (or use [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) for ORM-style queries and remote endpoints).

## When to use which helper

| Goal | Helper |
|------|--------|
| Full resources from a local graph | `construct_models` with **CONSTRUCT** or **DESCRIBE** |
| Tabular SELECT → flat model fields | `select_models` (projection) |
| Filter subjects already in a local graph | `select_models(..., hydrate=True, subject_var="s")` |
| Boolean check | `ask` |
| Mutate a graph in place | `apply_update` then reload with `from_graph` / `construct_models` |
| Remote SPARQL endpoint | **Not in 0.10** — fetch data into a local `Store`, or use SparqlModel |

**SELECT** returns bindings only — not full RDF graphs. Prefer **CONSTRUCT** for graph → `TripleModel` round-trip.

`open_sparql_graph` and `load_sparql` raise `NotImplementedError` in **0.10.0** (pyoxigraph has no built-in remote SPARQL graph). See {doc}`../MIGRATION_0.10`.

## CONSTRUCT on an in-memory graph

```python
from triplemodel import TripleModel, rdf_field
from triplemodel.vocab import FOAF

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")

people = Person.construct_from_sparql(
    graph,
    """
    CONSTRUCT { ?s ?p ?o }
    WHERE { ?s a foaf:Person . ?s ?p ?o . }
    """,
)
```

## Remote data (pattern)

Load RDF from an endpoint or file into a local `Store`, then use the helpers above:

```python
from triplemodel import Store, load_graph

graph = load_graph(source="endpoint-export.nt", format="nt")
people = Person.construct_from_sparql(
    graph,
    "CONSTRUCT { ?s ?p ?o } WHERE { ?s a foaf:Person . ?s ?p ?o }",
)
```

For live SPARQL sessions against remote endpoints, use [SparqlModel](https://github.com/eddiethedean/sqarqlmodel).

## SELECT projection

Map SPARQL variables to model fields (default: variable name = field name):

```python
rows = Person.select_from_sparql(
    graph,
    """
    SELECT ?slug ?name WHERE {
      ?s a foaf:Person .
      ?s foaf:name ?name .
      BIND(REPLACE(STR(?s), "http://example.org/people/", "") AS ?slug)
    }
    """,
)
```

With a subject URI variable, set `subject_var="s"` so `Rdf.id_field` is filled from the IRI (or the full IRI when `IriId` is used).

## Dataset union and named graphs

``run_sparql`` and ``PreparedModelQuery.execute`` forward pyoxigraph dataset options:

```python
from triplemodel import run_sparql

result = run_sparql(
    graph,
    "SELECT ?s WHERE { ?s ?p ?o }",
    use_default_graph_as_union=True,
    named_graphs=["http://example.org/graph/g1"],
    default_graph="http://example.org/graph/default",
)
```

Save or reload result documents with ``parse_query_results`` and ``SparqlResult.serialize(format="sparql-results+json")``.

## ASK

```python
from triplemodel import ask

if Person.ask_sparql(graph, "ASK { ?s a foaf:Person }"):
    ...
```

## SPARQL UPDATE

`apply_update` wraps `graph.update`. In-memory `TripleModel` instances are **not** updated automatically.

```python
from triplemodel import apply_update

apply_update(
    graph,
    """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    DELETE { ?s foaf:age ?age } WHERE { ?s foaf:age ?age }
    """,
    model_cls=Person,
)
person = Person.from_graph(graph, person.subject_uri())
```

For mapped predicates on a known subject, `sync_to_graph` remains the typed alternative; SPARQL UPDATE is for arbitrary graph edits.

## Prepared queries and bindings

```python
from triplemodel import prepare_model_query, init_bindings_from_model

pq = prepare_model_query(Person, "SELECT ?name WHERE { ?s foaf:name ?name . FILTER(?s = ?subj) }")
bindings = init_bindings_from_model(alice, {"subj": "slug"})
result = pq.execute(graph, initBindings=bindings)
```

`run_sparql` (and helpers that call it) bind `Rdf.prefixes` on the **same** `Store` you pass in (`bind_namespaces` with `override=True`). That mutates the graph for serialization and SPARQL prefix resolution.

## Security

`graph.query` may follow `SERVICE` clauses when the underlying engine supports them. Only run trusted queries or restrict network access when loading untrusted RDF.
