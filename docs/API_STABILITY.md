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

## SparqlModel integration

Recommended dependency range after **0.9.0**:

```text
triplemodel>=0.9,<2
```

Tighten to `~=1.0` when TripleModel 1.0 ships. See [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) for stable entry points (`model_to_graph`, `sync_to_graph`, `load_models`, `register_predicate_resolver`, etc.).

## Historical versions

There is no end-user migration guide for 0.1–0.8 (no production adopters). See [CHANGELOG.md](../CHANGELOG.md) for release history.
