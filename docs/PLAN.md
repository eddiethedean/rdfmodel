# TripleModel project plan

This document is the **strategic plan** for **TripleModel** (PyPI package **`triplemodel`**). [ROADMAP.md](ROADMAP.md) tracks **releases and rdflib parity** (including **SM-*** SparqlModel integration milestones); [ECOSYSTEM.md](ECOSYSTEM.md) defines boundaries with [SparqlModel](https://github.com/eddiethedean/sqarqlmodel). SparqlModel maintainers should copy [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) into that repo.

---

## Current status (0.4.1)

**Released (beta) on PyPI:** Everything in **0.4.0** (file `parse` / `serialize`, dispatch, inverse predicates, optional SHACL) plus **0.4.1** linked-data ergonomics: `load_graph` / `load_models` / `load_models_from_graph`, `Rdf.instance_of`, `ref_field`, XSD `gYear` / `gMonth` / `gMonthDay`, and predicate mapping validation at class definition. See {doc}`changelog` and {doc}`guides/11-real-world-patterns`.

**Validated in-repo:** [examples/realworld](https://github.com/eddiethedean/triplemodel/blob/main/examples/realworld/README.md) — Nobel, DCAT, Wikidata capitals, Schema.org NGOs (offline TTL + CI). SparqlModel may pin `triplemodel>=0.4,<0.5` for SM-3 experiments.

**Not yet shipped:** Dataset/named graphs (**0.5**); SPARQL helpers (**0.6**).

**Next focus:** **0.5.0** — `to_dataset` / named graph contexts on `Rdf`.

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
- Term conversion (XSD, lang tags, custom datatypes; **0.4.1:** `gYear` / partial dates)
- Stateless graph I/O and sync (add / remove / merge policies)
- Document formats via rdflib (`parse` / `serialize`)
- **Linked-data ergonomics (0.4.1):** one-parse multi-class load, `Rdf.instance_of` for non-`rdf:type` vocabularies, predicate-URI validation, URI FK → nested model hydration
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

## Real-world integration lessons (0.4 evaluation)

Exercises in `examples/realworld/` showed where TripleModel is already **Pythonic** (typed fields, `parse_file`, `set` keywords, `models_to_graph`, prefixes) and where **setup cost** dominates (Wikidata `wdt:P31` vs `rdf:type`, repeated `parse_file` per class, flat URI foreign keys, XSD `gYear`, predicate URI mistakes).

| Lesson | User pain today | Planned response | Release |
|--------|-----------------|------------------|---------|
| One file, many classes | Nobel/DCAT need three `parse_file` calls on the same TTL | `load_models(graph, *classes)` | **0.4.1** (done) |
| Wikidata typing | Manual QID lists + `from_graph` per subject | `Rdf.instance_of` + discovery | **0.4.1** (done) |
| Cross-resource links | `country: str` + hand-built dict | `ref_field` hydration | **0.4.1** (done) |
| Partial dates | `foundingDate` forced to `str` | XSD `gYear` in literal registry | **0.4.1** (done) |
| Mapping footguns | `RDFS_LABEL` = namespace base breaks import | Class-definition validation on predicate IRIs | **0.4.1** (done) |
| Object graphs in Python | Laureate and Prize are disconnected models | Nested embed + cookbook (inverse optional) | **0.4.1** docs; richer **0.7** CBD |
| Dogfooding | Examples still teach workarounds after APIs ship | Refactor `examples/realworld/` (+ snippets) per feature; extend CI tests | **0.4.1** (done) |
| Live endpoint slices | CONSTRUCT refresh script is ad hoc | `construct_models` + documented refresh recipe | **0.6** |
| App-level joins | Country labels need manual joins | `hydrate_refs` / batch load from graph | **0.7** |

**Documentation (no semver bump):** Promote real-world patterns into the cookbook; keep `examples/realworld/DATA_SOURCES.md` as the provenance index.

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
| **Real-world ergonomics** | 0.4.1 | Multi-class load, Wikidata typing, XSD dates, mapping validation |
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
3. **Real-world ergonomics (0.4.1)** — multi-class load, property-based typing, mapping validation, partial XSD dates (unblocks LOD examples without Dataset).
4. **rdflib matrix** — per [ROADMAP.md](ROADMAP.md) (0.5+ Dataset, 0.6 SPARQL passthrough).
5. **Ergonomic extras** — codegen, `hydrate_refs`, advanced SPARQL helpers.
6. **Never** — session/query compiler in TripleModel core.

---

## Documentation map

| Document | Audience |
|----------|----------|
| [README on GitHub](https://github.com/eddiethedean/triplemodel/blob/main/README.md) | Library users |
| [ROADMAP.md](ROADMAP.md) | Releases, rdflib matrix |
| [PLAN.md](PLAN.md) | Strategy (this file) |
| [ECOSYSTEM.md](ECOSYSTEM.md) | triplemodel ↔ SparqlModel boundaries |
| [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) | Copy into SparqlModel repo |

---

## Success metrics

- **0.2:** SparqlModel can prototype `triplemodel` for `model_to_graph` / load without losing `put` semantics.
- **0.4:** Load/save Turtle/JSON-LD without SparqlModel-only parsers.
- **0.4.1:** Nobel + DCAT examples use a single graph load; Wikidata capitals avoid hard-coded QID loops; Schema.org `gYear` imports without `str` workarounds; invalid `rdf_predicate` fails at class definition; **in-repo examples updated** to match each shipped API (`examples/realworld/`, relevant snippets, `test_realworld_examples.py`).
- **0.9:** SparqlModel pins released `triplemodel`; duplicate term code removed from SparqlModel.
- **1.0:** Downstream apps choose **triplemodel** for pipelines and **sparqlmodel** for apps — clear docs, no overlap confusion.
