# RDFModel and SparqlModel — separation of responsibilities

Both projects wrap **Pydantic** and **rdflib**. They share a maintainer and a long-term direction: **SparqlModel will depend on RDFModel** once the graph-mapping APIs are aligned. Until then, this document is the contract for what each package owns.

| Doc | Purpose |
|-----|---------|
| [PLAN.md](PLAN.md) | Strategy, priorities, integration gates |
| [ROADMAP.md](ROADMAP.md) | Releases, rdflib matrix, **SM-*** milestones |
| [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) | SparqlModel maintainer guide (copy into SparqlModel repo) |

**SparqlModel maintainers:** start with [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) for module retirement and PR boundaries.

```text
┌──────────────────────────────────────────┐
│  SparqlModel (sparqlmodel)               │
│  ORM · session · queries · stores        │
└────────────────────┬─────────────────────┘
                     │ depends on (future)
┌────────────────────▼─────────────────────┐
│  RDFModel (rdfmodel)                     │
│  Pydantic ↔ RDF mapping · graph I/O      │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│  rdflib · pydantic                       │
└──────────────────────────────────────────┘
```

**Rule:** dependency flows downward only. RDFModel must never import SparqlModel.

---

## RDFModel — the mapping layer

**Tagline:** Typed Pydantic models ↔ RDF graphs (terms, triples, files).

**User question it answers:** “How do I turn this Python object into correct triples (and back) without hand-writing every predicate?”

### Owns

| Area | Examples |
|------|----------|
| **Model metadata** | Nested `Rdf` config (`namespace`, `type_uri`, `id_field`), `rdf_field()`, `Predicate` |
| **Subject identity** | `subject_base()`, `id_from_subject_uri()`, `RdfModel.subject_uri()` (encoding, safe prefix matching) |
| **Term conversion** | Python scalars ↔ `URIRef` / `Literal` / XSD datatypes |
| **Graph serialization** | `to_graph`, `from_graph`, `all_from_graph`, `models_to_graph`, low-level helpers |
| **Field ↔ predicate** | Single- and multi-valued fields, nested embedded models (roadmap) |
| **Namespaces** | Prefixes, CURIE expansion, `Graph.bind` integration (roadmap) |
| **Document I/O** | `parse` / `serialize`, formats (Turtle, JSON-LD, …), base URI (roadmap) |
| **Named graphs** | `Dataset`, graph context on models (roadmap) |
| **rdflib parity** | Coverage matrix in [ROADMAP.md](ROADMAP.md) for features that map to typed models |

### Does not own

- Sessions, identity maps, or unit-of-work lifecycle
- Python query expressions or SPARQL compilation
- `put` / `delete` cascade or orphan cleanup policies
- HTTP SPARQL endpoints or store plugins (except thin passthrough where noted in the matrix)
- FastAPI or web framework integration
- Application-level “repository” patterns

### Typical callers

- ETL and data pipelines
- Tests and fixtures (round-trip assertions)
- Libraries (e.g. **SparqlModel**) that need stable graph mapping
- Scripts that load a file → Pydantic → transform → serialize

### API shape

**Stateless and explicit:** you pass a `Graph` (or get one back). No hidden global graph.

```python
person = Person(slug="alice", name="Alice")
g = person.to_graph()
restored = Person.from_graph(g, person.subject_uri())
```

---

## SparqlModel — the ORM layer

**Tagline:** SPARQL-native object graph mapper for triple stores.

