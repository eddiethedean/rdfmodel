# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-17

### Added

- **RDF lists** — `list[T]` fields serialize as `rdf:List` via rdflib `Collection`; `set[T]` maps to multiple objects per predicate (unordered)
- **Language-tagged literals** — `LangString`, `Annotated[str, Lang("en")]`, and `Lang` field metadata for Dublin Core–style `@lang` values
- **`ResourceRef`** — validated IRI holder for resource object fields (preferred over bare `str` when the object is always a resource)
- **`OpaqueLiteral`** — preserves unknown or custom XSD/datatype literals on import when no converter is registered
- **`rdf:HTML` / `rdf:XMLLiteral`** — round-trip as `str` when the field type is `str`
- **Blank-node embed hardening** — stale blank-node subgraphs removed on `replace` / `patch`; `Rdf.blank_node_policy` (`"fresh"` | `"stable"`) for deterministic nested blank nodes
- **Skolemization** — `skolemize` / `de_skolemize` kwargs on `to_graph`, `sync_to_graph`, `model_to_graph`, and `from_graph`; `Rdf.skolemize_export` / `Rdf.skolemize_import` defaults
- **`examples/exit_criteria_03.py`** — DC `title` with language tag, blank-node `Address` embed, ordered `nick` `rdf:List`
- Guide: `docs/guides/09-rdf-lists-and-lang.md`

### Changed

- **Breaking:** `list[T]` is no longer “multiple objects per predicate”; use `set[T]` for that semantics (see migration in README)

### Fixed

- Union fields (`str | int`) import using literal datatype to pick the matching member type

## [0.2.0] - 2026-05-17

### Added

- **Multi-valued fields** — `list[T]` and `set[T]` map to multiple objects per predicate on import/export
- **Nested `TripleModel`** — embed related resources with `Rdf.embed` (`"iri"` or `"bnode"`)
- **Graph sync modes** — `sync_to_graph`, `to_graph(..., mode=)`, and `GraphMode` (`"add"`, `"replace"`, `"patch"`) to remove stale owned triples
- **Namespaces** — `Rdf.prefixes`, `expand_curie`, `bind_namespaces`, CURIE predicates in `rdf_field("foaf:name")`
- **`triplemodel.vocab`** — re-exports common rdflib namespaces (FOAF, DC, SKOS, …)
- **Literal registry** — `register_literal_type` with defaults for `Decimal`, `UUID`, and `Enum`
- **Graph helpers** — `merge_graphs`, `graph_value`, `graph_set`, `objects_for_field`
- **`IriId`** metadata and full-IRI `id_field` values when `Rdf.namespace` is set
- **`Rdf.graph_mode`** — when `to_graph()` / `sync_to_graph()` / `model_to_graph()` omit `mode=`, they use the class `Rdf.graph_mode` (`sync_to_graph` still defaults to `"replace"` when `graph_mode` is `"add"`)
- **`all_from_graph` without `type_uri`** — discovers subjects that have triples for mapped field predicates when no RDF type is configured
- **`graph_set_many`** — helper for multi-object predicate updates (used by patch sync)
- **Subpackages** — `triplemodel.io`, `triplemodel.fields`, `triplemodel.config`, `triplemodel.terms`, `triplemodel.embed`, `triplemodel.metadata` with single-responsibility modules (export, import, discovery, writer, sync modes, embed strategies)
- **`triplemodel.protocols`** — public extension points: `RdfResource`, `PredicateResolver`, `LiteralRegistry`, `EmbedStrategy`, `GraphWriteMode`, plus `register_rdf_resource` / `is_rdf_resource_class` for nested-type detection without importing `TripleModel` from cardinality helpers
- **`LiteralRegistry` class** — `register_literal_type` remains a thin wrapper over `default_registry`
- **Advanced kwargs** — `model_to_graph` / `sync_to_graph` accept optional `registry=` and `resolver=` for tests and custom converters (all graph modes)
- Root exports: `GraphMode`, `sync_to_graph`, `expand_curie`, `bind_namespaces`, `merge_graphs`, `LiteralRegistry`, `RdfResource`, `register_rdf_resource`, `freeze_prefixes`, `default_registry`

### Changed

