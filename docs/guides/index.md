# User guides

These guides explain how to use TripleModel **0.4.x** in order of increasing complexity. Each guide is self-contained, but later guides assume you have read {doc}`01-getting-started`.

| # | Guide | Topics |
|---|--------|--------|
| 1 | {doc}`01-getting-started` | Install, `TripleModel`, `to_graph` / `from_graph` |
| 2 | {doc}`02-mapping-fields-and-subjects` | `class Rdf`, `rdf_field`, subject IRIs |
| 3 | {doc}`03-multi-valued-fields` | Sets (multi-object), `on_duplicate` |
| 9 | {doc}`09-rdf-lists-and-lang` | RDF lists (`list[T]`), `LangString`, language metadata |
| 4 | {doc}`04-updating-graphs` | Sync modes, clearing fields |
| 5 | {doc}`05-nested-models` | Child resources, `embed` |
| 6 | {doc}`06-namespaces-and-curies` | Prefixes, compact predicates |
| 7 | {doc}`07-custom-literals-and-types` | Registry, `Decimal`, `Enum` |
| 8 | {doc}`08-working-with-graphs` | Batch export/import, helpers |
| 10 | {doc}`10-file-io` | Parse/serialize files, base URI, SHACL |
| 11 | {doc}`11-real-world-patterns` | Multi-class load, Wikidata typing, `ref_field`, `gYear` |

**Next:** {doc}`01-getting-started`