**Repo:** [github.com/eddiethedean/sqarqlmodel](https://github.com/eddiethedean/sqarqlmodel) · PyPI: `sparqlmodel`

**User question it answers:** “How do I build an app that CRUDs and queries RDF data like a small database?”

### Owns

| Area | Examples |
|------|----------|
| **Session** | `SPARQLSession` — `add`, `put`, `delete`, `get` |
| **Store abstraction** | `MemoryStore`, future `HttpStore`, pluggable backends |
| **Query DSL** | `session.query(Person).where(Person.name == "x")` |
| **SPARQL compiler** | Python comparisons → SPARQL WHERE (and extensions: OR, joins, …) |
| **Hydration** | Load by IRI with relationship `depth` |
| **Relationship semantics** | Embedded models vs `IRI` references; cascade on `put`/`delete` |
| **Persistence policy** | Owned triples, orphan cleanup, `add` vs `put` behaviour |
| **App integration** | FastAPI extras, remote SPARQL (roadmap) |
| **Raw SPARQL** | `session.execute(sparql)` with prefix injection |

### Does not own (delegates to RDFModel, once integrated)

- Canonical `python_to_term` / `term_to_python`
- Predicate metadata resolution and duplicate-predicate rules
- File format registry and `Graph.parse` / `serialize` wrappers
- Subject IRI rules shared across projects
- Named-graph quad I/O primitives

### Typical callers

- Web APIs and services
- Interactive apps with filters and updates
- Prototypes against in-memory or remote SPARQL endpoints

### API shape

**Stateful:** a session holds a store/graph; queries and writes go through the session.

```python
session = SPARQLSession()
session.put(person)
found = session.query(Person).where(Person.name == "Odos").first()
```

---

## Decision guide

When choosing a package (or deciding where a feature belongs):

| If you need… | Package |
|--------------|---------|
| Round-trip a model from an existing `Graph` | **RDFModel** |
| Load/save Turtle, JSON-LD, Trig files | **RDFModel** |
| Shared vocabulary / term conversion bugs fixed once | **RDFModel** |
| `session.put` / `delete` with cascade | **SparqlModel** |
| `Model.field == value` queries | **SparqlModel** |
| SPARQL endpoint over HTTP | **SparqlModel** |
| FastAPI RDF responses | **SparqlModel** |
| Raw `graph.query("SELECT …")` without a DSL | **rdflib** or RDFModel passthrough; not a SparqlModel requirement |

When **implementing** a feature:

| Touching… | Belongs in |
|-----------|------------|
| “This `str` became the wrong `Literal`” | RDFModel |
| “Re-export dropped a triple on update” | RDFModel (sync/merge) + SparqlModel policy |
| “`!=` filter should mean NOT EXISTS” | SparqlModel compiler |
| “Two parents deleted the same embedded IRI” | SparqlModel cascade rules (may call RDFModel for triple sets) |
| “TriG named graph round-trip” | RDFModel; SparqlModel uses it via session/store |

---

## Public API convergence (target)

Today the two libraries use different surface names; convergence is intentional, not required to be identical.

| Concept | RDFModel | SparqlModel (current) | Notes |
|---------|----------|------------------------|-------|
| Base model | `RdfModel` | `SPARQLModel` | SparqlModel may subclass or compose `RdfModel` later |
| RDF type | `Rdf.type_uri` | `rdf_type` (CURIE) | Unify via prefixes + expansion in RDFModel |
| Predicates | `rdf_field(iri)` | `Field("curie")` | Same metadata; different constructors |
| Subject id | `Rdf.id_field` + `namespace` | `id: IRI` | RDFModel may add explicit `IRI` id field support |
| Prefixes | `Rdf.prefixes` (planned) | `__prefixes__` | Single implementation in RDFModel |
| Export graph | `to_graph()` | via internal graph + `export_model` | SparqlModel calls RDFModel |
| Import graph | `from_graph(g, uri)` | `get` + hydration | SparqlModel adds depth and relationships |

---

## RDFModel APIs SparqlModel needs before a hard dependency

Track these on the RDFModel roadmap; SparqlModel should not fork duplicate logic once they exist:

1. **0.2** — Multi-valued fields; nested embedded models; **remove/replace** triples on sync; namespace/`bind`; merge policies.
2. **0.3** — Blank nodes and RDF lists (if SparqlModel keeps embedded graphs).
3. **0.4** — `parse` / `serialize` and base URI.
4. **0.5** — `Dataset` / named graphs (if SparqlModel names contexts per model).

SparqlModel-specific behaviour (cascade, query compiler, session) stays in SparqlModel.

---

## Optional extras (unchanged split)

| Extra | Package |
|-------|---------|
| `rdfmodel[shacl]` | RDFModel |
| `rdfmodel[sqlalchemy]`, `[berkeleydb]` | RDFModel (store backends for graphs) |
| `sparqlmodel[fastapi]` | SparqlModel |
| `httpx` remote SPARQL | SparqlModel dev / optional extra |

---

## Summary

- **RDFModel** = **what** the data is in RDF (mapping + files + rdflib parity for models).
- **SparqlModel** = **how** an application **uses** that data (session, queries, updates, stores).

Keep RDFModel thin, library-friendly, and stateless. Keep SparqlModel opinionated about persistence and querying. Share one mapping implementation; do not share one public API.
