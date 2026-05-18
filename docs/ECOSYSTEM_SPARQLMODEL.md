# SparqlModel ecosystem guide (for SparqlModel development)

Copy this file into the SparqlModel repo (e.g. `docs/ECOSYSTEM.md`). TripleModel-side summary: [ECOSYSTEM.md](ECOSYSTEM.md). Strategy: [PLAN.md](PLAN.md).

---

## Stack

```text
sparqlmodel  →  triplemodel  →  rdflib · pydantic
```

**Rules:** SparqlModel may depend on **`triplemodel`** (PyPI); `triplemodel` must never import `sparqlmodel`. Do not reimplement mapping in `graph.py` once upstream APIs exist.

---

## Division of labour

| SparqlModel owns | TripleModel owns |
|------------------|---------------|
| `SPARQLSession`, stores | `to_graph` / `from_graph`, sync/remove |
| Query DSL + compiler | Terms, literals, subject IRIs |
| `put`/`delete` cascade | `parse` / `serialize` |
| Hydration `depth` | Namespaces, Dataset |
| FastAPI, HTTP SPARQL | rdflib matrix ([ROADMAP](ROADMAP.md)) |

---

## Dependency gate

Pin `triplemodel` only after:

| TripleModel | Unblocks |
|----------|----------|
| **0.2** (released) | Multi-value, nested models, sync/remove, prefixes — pin `triplemodel>=0.2,<0.3` |
| **0.3** (released) | Blanks / RDF lists — pin `triplemodel>=0.3,<0.4` |
| **0.4** (released) | File I/O, dispatch, inverse predicates — pin `triplemodel>=0.4,<0.5` |
| **0.5** (released) | Named graphs — pin `triplemodel>=0.5,<0.6` |
| **0.9** (released) | API freeze — pin `triplemodel>=0.9,<2` |
| **1.0** (planned) | Production semver — pin `triplemodel~=1.0` (exact range TBD) |

**Current recommendation (SM-5):**

```toml
dependencies = ["triplemodel>=0.9,<2"]
```

### Stable TripleModel entry points

Use these from SparqlModel instead of reimplementing mapping:

| API | Role |
|-----|------|
| `TripleModel.to_graph` / `from_graph` | Core round-trip |
| `sync_to_graph` / `sync_to_dataset` | Owned-triple sync (SparqlModel `put` builds on this) |
| `model_to_graph`, `graph_to_model`, `load_models` | Batch I/O |
| `register_predicate_resolver`, `register_literal_type` | Shared predicate/literal policy |
| `Rdf.prefixes`, `bind_namespaces` | Namespace binding |
| `parse` / `serialize`, `load_graph`, `dump_graph` | File and string I/O |

See [API_STABILITY.md](API_STABILITY.md) for semver rules.

---

## Module retirement plan

| SparqlModel | Action |
|-------------|--------|
| `graph.py` | Delegate to TripleModel; keep cascade in `session.py` |
| `serializers.py` | Wrap TripleModel 0.4+ |
| `fields.py` | Adapter to TripleModel predicate metadata |
| `compiler.py`, `query.py`, `stores/` | **Keep** |

---

## Where to fix bugs

| Issue | Repo |
|-------|------|
| Wrong `Literal` datatype | TripleModel |
| Stale triple after `put` | TripleModel sync + SparqlModel policy |
| `!=` filter semantics | SparqlModel |
| Orphan embedded IRI | SparqlModel |

Full tables: [ECOSYSTEM.md](ECOSYSTEM.md).

---

## Integration checklist (SparqlModel repo)

1. **Before 0.2:** Keep mapping in `graph.py`; optionally vendor or path-depend on TripleModel for comparison tests only.
2. **At TripleModel 0.2:** Add `triplemodel` as optional extra or dev dependency; replace export/import core with `TripleModel.to_graph` / `from_graph` + TripleModel sync API; retain `session.put` / `delete` for cascade and orphans.
3. **At 0.4:** Point `serializers.py` at TripleModel `parse` / `serialize`; delete duplicate format tables.
4. **At 0.9+:** Require `triplemodel>=0.9,<2` in `pyproject.toml`; delegate mapping to stable APIs above; publish SparqlModel-side note for users who relied on duplicated `graph.py` mapping (not TripleModel version upgrades).

---

## PR boundary (quick)

| Change | Open in |
|--------|---------|
| Predicate metadata, literals, subject URI | TripleModel |
| New `Field()` CURIE sugar only | SparqlModel (thin wrapper) |
| `where()` / compiler / `NOT EXISTS` | SparqlModel |
| Turtle round-trip in unit tests | TripleModel (or SparqlModel integration test calling TripleModel) |

Cross-package contract tests (optional): export `put(person)` triple set equals TripleModel `sync_to_graph` + SparqlModel-owned cascade rules.
