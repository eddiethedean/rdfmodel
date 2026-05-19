# API stability (0.9+)

From **0.9.0**, the public API is frozen for downstream packages (including [SparqlModel](ECOSYSTEM_SPARQLMODEL.md)) until **1.0.0**.

## Stable surface

Import from the package root:

```python
from triplemodel import TripleModel, model_to_graph, load_models, ...
```

Symbols in `triplemodel.__all__` are **semver-stable** from 0.9 through 1.x:

- **Patch** releases: bug fixes only; no `__all__` changes.
- **Minor** releases (pre-1.0 beta): additive symbols only; deprecations require a prior minor with `DeprecationWarning`.
- **Major** 1.0: breaking removals only after ≥1 minor of deprecation.

## Semipublic modules

These are supported for integrators but may gain symbols without a major bump:

| Module | Use |
|--------|-----|
| `triplemodel.plugins` | Literals, predicate resolvers, rdflib plugin registration |
| `triplemodel.io` | Advanced graph/dataset/SPARQL helpers |
| `triplemodel.config` | `RdfConfig`, constants |
| `triplemodel.vocab` | Bundled namespace objects |

Prefer root imports when a name is re-exported in `__all__`.

## Not public

- `triplemodel._typing`, private modules, and test-only code.
- Undocumented attributes on `TripleModel` or rdflib objects.

## Integrator tier (SparqlModel / Option A)

APIs SparqlModel may call from a **`SPARQLModel(TripleModel)` subclass** without forking mapping logic:

| API | Role |
|-----|------|
| `TripleModel`, `rdf_field`, `Predicate`, `IriId` | Model base and field metadata |
| `sync_to_graph`, `from_graph`, `to_graph` | Session read/write |
| `RdfConfig` / nested `class Rdf` | `type_uri`, prefixes, embed mode |
| `register_rdf_resource` | Subclass registration (must work for `SPARQLModel`) |

**Out of scope for integrators:** `SPARQLSession`, Python query DSL, cascade `put` policy — SparqlModel only.

## SparqlModel integration

Recommended dependency range after **0.9.0** (shipped in `sparqlmodel`):

```text
triplemodel>=0.9,<2
```

Tighten to `~=1.0` when TripleModel 1.0 ships. **SM-6 / SparqlModel 0.4** adopts Option A (`SPARQLModel` subclasses `TripleModel`). See [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) for module retirement and exit criteria.

## Historical versions

There is no end-user migration guide for 0.1–0.8 (no production adopters). See {doc}`changelog` for release history.
