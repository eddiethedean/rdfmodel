# TripleModel roadmap

Roadmap for the **`triplemodel`** package on PyPI (base class **`TripleModel`**). This document tracks planned releases from the current **0.1.0** alpha through a stable **1.0.0**. Versions follow [Semantic Versioning](https://semver.org/): breaking API changes only on major releases; minors add features; patches fix bugs.

**Vision:** Make RDF a natural persistence and interchange layer for Pydantic-shaped domain models — typed in Python, portable as triples, without bespoke mapping code per project.

**Ecosystem:** TripleModel is the **stateless in-memory mapping** layer (file parse/serialize from **0.4**). [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (`sparqlmodel`) is the **session, query, and ORM** layer for applications. SparqlModel will **depend on TripleModel** once mapping APIs align (see [SparqlModel integration](#sparqlmodel-integration-milestones)). TripleModel must never depend on SparqlModel.

| Document | Purpose |
|----------|---------|
| {doc}`changelog` | Release history |
| {doc}`releasing` | PyPI publish checklist |
| {doc}`PLAN` | Strategy, principles, priorities |
| {doc}`ECOSYSTEM` | Boundary contract (both packages) |
| {doc}`ECOSYSTEM_SPARQLMODEL` | SparqlModel maintainer guide (copy to SparqlModel repo) |

**Pre-1.0 commitment:** Every **0.x** release adds capability until TripleModel exposes all [rdflib](https://github.com/RDFLib/rdflib) features that sensibly map to typed Pydantic models. We wrap and orchestrate rdflib; we do not reimplement parsers, stores, or SPARQL engines. We do **not** build sessions, query compilers, or cascade `put` semantics — that stays in SparqlModel. **1.0.0** is API stability and production hardening — not a catch-up release for rdflib parity.

**Matrix legend:** **SM** in release sections = required for SparqlModel’s planned `triplemodel` dependency (see integration milestones).

---

## SparqlModel integration milestones

SparqlModel today implements its own `graph.py`, `fields.py`, and `serializers.py`. TripleModel should replace that **implementation** while SparqlModel keeps **session, compiler, and cascade policy**.

| Milestone | triplemodel deliverable | SparqlModel outcome |
|-----------|----------------------|---------------------|
| **SM-0** (now) | 0.1.x mapping, subject IRI fixes | Optional dev pin; no PyPI dependency yet |
| **SM-1** | **0.2** — sync/remove, nested models, multi-value, `Rdf.prefixes`, vocab | Replace export/import core; keep `put`/`delete` orchestration |
| **SM-2** | **0.3** — blanks, RDF lists (if embed model kept) | Align hydration with TripleModel loaders |
| **SM-3** | **0.4** — `parse` / `serialize`, base URI | Retire duplicate serializers |
| **SM-4** | **0.5** — `Dataset` (if named graphs on models) | Store uses TripleModel dataset helpers |
| **SM-5** | **0.9–1.0** — API freeze, `py.typed`, semver | `sparqlmodel` requires `triplemodel~=1.0` (exact range TBD) |

**TripleModel will not implement:** `SPARQLSession`, Python `where(Model.field == x)`, SPARQL expression compiler, identity map, FastAPI, or HTTP store — see [ECOSYSTEM.md](ECOSYSTEM.md).

**0.6 SPARQL helpers** (`select_models`, etc.) are optional conveniences for TripleModel-only users; SparqlModel keeps its own compiler and may use raw `graph.query` internally.

---

## rdflib coverage matrix

Status key: **done** (0.1.0) · **planned** (target version) · **partial** · **out of scope**

| rdflib area | Capability | TripleModel surface (planned) | Ver |
|-------------|------------|----------------------------|-----|
| **Terms** | `URIRef`, `Literal`, XSD datatypes | `python_to_term` / `term_to_python` | 0.1 |
| | `BNode`, anonymous subjects/objects | `Rdf.blank_node` strategy, skolemize on export | 0.3 |
| | Language tags (`Literal.lang`) | `LangString`, `Annotated[..., Lang("en")]` | 0.3 |
| | `rdf:HTML` / `rdf:XMLLiteral` literals | optional field types or preserve via registry | 0.3 |
| | Custom / unknown datatypes | pluggable `Literal` converters | 0.2 |
| | `term.bind()` (Python ↔ datatype) | shared registry with rdflib `bind()` | 0.2 |
| | `Variable` | SPARQL result binding only (not model fields) | 0.6 |
| | RDF-star / quoted triples (`QuotedGraph`) | deferred unless rdflib 7 usage is stable | TBD |
| | RDF Containers (`Bag` / `Seq` / `Alt`) | **out of scope** (prefer `rdf:List` in 0.3) | — |
| **Graph API** | `add` / triple iterators | `to_graph`, `model_to_triples` | 0.1 |
| | `remove` / `set` | sync cleared fields; functional-property `set` | 0.2 |
| | `value()` | read single object for 0..1 cardinality fields | 0.2 |
| | `__contains__` | `Graph.has_triple` / membership in tests | 0.2 |
| | set ops `+` `-` `&` `^` | `merge_graphs` + documented BNode policy | 0.2 |
| | slice / `__getitem__` triple patterns | **out of scope** (rdflib convenience sugar) | — |
| | `bind`, `namespaces`, `compute_qname`, `qname` | `Rdf.prefixes`, `Namespace` helpers on models | 0.2 |
| | `bind_namespaces` strategies (`core` / `rdflib` / `none`) | passthrough when creating `Graph` / `Dataset` | 0.2 |
| | `parse` / `serialize` (all registered formats) | `TripleModel.parse`, `.serialize`, `load_*` / `dump_*` | 0.4 |
| | parse base URI (`publicID`, rdflib 7) | `Rdf.base_uri` / `parse(..., base=)` for relative IRIs | 0.4 |
| | `query` (SELECT, ASK, CONSTRUCT, DESCRIBE) | `select_models`, `ask`, `construct_models` | 0.6 |
| | SPARQL `SERVICE` (federated) | works via `Graph.query`; document patterns | 0.6 |
| | SPARQL UPDATE | `graph.update` wrapper + model-aware patches | 0.6 |
| | `prepareQuery`, `initNs`, `initBindings` | prepared model queries + variable pre-bind | 0.6 |
| | `cbd` (concise bounded description) | `model.cbd(graph)` → nested sub-model | 0.7 |
| | `skolemize` / `de_skolemize` | export/import options on `to_graph` / `from_graph` | 0.3 |
| | `isomorphic` / graph comparison | `graphs_equal`, optional `model_diff` | 0.7 |
| | `transitiveClosure`, `transitive_*` | optional helpers for hierarchy fields | 0.7 |
| | `collection` (RDF lists) | `list[T]` ↔ `rdf:List` | 0.3 |
| | `resource()` | lazy `ResourceRef` fields | 0.3 |
| | `Dataset` / named graphs | `@graph` context on `Rdf`, `Dataset` I/O | 0.5 |
| | `quads()`, `get_context()` | named-graph read/write in dataset helpers | 0.5 |
| | `ConjunctiveGraph` | use `Dataset` only (rdflib deprecation) | 0.5 |
| **Formats** | Turtle, Trig, N-Triples, N-Quads | `serialize(format=...)` | 0.4 |
| | RDF/XML, N3 | same | 0.4 |
| | JSON-LD | same; optional `jsonld` extra if needed | 0.4 |
| | TriG, TriX, HexTuples, longTurtle | same where rdflib registers parser/serializer | 0.4 |
| | Microdata, RDFa | **out of scope** (HTML scraping, not domain modeling) | — |
| **Stores** | Memory (`default`, `memory`) | default `Graph()` / `Dataset()` | 0.1 |
| | Remote SPARQL read (`SPARQLStore`) | `TripleModel.load_sparql(url, query)` | 0.6 |
| | Remote SPARQL read-write (`SPARQLUpdateStore`) | persistent endpoint + `update()` passthrough | 0.6 |
| | BerkeleyDB, SQLAlchemy | optional extras `triplemodel[berkeleydb]`, `[sqlalchemy]` | 0.8 |
| | LevelDB, Kyoto Cabinet (rdflib plugins) | **out of scope** for core; link in cookbook | — |
| | `open` / `close` / `destroy` on store | context manager / lifecycle helpers | 0.8 |
| | Store transactions (`commit` / `rollback` / `open`) | passthrough when backing store supports | 0.8 |
| **Namespace** | `Namespace`, `DefinedNamespace`, bundled vocabs | `from triplemodel.vocab import FOAF, SKOS, ...` | 0.2 |
| **Security** | untrusted parse URLs / files | safe defaults on `parse_url`; document risks | 1.0 |
| **Plugins** | Register custom Parser/Serializer/Store | `triplemodel.plugins.register_*` passthrough | 0.9 |
| **SHACL** | Validation (rdflib ecosystem / pyshacl) | optional `triplemodel[shacl]` pre-export hook | 0.4 |
| **contrib** | GraphDB, RDF4J clients | **out of scope** for core; link in cookbook only | — |
| **Tools** | `rdflib.tools` CLI (csv2rdf, etc.) | **out of scope** (use rdflib directly) | — |
| **Paths** | Path algebra | **out of scope** (graph traversal, not ORM) | — |

Before **1.0.0**, the matrix above must be **done** or explicitly **out of scope** with rationale in this file — no silent gaps.

---

## 0.1.0 — Foundation (current)

**Status:** Released (alpha) — on PyPI as `triplemodel==0.1.0`

| Area | Delivered |
|------|-----------|
| Core | `TripleModel` base, `Rdf` config class, `rdf_field()` / `Predicate` |
| Graph I/O | `to_graph()`, `from_graph()`, `all_from_graph()`, `models_to_graph()` |
| Terms | XSD scalars; IRI-like `str` → `URIRef` (RFC 3986 schemes) |
| Identity | Subject IRI from `Rdf.namespace` + `Rdf.id_field`; `subject_base` / `id_from_subject_uri`; explicit `uri=` override |
| Store | In-memory `Graph` only |

**rdflib parity:** minimal `Graph.add` path via serialization; most of the matrix still open.

**0.1.x hardening (done):** Safe subject-id extraction (`subject_base` / `id_from_subject_uri`); percent-encoding on export; `BNode` rejected for `str` fields; contextual import errors; `xsd:string` for plain literals; `str_strip_whitespace=False` on `TripleModel`; CI + `py.typed` + 100% coverage; MRO-inherited `Rdf` config; `validate_type` on import; duplicate-predicate warning (`on_duplicate`); unified validation error messages; `Annotated` import coercion; RFC 3986 IRI schemes on export; `OnDuplicate` public export.

**SparqlModel (SM-0):** Optional local/dev pin on `triplemodel==0.1.*` for experiments; **no** required `triplemodel` dependency in `sparqlmodel` until **0.2** (SM-1).

---

## 0.2.0 — Terms, fields, and namespaces

**Status:** Released (alpha) — on PyPI as `triplemodel==0.2.0`

**Theme:** Everything needed for ordinary RDF-shaped Pydantic models on a single default graph.

- [x] **Multi-valued fields** — `list[T]`, `set[T]` ↔ multiple objects per predicate
- [x] **Nested `TripleModel`** — blank node or named IRI embedding (configurable)
- [x] **Optional & null semantics** — omit vs explicit empty; **remove** prior triples when a field is cleared on re-export
- [x] **Custom `Literal` datatypes** — register converters (`Decimal`, `UUID`, `Enum`, …); wire **rdflib `term.bind()`**
- [x] **Namespace helpers** — CURIE expansion, `Rdf.prefixes` → `Graph.bind`
- [x] **`DefinedNamespace` vocabs** — re-export common rdflib namespaces from `triplemodel.vocab`
- [x] **`bind_namespaces` strategies** — passthrough `core` / `rdflib` / `none` when constructing graphs
- [x] **Graph merge policies** — replace / patch / add when writing into existing `Graph`
- [x] **Graph set operations** — `merge_graphs()` helper; BNode identity documented in docstrings
- [x] **`Graph.set` / `Graph.value`** — `graph_set` / `graph_value` helpers
- [x] **Graph iterator helpers** — `objects_for_field`
- [x] **Duplicate predicate warning** — scalars use `on_duplicate`; collections import all values

**Exit criteria:** FOAF `Person` with multiple `nick` values and embedded `mbox` round-trips; prefixes appear in serialized Turtle; clearing `age=None` removes `foaf:age` triples on re-export.

**SparqlModel (SM-1):** Ship `sync_to_graph` / `model_to_graph(..., mode="replace"|"patch")` (or equivalent) for owned-predicate replacement; `Rdf.prefixes` + CURIE expansion aligned with SparqlModel `__prefixes__`; optional explicit `IRI` id field alongside `id_field` + `namespace`; document triple-ownership boundaries for cascade layers.

---

## 0.3.0 — Literals, blanks, lists, and identity

**Theme:** Full rdflib **term** expressiveness for model fields.

- [ ] **`LangString` / per-language fields** — `Literal.lang` round-trip
- [ ] **Typed XML/HTML literals** — `rdf:XMLLiteral`, `rdf:HTML` where needed (or preserve opaque)
- [ ] **Arbitrary datatype literals** — preserve unknown datatype URIs via registry
- [ ] **Blank nodes** — import/export; optional `skolemize` / `de_skolemize` on `to_graph` / `from_graph`
- [ ] **RDF collections** — `list[T]` ↔ `rdf:List` via `Graph.collection`
- [ ] **`ResourceRef`** — IRI-only field resolved through `Graph.resource`
- [ ] **BNode stability** — document when IDs are stable vs session-scoped

**Exit criteria:** Dublin Core `title` with language tags; blank-node `Address`; RDF list of `nick` values all round-trip.

**SparqlModel (SM-2):** Hydration can delegate single-resource load to TripleModel before relationship expansion; blank-node strategy documented for embedded `SPARQLModel` values.

---

## 0.4.0 — Parsing, serialization, and validation

**Theme:** All rdflib **syntaxes** that make sense for documents (not HTML).

- [ ] **`TripleModel.parse` / `.serialize`** — delegate to `Graph.parse` / `Graph.serialize`
- [ ] **Format support** — Turtle, Trig, N-Triples, N-Quads, RDF/XML, N3, JSON-LD, TriX, HexTuples, longTurtle (each format rdflib registers in CI)
- [ ] **Format autodetection** — filename suffix and `format=` / media type passthrough
- [ ] **Base URI on parse** — rdflib 7 `publicID` semantics: `Rdf.base_uri` for resolving relative IRIs (not named-graph id)
- [ ] **`parse_file` / `parse_url`** — stream from path or URL into `list[TripleModel]`
- [ ] **`parse(data=...)`** — load from string (Turtle/JSON-LD snippets in apps and tests)
- [ ] **JSON-LD context** — optional `@context` on `Rdf` class for compaction; passthrough compact/expand kwargs
- [ ] **SHACL (optional extra)** — validate before `to_graph()` via pyshacl or equivalent
- [ ] **Inverse predicates** — `owl:inverseOf` pairs for import/export symmetry
- [ ] **Subclass dispatch** — multiple `type_uri`; import picks most specific registered model

**Exit criteria:** Same `Person` instance equivalent from Turtle file, JSON-LD string, and in-memory `Graph`; invalid data fails SHACL when extra installed.

**SparqlModel (SM-3):** `export_model` / file load paths call TripleModel; remove parallel format registry from SparqlModel.

---

## 0.5.0 — Datasets and named graphs

**Theme:** rdflib **Dataset** (replacing deprecated `ConjunctiveGraph`).

- [ ] **`Rdf.graph_iri` / `@graph`** — map model class or instance to a named graph IRI
- [ ] **`to_dataset` / `from_dataset`** — serialize models into correct named graphs
- [ ] **`Dataset.get_context()` / `quads()`** — read and write via named-graph helpers
- [ ] **`all_from_dataset`** — load by `rdf:type` within a graph context
- [ ] **Default graph vs union** — document query/import behavior (union default in rdflib)
- [ ] **Trig / N-Quads round-trip** — named graph boundaries preserved
- [ ] **Migrate from `ConjunctiveGraph`** — document rdflib 6→7 / `publicID` changes for dataset users

**Exit criteria:** Two model types in different named graphs round-trip through Trig without collision.

**SparqlModel (SM-4):** Only if SparqlModel models gain named-graph context; otherwise defer.

---

## 0.6.0 — SPARQL and remote graphs

**Theme:** rdflib **query** and **SPARQL store** integration (TripleModel **passthrough** — not a Python query DSL).

- [ ] **`select_models`** — SPARQL SELECT → `list[TripleModel]` with variable→field mapping
- [ ] **`construct_models`** — CONSTRUCT/DESCRIBE → target model class
- [ ] **`ask`** — thin wrapper returning `bool`
- [ ] **SPARQL UPDATE** — `apply_update(graph, query)` with documented interaction with models
- [ ] **`load_sparql`** — `SPARQLStore` / read-only endpoint into models
- [ ] **`SPARQLUpdateStore`** — read-write remote graph pattern (optional extra if needed)
- [ ] **Federated `SERVICE`** — document querying remote endpoints inside SPARQL
- [ ] **Prepared queries** — `prepareQuery()` + `initNs` from model `Rdf.prefixes`
- [ ] **`initBindings`** — pre-bind subject URI or field values in prepared model queries
- [ ] **Result types** — handle all rdflib result kinds (bindings, boolean, graph, JSON)

**Exit criteria:** Load `Person` rows from a public SPARQL endpoint in ≤10 lines; UPDATE example in docs.

**SparqlModel:** Not required for integration gate — SparqlModel owns app-side SPARQL ergonomics. TripleModel may expose thin helpers; SparqlModel keeps compiler + `HttpStore` roadmap.

---

## 0.7.0 — Graph algorithms and RDFS

**Theme:** rdflib **graph operations** that help modeling, not replace reasoners.

- [ ] **`cbd` wrapper** — extract concise bounded description as nested `TripleModel`
- [ ] **Transitive helpers** — optional field decorators using `transitiveClosure` / `transitive_subjects`
- [ ] **`graphs_equal`** — `isomorphic` + term-normalized compare for tests
- [ ] **`model_diff` / graph diff** — compare two instances or graphs for migration tests
- [ ] **Safe graph merge** — guidance when combining graphs parsed separately (BNode identity)
- [ ] **RDFS subclass import** — follow `rdfs:subClassOf` when choosing model class
- [ ] **Vocabulary registry** — prefix ↔ model class ↔ `type_uri` registry
- [ ] **Codegen (experimental)** — OWL/RDFS → stub `TripleModel` classes (CLI)

**Exit criteria:** Subclass graph imports into correct `Agent` vs `Person`; `cbd` example in cookbook.

---

## 0.8.0 — Stores, scale, and ergonomics

**Theme:** rdflib **stores** and production-sized graphs.

- [ ] **SPARQL store adapter** — documented pattern for persistent remote graphs
- [ ] **Optional extras** — `sqlalchemy`, `berkeleydb` store backends with examples
- [ ] **Store lifecycle** — `Graph.open` / `close` / `destroy` context managers for on-disk stores
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

**SparqlModel (SM-5):** Publish compatibility range; migration guide for `sparqlmodel` users; cross-package contract tests in CI (optional job).

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

**Celebration criteria:** A downstream app can depend on `triplemodel~=1.0` knowing rdflib features are available through TripleModel where they apply to typed models, SparqlModel can pin this release for mapping, and patch releases are safe.

---

## Explicitly out of scope (even pre-1.0)

### rdflib areas TripleModel does not wrap

Use rdflib directly, SparqlModel, or another integration package:

| Item | Rationale |
|------|-----------|
| HTML Microdata / RDFa parsers | Scraping workflow, not domain model I/O |
| RDF Containers (`Bag` / `Seq` / `Alt`) | Legacy container model; use `rdf:List` (0.3) instead |
| Graph slice / `g[s:p:o]` syntax | rdflib REPL sugar; use explicit `triples()` / helpers |
| `rdflib.paths` property-path operators | Graph traversal DSL, not Pydantic ORM |
| `rdflib.contrib.graphdb` / RDF4J clients | Vendor-specific; belongs in integrations |
| LevelDB / Kyoto Cabinet store plugins | Third-party rdflib extensions; cookbook only |
| `rdflib.tools` CLI utilities | CLI is rdflib’s job |
| Custom SPARQL algebra (`CUSTOM_EVALS`) | Expert extension point; use rdflib directly |
| Full OWL reasoning | Use dedicated reasoners |
| Replacing rdflib parsers, stores, or SPARQL engine | TripleModel orchestrates, never forks |

### Application features owned by SparqlModel (not TripleModel)

| Item | Package |
|------|---------|
| `SPARQLSession`, identity map, unit-of-work | SparqlModel |
| Python query DSL (`Model.field == value`) | SparqlModel |
| SPARQL WHERE compiler | SparqlModel |
| `put` / `delete` cascade and orphan cleanup | SparqlModel |
| HTTP SPARQL store (`HttpStore`) | SparqlModel |
| FastAPI integration | SparqlModel optional extra |

---

## Ecosystem summary

| | triplemodel | sparqlmodel |
|---|-------------|-------------|
| **Role** | Mapping + files | Session + queries |
| **State** | Stateless | Stateful |
| **Base class** | `TripleModel` | `SPARQLModel` |
| **Depends on** | rdflib, pydantic | rdflib, pydantic; **triplemodel** (from 0.2) |

Full boundaries: **[ECOSYSTEM.md](ECOSYSTEM.md)** · Strategy: **[PLAN.md](PLAN.md)** · SparqlModel dev copy: **[ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md)**

---

## How to influence the roadmap

1. Open an issue with the label `roadmap` describing your use case.
2. If requesting a new rdflib feature, name the rdflib API (`Graph.method`, format, store plugin).
3. For SparqlModel integration needs, reference milestone **SM-*** and whether the feature belongs in TripleModel or SparqlModel per [ECOSYSTEM.md](ECOSYSTEM.md).
4. Link vocabularies, sample data, or SHACL shapes when possible.

---

## Version summary

| Version | Focus | rdflib layers | SparqlModel |
|---------|--------|----------------|-------------|
| **0.1.0** | Flat models, in-memory graph round-trip | `Graph.add`, basic terms | SM-0 (optional dev pin) |
| 0.2.0 | Fields, namespaces, merge, remove/set | `bind`, `remove`, `value`, vocabs | **SM-1** (dependency gate) |
| 0.3.0 | Literals, blanks, lists, skolemize | `term`, `collection`, `resource` | SM-2 |
| 0.4.0 | All document formats, base URI, SHACL | `parse`, `serialize` | **SM-3** |
| 0.5.0 | Named graphs | `Dataset`, `quads`, `get_context` | SM-4 (if needed) |
| 0.6.0 | SPARQL passthrough + remote store | `query`, UPDATE, `SERVICE`, stores | — |
| 0.7.0 | CBD, isomorphism, RDFS, safe merge | graph algorithms | — |
| 0.8.0 | Persistent stores, scale | `Store` open/close, plugins | — |
| 0.9.0 | Matrix audit, API freeze | `plugin` passthrough | **SM-5** prep |
| **1.0.0** | Stable, documented, governed | parity frozen | **SM-5** pin `triplemodel` |
