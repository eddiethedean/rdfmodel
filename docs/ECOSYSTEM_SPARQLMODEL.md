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
| **0.3** | Blanks / RDF lists (if needed) |
| **0.4** | File I/O |
| **0.5** | Named graphs (if needed) |
| **0.9+** | API freeze for semver pin |

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
4. **At 0.9+:** Require `triplemodel` in `pyproject.toml` with a documented semver range; publish migration note for users who only used SparqlModel mapping APIs.

---

## PR boundary (quick)

| Change | Open in |
|--------|---------|
| Predicate metadata, literals, subject URI | TripleModel |
| New `Field()` CURIE sugar only | SparqlModel (thin wrapper) |
| `where()` / compiler / `NOT EXISTS` | SparqlModel |
| Turtle round-trip in unit tests | TripleModel (or SparqlModel integration test calling TripleModel) |

Cross-package contract tests (optional): export `put(person)` triple set equals TripleModel `sync_to_graph` + SparqlModel-owned cascade rules.