- Scalar fields still use `on_duplicate` for multiple objects; collection fields import all values
- `to_graph` defaults to `mode="add"` (0.1 behaviour); use `sync_to_graph(..., mode="replace")` to drop cleared fields
- **Preferred imports** — graph I/O via `triplemodel.io`; field helpers via `triplemodel.fields`; configuration via `triplemodel.config`. The package root still re-exports the common developer surface
- **`objects_for_field`** — resolves field predicates with the same prefix/CURIE expansion as export/import (fixes inconsistency with `graph_value` / `graph_set`)
- **`freeze_prefixes`** — public name (was `_freeze_prefixes`); accepts `dict` or `list[tuple[str, str]]` for `Rdf.prefixes`
- Invalid `Rdf.embed` / `Rdf.graph_mode` values emit a `UserWarning` and fall back to `"iri"` / `"add"`
- Internal layout: no import cycles between `io`, `embed`, `terms`, `fields`, and `config`; `model_to_graph` delegates non-`add` modes to sync mode handlers instead of cross-importing monolithic modules

### Fixed

- **`patch` sync for multi-valued fields** — `sync_to_graph(..., mode="patch")` and `to_graph(..., mode="patch")` now replace all objects per predicate in one step, so `list`/`set` fields keep every value instead of only the last
- **Nested IRI embed + `replace` sync** — clears owned triples on embedded child subjects before re-export
- **Stale nested IRI children** — `replace` and `patch` remove owned triples for nested child subjects that are no longer linked (including `mbox=None`)
- **`set` export** — `None` elements are skipped on export, matching `list` behaviour
- **`list[TripleModel]` / `set[TripleModel]`** — rejected with a clear `ValueError` on export and import
- **`graph_to_model` with `URIRef` subjects** — `id_field` is derived from the subject URI when the URI is passed as a `URIRef`
- **`replace` / `patch` extension kwargs** — custom `resolver=` and `registry=` are honored in all graph write modes (not only `add`)
- **`to_graph(..., mode="patch")` on a new graph** — `PatchGraphMode` now honors `bind` and binds `Rdf.prefixes` (same as `add` / `replace`); previously only `sync_to_graph` bound prefixes for patch writes
- **Nested import with custom `registry`** — `graph_to_model(..., registry=...)` now passes the registry through `import_nested_value` and embed strategies so nested fields use the same literal converters as top-level fields

### Removed

- **Private modules** — `triplemodel._graph`, `_sync`, `_embed`, `_config`, `_fields`, `_cardinality`, `_types`, `_registry`, `_graph_ops`, `_namespaces` are no longer importable
- **`_unwrap_optional`** — use `triplemodel.metadata.cardinality.unwrap_annotation` (also exported from `triplemodel.metadata`)

### Documentation

- `examples/foaf_person_02.py` demonstrates 0.2 exit criteria
- Triple ownership documented for SparqlModel integration (SM-1)
- API reference updated for new module paths; README documents import path changes

## [0.1.0] - 2026-05-17

### Added

- `TripleModel` base class with `to_graph()`, `from_graph()`, `all_from_graph()`, and `subject_uri()`
- `rdf_field()` / `Predicate` for mapping Pydantic fields to RDF predicates
- Nested `Rdf` config (`namespace`, `type_uri`, `id_field`)
- Low-level helpers: `model_to_graph`, `model_to_triples`, `graph_to_model`, `graph_to_models`, `models_to_graph`
- Public subject-IRI helpers: `subject_base()`, `id_from_subject_uri()`
- XSD scalar round-trip (`str`, `int`, `float`, `bool`, `date`, `datetime`)
- Package constants: `RDF`, `RDFS`, `XSD`, `RDF_TYPE`
- `py.typed` PEP 561 marker for type checkers (verified in wheel via CI build)
- `from_graph` / `all_from_graph` / `graph_to_model` options: `validate_type` (default `True`), `on_duplicate` (`"warn"` | `"ignore"` | `"error"`)
- Export `OnDuplicate` from the package root for type checkers

### Fixed

- `get_rdf_config` walks the class MRO so subclasses inherit a parent’s nested `Rdf` config
- `from_graph` checks `rdf:type` against `Rdf.type_uri` when set (pass `validate_type=False` to skip)
- Pydantic validation failures on import are raised as `ValueError` with model class and subject URI context
- Duplicate predicate objects on import emit a warning by default (first value still used until 0.2 multi-value support)
- Safe subject-id extraction (no false matches when one namespace is a prefix of another)
- Percent-encoding of id segments on subject IRI export; decode on import
- Plain string literals use `xsd:string`
- XSD booleans via `Literal.toPython()` when datatype is `xsd:boolean`
- `BNode` values rejected when importing into `str` fields
- Import errors include field, predicate, and subject context
- `unwrap_annotation` peels `Annotated[...]` so `Annotated[int, Predicate(...)]` imports with correct XSD coercion
