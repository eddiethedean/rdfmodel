# SPARQL and remote endpoints

TripleModel **0.6** adds thin helpers around rdflib’s `Graph.query`, `Graph.update`, and SPARQL stores. There is no Python query DSL — write SPARQL (or use [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) for ORM-style queries).

## When to use which helper

| Goal | Helper |
|------|--------|
| Full resources from a graph or endpoint | `construct_models` / `load_sparql` with **CONSTRUCT** or **DESCRIBE** |
| Tabular SELECT → flat model fields | `select_models` (projection) |
| Filter subjects already in a local graph | `select_models(..., hydrate=True, subject_var="s")` |
| Boolean check | `ask` |
| Mutate a graph in place | `apply_update` then reload with `from_graph` / `construct_models` |
| Federated `SERVICE` | `open_sparql_graph` + raw `graph.query` (rdflib executes `SERVICE`) |

**SELECT from a remote endpoint** returns bindings only — not full RDF graphs. Prefer **CONSTRUCT** for endpoint → `TripleModel` round-trip.

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

## Remote endpoint (≤10 lines)

```python
people = Person.load_sparql(
    "https://dbpedia.org/sparql",
    """
    CONSTRUCT { ?s ?p ?o } WHERE {
      ?s a <http://xmlns.com/foaf/0.1/Person> .
      ?s <http://xmlns.com/foaf/0.1/name> ?name .
      ?s ?p ?o
    } LIMIT 5
    """,
)
```

Use `read_only=False` and `open_sparql_graph(..., read_only=False)` for `SPARQLUpdateStore` when the endpoint supports SPARQL Update.

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

`run_sparql` (and helpers that call it) bind `Rdf.prefixes` on the **same** `Graph` you pass in (`bind_namespaces` with `override=True`). That mutates the graph for serialization and SPARQL prefix resolution.

On **SPARQLStore**, `initBindings` may behave differently than on an in-memory graph when bindings must appear inside `WHERE`. Pass `use_store_provided=False` to `execute` / `run_sparql` if results look wrong (see [rdflib#1772](https://github.com/RDFLib/rdflib/issues/1772)).

## Security

`graph.query` and remote stores may follow `SERVICE` clauses and fetch URLs. Only run trusted queries or restrict network access (see rdflib security documentation).
