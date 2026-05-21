# API stability (0.9+)

From **0.9.0**, the public API is frozen for downstream packages (including [SparqlModel](ECOSYSTEM_SPARQLMODEL.md)) until **1.0.0**.

## 0.10.0 engine exception

**0.10.0** replaces rdflib with pyoxigraph. These are **intentional breaking changes** (see [MIGRATION_0.10.md](MIGRATION_0.10.md)):

| Breaking | Detail |
|----------|--------|
| Graph type | Use `triplemodel.Store` (not `rdflib.Graph`) |
| Plugin hooks | `register_parser` / `register_serializer` / `register_store` removed |
| Remote SPARQL graph | `open_sparql_graph` / `load_sparql` raise `NotImplementedError` (symbols kept for import compatibility) |
| `[sqlalchemy]` extra | Use `open_graph("disk", path)` |

**Unchanged:** symbols in `triplemodel.__all__` for mapping (`TripleModel`, `rdf_field`, `to_graph`, `from_graph`, `sync_to_graph`, `load_models`, …) — method **names** kept; arguments expecting rdflib graphs now expect `Store`.

## 0.11.0 rdflib cleanup exception

**0.11.0** removes all remaining rdflib integration (see [MIGRATION_0.11.md](MIGRATION_0.11.md)):

| Breaking | Detail |
|----------|--------|
| SHACL | `triplemodel[shacl]` extra, `validate_graph`, `shacl_shapes=` removed |
| Parse/serialize kwargs | `**rdflib_kwargs` → `**format_kwargs` |
| `bind_namespaces` | `strategy="rdflib"` removed (use `"core"`) |
| Low-level parse | `publicID=` → `base_iri=` on `Store.parse` / `Dataset.parse` |

## Stable surface

Import from the package root:

```python
from triplemodel import TripleModel, Store, model_to_graph, load_models, ...
```

Symbols in `triplemodel.__all__` are **semver-stable** from 0.9 through 1.x for mapping behavior (patch fixes only).

## Semipublic modules

| Module | Use |
|--------|-----|
| `triplemodel.plugins` | Literals, predicate resolvers |
| `triplemodel.io` | Advanced graph/dataset/SPARQL helpers |
| `triplemodel.config` | `RdfConfig`, constants |
| `triplemodel.vocab` | Bundled namespace objects |

## Integrator tier (SparqlModel / Option A)

| API | Role |
|-----|------|
| `TripleModel`, `rdf_field`, `Predicate`, `IriId` | Model base and field metadata |
| `sync_to_graph`, `from_graph`, `to_graph` | Session read/write on `Store` |
| `RdfConfig` / nested `class Rdf` | `type_uri`, prefixes, embed mode |
| `register_rdf_resource` | Subclass registration |

Recommended dependency after **0.10.0**:

```text
triplemodel>=0.10,<2
```

See [ECOSYSTEM_SPARQLMODEL.md](ECOSYSTEM_SPARQLMODEL.md) for **SM-7**.
