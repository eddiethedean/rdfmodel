# TripleModel project plan

This document is the **strategic plan** for **TripleModel** (PyPI package **`triplemodel`**). [ROADMAP.md](ROADMAP.md) tracks **releases and rdflib parity** (including **SM-*** SparqlModel integration milestones); [ECOSYSTEM.md](ECOSYSTEM.md) defines boundaries with [SparqlModel](https://github.com/eddiethedean/sqarqlmodel). SparqlModel maintainers should copy [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) into that repo.

---

## Current status (0.2.0)

**Released (alpha) on PyPI:** Multi-value `list`/`set` fields, nested `TripleModel` embed (`iri`/`bnode`), `sync_to_graph` with `add`/`replace`/`patch`, `Rdf.prefixes` + CURIE expansion, `triplemodel.vocab`, literal registry, and graph helpers. SparqlModel may pin `triplemodel>=0.2,<0.3` for SM-1 experiments. See [CHANGELOG.md](../CHANGELOG.md).

**Not yet shipped:** File parse/serialize (**0.4**), RDF lists and full blank-node strategy (**0.3**), Dataset/named graphs (**0.5**).

**Next focus:** **0.3.0** — language tags, RDF lists, blank-node hardening; then **0.4** file I/O.

---

## Mission

**TripleModel** is the shared **typed Pydantic ↔ RDF mapping** library for the ecosystem: correct triples from typed models and rdflib feature coverage (file interchange from **0.4**) — without application session or query machinery.

**Not the mission:** ORM-style persistence, Python-to-SPARQL compilers, HTTP stores, or web frameworks. That is **SparqlModel**.

---

## Stack and dependency rule

```text
sparqlmodel  →  triplemodel  →  rdflib, pydantic
                  ↑
            (never imports sparqlmodel)
```

| Layer | Package | Stateful? |
|-------|---------|-----------|
| Application ORM | `sparqlmodel` | Yes (`SPARQLSession`) |
| Mapping / I/O | `triplemodel` | No (explicit `Graph` in/out) |
| RDF engine | `rdflib` | Varies |

---

## Design principles

1. **Library-first** — usable from ETL, tests, and SparqlModel without a global session.
2. **Orchestrate rdflib** — do not reimplement parsers, stores, or SPARQL engines.
3. **One mapping implementation** — term conversion and subject-IRI rules live here once; downstream packages must not fork them.
4. **Explicit over magic** — `to_graph` / `from_graph` behavior is documented; merge and null semantics are testable.
5. **Optional heaviness** — SHACL, SQLAlchemy/BerkeleyDB stores, JSON-LD extras are install extras, not core deps.
6. **Stable mapping before ORM sugar** — prioritize releases that unblock SparqlModel’s `triplemodel` dependency over duplicating SparqlModel features in TripleModel.

---

## Core dependencies

| Package | Role |
|---------|------|
| `pydantic` | Model validation and field metadata |
| `rdflib` | Graphs, terms, parse/serialize, SPARQL passthrough |
| `typing-extensions` | `Self` and typing on Python 3.10 |

Runtime core stays **pydantic + rdflib + typing-extensions**. Everything else is optional extras or dev tooling.

---

## What TripleModel builds (in scope)

- Field ↔ predicate mapping (`rdf_field`, `Predicate`, future CURIE/`Rdf.prefixes`)
- Subject identity (namespace + id, percent-encoding, safe import)
- Term conversion (XSD, lang tags, custom datatypes)
- Stateless graph I/O and sync (add / remove / merge policies)
- Document formats via rdflib (`parse` / `serialize`)
- Named graphs (`Dataset`) where models need contexts
- Thin SPARQL **passthrough** (`graph.query`, optional helpers) — not a Python query DSL
- Vocabulary helpers (`triplemodel.vocab`)
- Stable mapping API for **SparqlModel** to prototype against from **0.2** (SM-1); semver pin at **0.9–1.0** (SM-5)

---

## What TripleModel does not build (out of scope)

See also [ROADMAP.md § Explicitly out of scope](ROADMAP.md#explicitly-out-of-scope-even-pre-10).

| Area | Owner |
|------|--------|
| `SPARQLSession`, `put`/`delete` cascade, orphan cleanup | SparqlModel |
| Python `Model.field == x` query DSL | SparqlModel |
| SPARQL compiler (WHERE generation from expressions) | SparqlModel |
| Hydration depth and relationship loading policy | SparqlModel |
| `HttpStore`, FastAPI, identity map | SparqlModel |
| Full OWL reasoning, path algebra, HTML scraping | Other tools / rdflib direct |

TripleModel **may** add `select_models`-style helpers in 0.6 for users who want SPARQL without SparqlModel; SparqlModel remains the home for ergonomic app queries.

---

## SparqlModel integration strategy

SparqlModel today duplicates mapping logic (`graph.py`, `fields.py`, `serializers.py`). The plan is to **converge implementation**, not merge public APIs.

### Integration gates (when SparqlModel should pin `triplemodel`)

| triplemodel release | Capability SparqlModel needs | SparqlModel action |
|------------------|------------------------------|-------------------|
| **0.2** | Multi-value fields; nested models; **sync/remove** on re-export; namespaces/`bind`; merge policies | Replace core of `graph.py` export/import; keep cascade in session |
| **0.3** | Blank nodes / RDF lists (if embedding retained) | Align hydration with TripleModel loaders |
| **0.4** | `parse` / `serialize`, base URI | Thin `serializers.py` → TripleModel |
| **0.5** | `Dataset` / named graphs (if models use `@graph`) | Store layer uses TripleModel dataset helpers |
| **≥0.9** | API freeze, `py.typed`, documented semver | `sparqlmodel` depends on `triplemodel~=1.0` (or `>=0.9,<2`) |

Until **0.2** sync/remove ships, SparqlModel should **not** declare a required `triplemodel` dependency (local dev pin only).

### API convergence (internal, not necessarily public)

| SparqlModel (public) | TripleModel (implementation) |
|----------------------|---------------------------|
| `SPARQLModel` | Compose / subclass `TripleModel` |
| `Field("schema:name")` | Predicate metadata + CURIE expand |
| `__prefixes__` | `Rdf.prefixes` |
| `id: IRI` | Explicit IRI id or `id_field` + namespace |
| `session.put` | TripleModel `sync_to_graph` + SparqlModel cascade |

### Contract tests (future)

- Cross-repo or published-wheel tests: SparqlModel `put` triple set equals TripleModel sync + cascade rules.
- TripleModel owns literal/subject bugs; SparqlModel owns compiler/session bugs.

---

## Release philosophy

| Phase | Versions | Goal |
|-------|----------|------|
| **Foundation** | 0.1.x | Flat round-trip, CI, typing, docs |
| **Model-complete** | 0.2–0.3 | Fields, sync, namespaces, literals, blanks, lists — **SparqlModel gate** |
| **Document I/O** | 0.4 | Files and optional SHACL |
| **Graph contexts** | 0.5 | Dataset / Trig |
| **Query passthrough** | 0.6 | rdflib SPARQL helpers (not ORM) |
| **Algorithms** | 0.7 | CBD, isomorphism, RDFS import helpers |
| **Scale** | 0.8 | Store extras, batch import |
| **Freeze** | 0.9 | Matrix audit, API stable for downstream |
| **Production** | 1.0 | Governance, security docs, no new surface |

Patch releases: bugfixes only. Minors: features. Majors: breaking API after 1.0.

---

## Priority order (when trade-offs arise)

1. **Correctness** — subject IRIs, literals, import/export symmetry.
2. **SparqlModel gate items** — sync/remove (0.2), namespaces (0.2), nested models (0.2).
3. **rdflib matrix** — per [ROADMAP.md](ROADMAP.md).
4. **Ergonomic extras** — codegen, advanced SPARQL helpers.
5. **Never** — session/query compiler in TripleModel core.

---

## Documentation map

| Document | Audience |
|----------|----------|
| [README.md](../README.md) | Library users |
| [ROADMAP.md](ROADMAP.md) | Releases, rdflib matrix |
| [PLAN.md](PLAN.md) | Strategy (this file) |
| [ECOSYSTEM.md](ECOSYSTEM.md) | triplemodel ↔ SparqlModel boundaries |
| [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) | Copy into SparqlModel repo |

---

## Success metrics

- **0.2:** SparqlModel can prototype `triplemodel` for `model_to_graph` / load without losing `put` semantics.
- **0.4:** Load/save Turtle/JSON-LD without SparqlModel-only parsers.
- **0.9:** SparqlModel pins released `triplemodel`; duplicate term code removed from SparqlModel.
- **1.0:** Downstream apps choose **triplemodel** for pipelines and **sparqlmodel** for apps — clear docs, no overlap confusion.
