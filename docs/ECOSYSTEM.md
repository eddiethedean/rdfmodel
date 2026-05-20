# TripleModel and SparqlModel — separation of responsibilities

Both projects wrap **Pydantic** and **pyoxigraph** (TripleModel 0.10+). They share a maintainer and a long-term direction: **SparqlModel depends on `triplemodel>=0.9,<2`** today; adopt **`>=0.10,<2`** when ready (**SM-7**). **SparqlModel 0.4 (Option A)** makes `SPARQLModel` a **`TripleModel` subclass** — one class, one mapping path. This document is the contract for what each package owns.

**Naming:** PyPI/install name **`triplemodel`**; base class **`TripleModel`**; project title **TripleModel**.

| Doc | Purpose |
|-----|---------|
| [PLAN.md](PLAN.md) | Strategy, priorities, integration gates |
| [ROADMAP.md](ROADMAP.md) | Releases, pyoxigraph matrix, **SM-*** milestones |
| [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) | SparqlModel maintainer guide (copy into SparqlModel repo) |

**SparqlModel maintainers:** start with [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) for module retirement and PR boundaries.

```text
┌──────────────────────────────────────────┐
│  SparqlModel (sparqlmodel)               │
│  ORM · session · queries · stores        │
└────────────────────┬─────────────────────┘
                     │ depends on (shipped >=0.9)
┌────────────────────▼─────────────────────┐
│  triplemodel (PyPI)                      │
│  TripleModel · Pydantic ↔ RDF · I/O      │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│  pyoxigraph · pydantic                   │
└──────────────────────────────────────────┘
```

**Rule:** dependency flows downward only. `triplemodel` must never import `sparqlmodel`.

---

## triplemodel — the mapping layer

**Tagline:** Typed Pydantic models ↔ RDF graphs (terms, triples, files).

**User question it answers:** “How do I turn this Python object into correct triples (and back) without hand-writing every predicate?”

### Owns

| Area | Examples |
|------|----------|
| **Model metadata** | Nested `Rdf` config (`namespace`, `type_uri`, `id_field`), `rdf_field()`, `Predicate` |
| **Subject identity** | `subject_base()`, `id_from_subject_uri()`, `TripleModel.subject_uri()` (encoding, safe prefix matching) |
| **Term conversion** | Python scalars ↔ `URIRef` / `Literal` / XSD datatypes |
| **Graph serialization** | `to_graph`, `from_graph`, `all_from_graph`, `models_to_graph`, low-level helpers |
| **Field ↔ predicate** | Single- and multi-valued fields, nested embedded models (roadmap) |
| **Namespaces** | Prefixes, CURIE expansion, `Graph.bind` integration (roadmap) |
| **Document I/O** | `parse` / `serialize`, formats (Turtle, JSON-LD, …), base URI (roadmap) |
| **Named graphs** | `Dataset`, graph context on models (roadmap) |
| **RDF engine coverage** | Matrix in [ROADMAP.md](ROADMAP.md) for features that map to typed models |

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

### Does not own (delegates to TripleModel, once integrated)

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
| Round-trip a model from an existing `Graph` | **TripleModel** |
| Load/save Turtle, JSON-LD, Trig files | **TripleModel** |
| Shared vocabulary / term conversion bugs fixed once | **TripleModel** |
| `session.put` / `delete` with cascade | **SparqlModel** |
| `Model.field == value` queries | **SparqlModel** |
| SPARQL endpoint over HTTP | **SparqlModel** |
| FastAPI RDF responses | **SparqlModel** |
| Raw `graph.query("SELECT …")` without a DSL | **rdflib** or TripleModel passthrough; not a SparqlModel requirement |

## Triple ownership (0.2+)

**TripleModel** owns **mapped predicates** for a subject: `sync_to_graph` / `mode="replace"` removes prior `(subject, predicate, ?)` triples for predicates declared on the model (plus `rdf:type` when configured), then writes the current field values.

**SparqlModel** owns **session policy** beyond that: cascade to related resources, orphan cleanup when a parent is deleted, and which related IRIs are included in a `put`.

SparqlModel should call `triplemodel.sync_to_graph` (or equivalent) for the resource’s owned triples, then apply its own rules for linked resources.

When **implementing** a feature:

| Touching… | Belongs in |
|-----------|------------|
| “This `str` became the wrong `Literal`” | TripleModel |
| “Re-export dropped a triple on update” | TripleModel (sync/merge) + SparqlModel policy |
| “`!=` filter should mean NOT EXISTS” | SparqlModel compiler |
| “Two parents deleted the same embedded IRI” | SparqlModel cascade rules (may call TripleModel for triple sets) |
| “TriG named graph round-trip” | TripleModel; SparqlModel uses it via session/store |

---

## Public API convergence (target)

Today the two libraries use different surface names; convergence is intentional, not required to be identical.

| Concept | TripleModel | SparqlModel (current) | Notes |
|---------|----------|------------------------|-------|
| Base model | `TripleModel` | `SPARQLModel(TripleModel)` | Option A target **SparqlModel 0.4**; 0.3 uses interim adapter |
| RDF type | `Rdf.type_uri` | `rdf_type` (CURIE) | Unify via prefixes + expansion in TripleModel |
| Predicates | `rdf_field(iri)` | `Field("curie")` | Same metadata; different constructors |
| Subject id | `Rdf.id_field` + `namespace` | `id: IRI` | TripleModel may add explicit `IRI` id field support |
| Prefixes | `Rdf.prefixes` (planned) | `__prefixes__` | Single implementation in TripleModel |
| Export graph | `to_graph()` | via internal graph + `export_model` | SparqlModel calls TripleModel |
| Import graph | `from_graph(g, uri)` | `get` + hydration | SparqlModel adds depth and relationships |

---

## SparqlModel integration status

**Shipped:** `sparqlmodel` requires `triplemodel>=0.9,<2`. Session I/O uses TripleModel `sync_to_graph` / `from_graph` (0.3 via interim `_triple.py` adapter).

**Next (SM-6 / SparqlModel 0.4):** `SPARQLModel(TripleModel)` — delete dynamic adapter; `Field` / `Relationship` as sugar over `rdf_field` / `Predicate`.

SparqlModel-specific behaviour (cascade, query compiler, session, async stores) stays in SparqlModel.

---

## Optional extras (unchanged split)

| Extra | Package |
|-------|---------|
| `triplemodel[shacl]` | TripleModel (rdflib bridge for pyshacl only) |
| `sparqlmodel[fastapi]` | SparqlModel |
| `httpx` remote SPARQL | SparqlModel dev / optional extra |

---

## Summary

- **TripleModel** = **what** the data is in RDF (mapping + files + pyoxigraph-backed graphs).
- **SparqlModel** = **how** an application **uses** that data (session, queries, updates, stores).

Keep TripleModel thin, library-friendly, and stateless. Keep SparqlModel opinionated about persistence and querying. Share one mapping implementation; do not share one public API.
