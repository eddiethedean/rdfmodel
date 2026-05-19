# SparqlModel ecosystem guide (for SparqlModel development)

Copy this file into the SparqlModel repo (e.g. `docs/ECOSYSTEM.md`). TripleModel-side summary: [ECOSYSTEM.md](ECOSYSTEM.md). Strategy: [PLAN.md](PLAN.md).

---

## Stack

```text
sparqlmodel  →  triplemodel  →  pyoxigraph · pydantic
```

**Architecture (Option A):** `SPARQLModel` **subclasses** `TripleModel`. One class, one mapping path. Session I/O calls `sync_to_graph` / `from_graph` on the same instances.

**Rules:** SparqlModel may depend on **`triplemodel`** (PyPI); `triplemodel` must never import `sparqlmodel`. Do not reimplement mapping in `graph.py`. Do not use dynamic shadow `TripleModel` classes (`exec`) after **0.4**.

---

## Division of labour

| SparqlModel owns | TripleModel owns |
|------------------|------------------|
| `SPARQLSession`, stores | `to_graph` / `from_graph`, sync/remove |
| Query DSL + compiler | Terms, literals, subject IRIs |
| `put`/`delete` cascade | `parse` / `serialize` |
| Hydration `depth` | Namespaces, Dataset |
| FastAPI, HTTP SPARQL | pyoxigraph matrix ([ROADMAP](ROADMAP.md)) |

---

## Dependency

**Current (shipped):**

```toml
dependencies = ["triplemodel>=0.9,<2"]
```

**After TripleModel 0.10 (SM-7):**

```toml
dependencies = ["triplemodel>=0.10,<2"]
```

Use `triplemodel.Store` (not `rdflib.Graph`) for session graph I/O. Tighten to `~=1.0` when TripleModel 1.0 ships.

---

## Stable TripleModel entry points (integrator tier)

Use these from SparqlModel instead of reimplementing mapping:

| API | Role |
|-----|------|
| `TripleModel` (subclassed by `SPARQLModel`) | Core model base |
| `sync_to_graph` / `sync_to_dataset` | Owned-triple sync (SparqlModel `put` builds on this) |
| `from_graph` / `all_from_graph` | Load paths |
| `model_to_graph`, `graph_to_model`, `load_models` | Batch I/O |
| `rdf_field`, `Predicate`, nested `class Rdf` | Field metadata |
| `IriId` | Explicit IRI `id` fields |
| `Rdf.prefixes`, `bind_namespaces` | Namespace binding |
| `parse` / `serialize`, `load_graph`, `dump_graph` | File and string I/O |
| `register_predicate_resolver`, `register_literal_type` | Shared policy hooks |

See [API_STABILITY.md](API_STABILITY.md) for semver rules.

---

## Module plan (SparqlModel)

| Module | Action |
|--------|--------|
| `_triple.py` | **Remove in 0.4** (interim 0.3 adapter) |
| `model.py` | **`SPARQLModel(TripleModel)`** + query metaclass |
| `fields.py` | Thin sugar → `rdf_field` / `Predicate` at class creation |
| `graph.py` | **Keep** cascade/orphan policy only |
| `serializers.py` | Wrap TripleModel (**0.6**) |
| `compiler.py`, `query.py`, `stores/` | **Keep** |

---

## Integration milestones (SparqlModel versions)

| SparqlModel | Theme | TripleModel |
|-------------|--------|-------------|
| **0.3** (shipped) | Session I/O via interim `_triple.py` | `sync_to_graph`, `from_graph` |
| **0.4** (next) | **Option A** — unified model; delete `_triple.py` | Direct calls on `SPARQLModel` instances |
| **0.5** | Async end-to-end | — |
| **0.6** | Delegated file I/O | `parse` / `serialize` |
| **1.2** | Production GA | Stable mapping substrate |

TripleModel **SM-6** tracks SparqlModel **0.4** — see [ROADMAP.md](ROADMAP.md#sparqlmodel-integration-milestones).

---

## SparqlModel 0.4 exit criteria (Option A)

- [ ] `class SPARQLModel(TripleModel)` with merged metaclass
- [ ] `Field` / `Relationship` build TripleModel metadata (no `exec`)
- [ ] `session.put` / `get` use `sync_to_graph` / `from_graph` on app instances
- [ ] Delete `_triple.py`; contract tests updated
- [ ] Public API unchanged: `Field`, `Relationship`, `session.put`

---

## Where to fix bugs

| Issue | Repo |
|-------|------|
| Wrong `Literal` datatype | TripleModel |
| Stale triple after `put` | TripleModel sync + SparqlModel policy |
| `!=` filter semantics | SparqlModel |
| Orphan embedded IRI | SparqlModel |
| Metaclass / subclass validation order | SparqlModel + TripleModel coordination |

Full tables: [ECOSYSTEM.md](ECOSYSTEM.md).

---

## PR boundary (quick)

| Change | Open in |
|--------|---------|
| Predicate metadata, literals, subject URI | TripleModel |
| `Field()` / `Relationship()` sugar only | SparqlModel |
| `where()` / compiler / `NOT EXISTS` | SparqlModel |
| `SPARQLModel(TripleModel)` inheritance | SparqlModel (**0.4**) |
| Turtle round-trip in unit tests | TripleModel (or SparqlModel integration test calling TripleModel) |

Cross-package contract tests: SparqlModel `put` triple set equals TripleModel `sync_to_graph` + SparqlModel-owned cascade rules.
