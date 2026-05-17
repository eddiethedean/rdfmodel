# RDFModel roadmap

Roadmap for **RDFModel** (Python package: `rdfmodel`). This document tracks planned releases from the current **0.1.0** alpha through a stable **1.0.0**. Versions follow [Semantic Versioning](https://semver.org/): breaking API changes only on major releases; minors add features; patches fix bugs.

**Vision:** Make RDF a natural persistence and interchange layer for Pydantic-shaped domain models — typed in Python, portable as triples, without bespoke mapping code per project.

**Pre-1.0 commitment:** Every **0.x** release adds capability until RDFModel exposes all [rdflib](https://github.com/RDFLib/rdflib) features that sensibly map to typed Pydantic models. We wrap and orchestrate rdflib; we do not reimplement parsers, stores, or SPARQL. **1.0.0** is API stability and production hardening — not a catch-up release for rdflib parity.

---

## rdflib coverage matrix

Status key: **done** (0.1.0) · **planned** (target version) · **partial** · **out of scope**

| rdflib area | Capability | RDFModel surface (planned) | Ver |
|-------------|------------|----------------------------|-----|
| **Terms** | `URIRef`, `Literal`, XSD datatypes | `python_to_term` / `term_to_python` | 0.1 |
| | `BNode`, anonymous subjects/objects | `Rdf.blank_node` strategy, skolemize on export | 0.3 |
| | Language tags (`Literal.lang`) | `LangString`, `Annotated[..., Lang("en")]` | 0.3 |
| | Custom / unknown datatypes | pluggable `Literal` converters | 0.2 |
| | `Variable` | SPARQL result binding only (not model fields) | 0.6 |
| | RDF-star / quoted triples (`QuotedGraph`) | deferred unless rdflib 7 usage is stable | TBD |
| **Graph API** | `add` / `remove` / `set` / triple iterators | `to_graph`, merge policies, graph helpers | 0.1–0.2 |
| | `bind`, `namespaces`, `compute_qname`, `qname` | `Rdf.prefixes`, `Namespace` helpers on models | 0.2 |
| | `parse` / `serialize` (all registered formats) | `RdfModel.parse`, `.serialize`, `load_*` / `dump_*` | 0.4 |
| | `query` (SELECT, ASK, CONSTRUCT, DESCRIBE) | `select_models`, `ask`, `construct_models` | 0.6 |
| | SPARQL UPDATE | `graph.update` wrapper + model-aware patches | 0.6 |
| | `cbd` (concise bounded description) | `model.cbd(graph)` → nested sub-model | 0.7 |
| | `skolemize` / `de_skolemize` | export/import options on `to_graph` / `from_graph` | 0.3 |
| | `isomorphic` / graph comparison | `graphs_equal` for tests and migrations | 0.7 |
| | `transitiveClosure`, `transitive_*` | optional helpers for hierarchy fields | 0.7 |
| | `collection` (RDF lists) | `list[T]` ↔ `rdf:List` | 0.3 |
| | `resource()` | lazy `ResourceRef` fields | 0.3 |
| | `Dataset` / named graphs | `@graph` context on `Rdf`, `Dataset` I/O | 0.5 |
| | `ConjunctiveGraph` | use `Dataset` only (rdflib deprecation) | 0.5 |
| **Formats** | Turtle, Trig, N-Triples, N-Quads | `serialize(format=...)` | 0.4 |
| | RDF/XML, N3 | same | 0.4 |
| | JSON-LD | same; optional `jsonld` extra if needed | 0.4 |
| | TriG, TriX, HexTuples, longTurtle | same where rdflib registers parser/serializer | 0.4 |
| | Microdata, RDFa | **out of scope** (HTML scraping, not domain modeling) | — |
| **Stores** | Memory (`default`, `memory`) | default `Graph()` / `Dataset()` | 0.1 |
| | Remote SPARQL (`sparql` store) | `RdfModel.load_sparql(url, query)` | 0.6 |
| | BerkeleyDB, SQLAlchemy | optional extras `rdfmodel[berkeleydb]`, `[sqlalchemy]` | 0.8 |
| | Store transactions (`commit` / `rollback` / `open`) | passthrough when backing store supports | 0.8 |
| **Namespace** | `Namespace`, `DefinedNamespace`, bundled vocabs | `from rdfmodel.vocab import FOAF, SKOS, ...` | 0.2 |
| **Plugins** | Register custom Parser/Serializer/Store | `rdfmodel.plugins.register_*` passthrough | 0.9 |
| **SHACL** | Validation (rdflib ecosystem / pyshacl) | optional `rdfmodel[shacl]` pre-export hook | 0.4 |
| **contrib** | GraphDB, RDF4J clients | **out of scope** for core; link in cookbook only | — |
| **Tools** | `rdflib.tools` CLI (csv2rdf, etc.) | **out of scope** (use rdflib directly) | — |
| **Paths** | Path algebra | **out of scope** (graph traversal, not ORM) | — |

Before **1.0.0**, the matrix above must be **done** or explicitly **out of scope** with rationale in this file — no silent gaps.

---

## 0.1.0 — Foundation (current)

**Status:** Released (alpha)

| Area | Delivered |
|------|-----------|
| Core | `RdfModel` base, `Rdf` config class, `rdf_field()` / `Predicate` |
| Graph I/O | `to_graph()`, `from_graph()`, `all_from_graph()`, `models_to_graph()` |
| Terms | XSD scalars; IRI-like `str` → `URIRef` |
| Identity | Subject IRI from `Rdf.namespace` + `Rdf.id_field`; explicit `uri=` override |
| Store | In-memory `Graph` only |

**rdflib parity:** minimal `Graph.add` path via serialization; most of the matrix still open.

---

## 0.2.0 — Terms, fields, and namespaces

**Theme:** Everything needed for ordinary RDF-shaped Pydantic models on a single default graph.

- [ ] **Multi-valued fields** — `list[T]`, `set[T]` ↔ multiple objects per predicate
- [ ] **Nested `RdfModel`** — blank node or named IRI embedding (configurable)
- [ ] **Optional & null semantics** — omit vs explicit empty documented and tested
- [ ] **Custom `Literal` datatypes** — register converters (`Decimal`, `UUID`, `Enum`, …)
- [ ] **Namespace helpers** — `Namespace`, CURIE expansion, `Rdf.prefixes` → `Graph.bind`
- [ ] **Graph merge policies** — replace / patch / only-own-triples when writing into existing `Graph`
- [ ] **Graph iterator helpers** — thin wrappers over `subjects` / `objects` / `predicate_objects` scoped to a model URI

**Exit criteria:** FOAF `Person` with multiple `nick` values and embedded `mbox` round-trips; prefixes appear in serialized Turtle.

---

## 0.3.0 — Literals, blanks, lists, and identity

**Theme:** Full rdflib **term** expressiveness for model fields.

- [ ] **`LangString` / per-language fields** — `Literal.lang` round-trip
- [ ] **Arbitrary datatype literals** — preserve unknown datatype URIs via registry
- [ ] **Blank nodes** — import/export; optional `skolemize` / `de_skolemize` on `to_graph` / `from_graph`
- [ ] **RDF collections** — `list[T]` ↔ `rdf:List` via `Graph.collection`
- [ ] **`ResourceRef`** — IRI-only field resolved through `Graph.resource`
- [ ] **BNode stability** — document when IDs are stable vs session-scoped

**Exit criteria:** Dublin Core `title` with language tags; blank-node `Address`; RDF list of `nick` values all round-trip.

---

## 0.4.0 — Parsing, serialization, and validation

**Theme:** All rdflib **syntaxes** that make sense for documents (not HTML).

- [ ] **`RdfModel.parse` / `.serialize`** — delegate to `Graph.parse` / `Graph.serialize`
- [ ] **Format support** — Turtle, Trig, N-Triples, N-Quads, RDF/XML, N3, JSON-LD, TriX, HexTuples, longTurtle (each format rdflib registers in CI)
- [ ] **`parse_file` / `parse_url`** — stream from path or URL into `list[RdfModel]`
- [ ] **JSON-LD context** — optional `@context` on `Rdf` class for compaction
- [ ] **SHACL (optional extra)** — validate before `to_graph()` via pyshacl or equivalent
- [ ] **Inverse predicates** — `owl:inverseOf` pairs for import/export symmetry
- [ ] **Subclass dispatch** — multiple `type_uri`; import picks most specific registered model

**Exit criteria:** Same `Person` instance equivalent from Turtle file, JSON-LD string, and in-memory `Graph`; invalid data fails SHACL when extra installed.

---

## 0.5.0 — Datasets and named graphs

**Theme:** rdflib **Dataset** (replacing deprecated `ConjunctiveGraph`).

- [ ] **`Rdf.graph_iri` / `@graph`** — map model class or instance to a named graph IRI
- [ ] **`to_dataset` / `from_dataset`** — serialize models into correct named graphs
- [ ] **`all_from_dataset`** — load by `rdf:type` within a graph context
- [ ] **Default graph vs union** — document query/import behavior (union default in rdflib)
- [ ] **Trig / N-Quads round-trip** — named graph boundaries preserved

**Exit criteria:** Two model types in different named graphs round-trip through Trig without collision.

---

## 0.6.0 — SPARQL and remote graphs

**Theme:** rdflib **query** and **SPARQL store** integration.

- [ ] **`select_models`** — SPARQL SELECT → `list[RdfModel]` with variable→field mapping
- [ ] **`construct_models`** — CONSTRUCT/DESCRIBE → target model class
- [ ] **`ask`** — thin wrapper returning `bool`
- [ ] **SPARQL UPDATE** — `apply_update(graph, query)` with documented interaction with models
- [ ] **`load_sparql`** — construct store from endpoint URL + query into models
- [ ] **Prepared queries** — cache `Graph.query` with namespace bindings from model vocab
- [ ] **Result types** — handle all rdflib result kinds (bindings, boolean, graph, JSON)

**Exit criteria:** Load `Person` rows from a public SPARQL endpoint in ≤10 lines; UPDATE example in docs.

---

## 0.7.0 — Graph algorithms and RDFS

**Theme:** rdflib **graph operations** that help modeling, not replace reasoners.

- [ ] **`cbd` wrapper** — extract concise bounded description as nested `RdfModel`
- [ ] **Transitive helpers** — optional field decorators using `transitiveClosure` / `transitive_subjects`
- [ ] **`graphs_equal`** — `isomorphic` + term-normalized compare for tests
- [ ] **RDFS subclass import** — follow `rdfs:subClassOf` when choosing model class
- [ ] **Vocabulary registry** — prefix ↔ model class ↔ `type_uri` registry
- [ ] **Codegen (experimental)** — OWL/RDFS → stub `RdfModel` classes (CLI)

**Exit criteria:** Subclass graph imports into correct `Agent` vs `Person`; `cbd` example in cookbook.

---

## 0.8.0 — Stores, scale, and ergonomics

**Theme:** rdflib **stores** and production-sized graphs.

- [ ] **SPARQL store adapter** — documented pattern for persistent remote graphs
- [ ] **Optional extras** — `sqlalchemy`, `berkeleydb` store backends with examples
- [ ] **Store transactions** — expose `commit` / `rollback` / `open` when store supports
- [ ] **Batch import** — chunked `graph_to_models` for large type sets
- [ ] **Caching** — memoize predicate maps per model class
- [ ] **Strict mode** — fail on unknown predicates; warn on unmapped fields
- [ ] **Plugin hooks** — custom term serializers and field resolvers (pre-0.9 registry)

**Exit criteria:** 100k-triple FOAF dump imports under documented benchmark; SQLAlchemy store example runs in CI with extra.

---

## 0.9.0 — rdflib parity audit and API freeze

**Theme:** Close the matrix; stabilize public API.

- [ ] **Coverage audit** — every row in the matrix **done** or **out of scope**
- [ ] **Plugin passthrough** — `register_parser` / `register_serializer` / `register_store` re-exports
- [ ] **API audit** — last breaking renames before 1.0
- [ ] **Migration guide** — from 0.1.x
- [ ] **Full API reference** — Sphinx/mkdocs
- [ ] **Cookbook** — formats, SPARQL, Dataset, SHACL, Fuseki, optional stores
- [ ] **Typing** — strict mypy on public API; `py.typed` complete
- [ ] **Compatibility matrix** — pinned pydantic / rdflib ranges in CI

**Exit criteria:** No “planned” cells remain in the matrix except **TBD** / **out of scope**; beta on PyPI.

---

## 1.0.0 — Stable release

**Theme:** Trustworthy default for Pydantic ↔ RDF in production. **No new rdflib surface** — only fixes, docs, and governance.

| Requirement | Detail |
|-------------|--------|
| rdflib coverage | Matrix complete per 0.9 audit |
| API stability | Semver commitment; deprecations required ≥1 minor earlier |
| Security | Safe parser defaults; document XML/URL fetch risks |
| Quality | ≥90% coverage on core; integration tests per supported format and SPARQL |
| Packaging | PyPI wheels; extras: `shacl`, `jsonld`, `sqlalchemy`, `berkeleydb`, `dev` |
| Governance | CONTRIBUTING.md, CODE_OF_CONDUCT, Keep a Changelog |

**Celebration criteria:** A downstream app can depend on `rdfmodel~=1.0` knowing rdflib features are available through RDFModel where they apply to typed models, and that patch releases are safe.

---

## Explicitly out of scope (even pre-1.0)

These rdflib areas are intentionally **not** wrapped; use rdflib directly or a separate integration package:

| Item | Rationale |
|------|-----------|
| HTML Microdata / RDFa parsers | Scraping workflow, not domain model I/O |
| `rdflib.contrib.graphdb` / RDF4J clients | Vendor-specific; belongs in integrations |
| `rdflib.tools` CLI utilities | CLI is rdflib’s job |
| Path algebra (`rdflib.paths`) | Graph traversal DSL, not Pydantic ORM |
| Full OWL reasoning | Use dedicated reasoners |
| Replacing rdflib parsers, stores, or SPARQL engine | RDFModel orchestrates, never forks |

---

## How to influence the roadmap

1. Open an issue with the label `roadmap` describing your use case.
2. If requesting a new rdflib feature, name the rdflib API (`Graph.method`, format, store plugin).
3. Link vocabularies, sample data, or SHACL shapes when possible.

---

## Version summary

| Version | Focus | rdflib layers |
|---------|--------|----------------|
| **0.1.0** | Flat models, in-memory graph round-trip | `Graph.add`, basic terms |
| 0.2.0 | Fields, namespaces, merge | `bind`, iterators |
| 0.3.0 | Literals, blanks, lists, skolemize | `term`, `collection`, `resource` |
| 0.4.0 | All document formats, SHACL | `parse`, `serialize` |
| 0.5.0 | Named graphs | `Dataset` |
| 0.6.0 | SPARQL + remote store | `query`, UPDATE, SPARQL store |
| 0.7.0 | CBD, isomorphism, RDFS | graph algorithms |
| 0.8.0 | Persistent stores, scale | `Store` plugins |
| 0.9.0 | Matrix audit, API freeze | `plugin` passthrough |
| **1.0.0** | Stable, documented, governed | parity frozen |
