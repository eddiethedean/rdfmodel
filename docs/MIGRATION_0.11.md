# Migrating to TripleModel 0.11.0

**0.11.0** removes the last rdflib integration from TripleModel. The runtime engine remains [pyoxigraph](https://github.com/oxigraph/pyoxigraph) only.

## Dependency

```bash
pip install 'triplemodel>=0.11,<2'
```

There is no `triplemodel[shacl]` extra. Core install never included rdflib after 0.10.0.

## SHACL validation removed

| Removed | Migration |
|---------|-----------|
| `pip install triplemodel[shacl]` | Install `pyshacl` (and its dependencies) in your app if needed |
| `from triplemodel import validate_graph` | Call `pyshacl.validate` on serialized RDF or your own graphs |
| `person.to_graph(shacl_shapes=...)` | Validate outside TripleModel before or after export |
| `person.serialize(..., shacl_shapes=...)` | Same |

TripleModel no longer converts `Store` graphs to rdflib for validation.

## Renamed kwargs

| 0.10.x | 0.11.0 |
|--------|--------|
| `**rdflib_kwargs` on `parse`, `parse_file`, `parse_url`, `serialize`, `parse_into_graph`, … | `**format_kwargs` |
| `Graph.parse(..., publicID=uri)` | `Graph.parse(..., base_iri=uri)` |
| `Dataset.parse(..., publicID=uri)` | `Dataset.parse(..., base_iri=uri)` |

High-level `TripleModel.parse(..., base=)` is unchanged.

## `bind_namespaces` strategy

`strategy="rdflib"` was an alias for `"core"`. Use `"core"` or `"none"` only.

## Related

- [MIGRATION_0.10.md](MIGRATION_0.10.md) — pyoxigraph engine (0.10.0)
- [API_STABILITY.md](API_STABILITY.md) — semver exceptions
