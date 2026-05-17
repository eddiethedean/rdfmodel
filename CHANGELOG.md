# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`patch` sync for multi-valued fields** — `sync_to_graph(..., mode="patch")` and `to_graph(..., mode="patch")` now replace all objects per predicate in one step, so `list`/`set` fields keep every value instead of only the last.
- **Nested IRI embed + `replace` sync** — `sync_to_graph` / `to_graph(..., mode="replace")` now clears owned triples on embedded child subjects before re-export, so updating nested field values no longer leaves duplicate predicates on the child IRI.
- **Stale nested IRI children** — `replace` and `patch` remove owned triples for nested child subjects that are no longer linked (identity change or `mbox=None`).
- **`set` export** — `None` elements are skipped on export, matching `list` behaviour.
- **`list[TripleModel]` / `set[TripleModel]`** — rejected with a clear `ValueError` on export and import instead of emitting invalid literals.
- **`graph_to_model` with `URIRef` subjects** — `id_field` is derived from the subject URI when the URI is passed as a `URIRef`.

### Added

- **`Rdf.graph_mode`** — when `to_graph()` / `sync_to_graph()` / `model_to_graph()` omit `mode=`, they use the class `Rdf.graph_mode` (`sync_to_graph` still defaults to `"replace"` when `graph_mode` is `"add"`).
- **`all_from_graph` without `type_uri`** — discovers subjects that have triples for mapped field predicates when no RDF type is configured.
- **`graph_set_many`** — internal helper for multi-object predicate updates (used by patch sync).

### Changed

- Invalid `Rdf.embed` / `Rdf.graph_mode` values emit a `UserWarning` and fall back to `"iri"` / `"add"`.

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
- Export `GraphMode`, `sync_to_graph`, `expand_curie`, `bind_namespaces`, `merge_graphs` from package root

### Changed

- Scalar fields still use `on_duplicate` for multiple objects; collection fields import all values
- `to_graph` defaults to `mode="add"` (0.1 behaviour); use `sync_to_graph(..., mode="replace")` to drop cleared fields

### Documentation

- `examples/foaf_person_02.py` demonstrates 0.2 exit criteria
- Triple ownership documented for SparqlModel integration (SM-1)

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
- `_unwrap_optional` peels `Annotated[...]` so `Annotated[int, Predicate(...)]` imports with correct XSD coercion
- IRI-like `str` values use any RFC 3986 scheme (`mailto:`, `file:`, etc.) on export, not only `http`/`https`/`urn`

### Changed

- `TripleModel` uses `str_strip_whitespace=False` so RDF string values are not altered on validation

### Documentation

- README with API overview, runnable examples, and development instructions
- Planning docs: `docs/PLAN.md`, `docs/ROADMAP.md`, `docs/ECOSYSTEM.md`
- `examples/readme_examples.py` and CI tests for README snippets
- README limitations: `uri=` namespace alignment, empty child `Rdf`, falsy `type_uri`, `id_from_subject_uri`, BNode subjects, loose bool coercion
- `TripleModel` docstring: subclass `Rdf` replaces parent config (do not use empty child `class Rdf:`)
- CI: Python 3.11, `ruff format --check`, `python -m build`, release workflow runs `pytest` before build

### Notes

- **Prior names (pre-release):** `rdfmodel` / `tripletyped` on PyPI and GitHub; public name is **`triplemodel`** / **`TripleModel`**.
- **Alpha:** API may change until 1.0. Multi-value fields, nested models, sync/remove, and file I/O are planned for **0.2+**.
- **[SparqlModel](https://github.com/eddiethedean/sqarqlmodel)** integration (optional `triplemodel` dependency) is targeted from **0.2**; see `docs/ECOSYSTEM.md`.

[0.2.0]: https://github.com/eddiethedean/triplemodel/releases/tag/v0.2.0
[0.1.0]: https://github.com/eddiethedean/triplemodel/releases/tag/v0.1.0
