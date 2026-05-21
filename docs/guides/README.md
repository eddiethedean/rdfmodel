# User guides

These guides explain how to use TripleModel **0.5.x** in order of increasing complexity. Each guide is self-contained, but later guides assume you have read [Getting started](01-getting-started.md).

| # | Guide | Topics |
|---|--------|--------|
| 1 | [Getting started](01-getting-started.md) | Install, `TripleModel`, `to_graph` / `from_graph` |
| 2 | [Mapping fields and subjects](02-mapping-fields-and-subjects.md) | `class Rdf`, `rdf_field`, subject IRIs |
| 3 | [Multi-valued fields](03-multi-valued-fields.md) | Sets (multi-object), `on_duplicate` |
| 9 | [RDF lists and language tags](09-rdf-lists-and-lang.md) | `list[T]` as `rdf:List`, `LangString`, language metadata |
| 4 | [Updating graphs](04-updating-graphs.md) | Sync modes, clearing fields |
| 5 | [Nested models](05-nested-models.md) | Child resources, `embed` |
| 6 | [Namespaces and CURIEs](06-namespaces-and-curies.md) | Prefixes, compact predicates |
| 7 | [Custom literals](07-custom-literals-and-types.md) | Registry, `Decimal`, `Enum` |
| 8 | [Working with graphs](08-working-with-graphs.md) | Batch export/import, helpers |
| 10 | [File I/O](10-file-io.md) | Parse/serialize, base URI |
| 11 | [Real-world patterns](11-real-world-patterns.md) | Multi-class load, Wikidata typing, `ref_field`, `gYear` |
| 12 | [Datasets and named graphs](12-datasets-and-named-graphs.md) | `Rdf.graph_iri`, `Dataset`, TriG / N-Quads |

**Next:** [Getting started →](01-getting-started.md) · Sphinx / Read the Docs navigation: [guides index](index.md)
