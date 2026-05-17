# SparqlModel ecosystem guide (for SparqlModel development)

Copy this file into the SparqlModel repo (e.g. `docs/ECOSYSTEM.md`). RDFModel-side summary: [ECOSYSTEM.md](ECOSYSTEM.md). Strategy: [PLAN.md](PLAN.md).

---

## Stack

```text
SparqlModel  →  RDFModel  →  rdflib · pydantic
```

**Rules:** SparqlModel may depend on RDFModel; RDFModel must never import SparqlModel. Do not reimplement mapping in `graph.py` once upstream APIs exist.

---

## Division of labour

| SparqlModel owns | RDFModel owns |
|------------------|---------------|
| `SPARQLSession`, stores | `to_graph` / `from_graph`, sync/remove |
| Query DSL + compiler | Terms, literals, subject IRIs |
| `put`/`delete` cascade | `parse` / `serialize` |
| Hydration `depth` | Namespaces, Dataset |
| FastAPI, HTTP SPARQL | rdflib matrix ([ROADMAP](ROADMAP.md)) |

---

## Dependency gate

Pin `rdfmodel` only after:

| RDFModel | Unblocks |
|----------|----------|
| **0.2** | Multi-value, nested models, sync/remove, prefixes |
| **0.3** | Blanks / RDF lists (if needed) |
| **0.4** | File I/O |
| **0.5** | Named graphs (if needed) |
| **0.9+** | API freeze for semver pin |

---

## Module retirement plan

| SparqlModel | Action |
|-------------|--------|
| `graph.py` | Delegate to RDFModel; keep cascade in `session.py` |
| `serializers.py` | Wrap RDFModel 0.4+ |
| `fields.py` | Adapter to RDFModel predicate metadata |
| `compiler.py`, `query.py`, `stores/` | **Keep** |

---

## Where to fix bugs

| Issue | Repo |
|-------|------|
| Wrong `Literal` datatype | RDFModel |
| Stale triple after `put` | RDFModel sync + SparqlModel policy |
| `!=` filter semantics | SparqlModel |
| Orphan embedded IRI | SparqlModel |

Full tables: [ECOSYSTEM.md](ECOSYSTEM.md).

---

## Integration checklist (SparqlModel repo)

1. **Before 0.2:** Keep mapping in `graph.py`; optionally vendor or path-depend on RDFModel for comparison tests only.
2. **At RDFModel 0.2:** Add `rdfmodel` as optional extra or dev dependency; replace export/import core with `RDFModel.to_graph` / `from_graph` + RDFModel sync API; retain `session.put` / `delete` for cascade and orphans.
3. **At 0.4:** Point `serializers.py` at RDFModel `parse` / `serialize`; delete duplicate format tables.
4. **At 0.9+:** Require `rdfmodel` in `pyproject.toml` with a documented semver range; publish migration note for users who only used SparqlModel mapping APIs.

---

## PR boundary (quick)

| Change | Open in |
|--------|---------|
| Predicate metadata, literals, subject URI | RDFModel |
| New `Field()` CURIE sugar only | SparqlModel (thin wrapper) |
| `where()` / compiler / `NOT EXISTS` | SparqlModel |
| Turtle round-trip in unit tests | RDFModel (or SparqlModel integration test calling RDFModel) |

Cross-package contract tests (optional): export `put(person)` triple set equals RDFModel `sync_to_graph` + SparqlModel-owned cascade rules.
