# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-17

### Added

- `RdfModel` base class with `to_graph()`, `from_graph()`, `all_from_graph()`, and `subject_uri()`
- `rdf_field()` / `Predicate` for mapping Pydantic fields to RDF predicates
- Nested `Rdf` config (`namespace`, `type_uri`, `id_field`)
- Low-level helpers: `model_to_graph`, `model_to_triples`, `graph_to_model`, `graph_to_models`, `models_to_graph`
- Public subject-IRI helpers: `subject_base()`, `id_from_subject_uri()`
- XSD scalar round-trip (`str`, `int`, `float`, `bool`, `date`, `datetime`)
- Package constants: `RDF`, `RDFS`, `XSD`, `RDF_TYPE`
- `py.typed` marker for type checkers

### Fixed

- Safe subject-id extraction (no false matches when one namespace is a prefix of another)
- Percent-encoding of id segments on subject IRI export; decode on import
- Plain string literals use `xsd:string`
- XSD booleans via `Literal.toPython()` when datatype is `xsd:boolean`
- `BNode` values rejected when importing into `str` fields
- Import errors include field, predicate, and subject context

### Changed

- `RdfModel` uses `str_strip_whitespace=False` so RDF string values are not altered on validation

### Documentation

- README with API overview, limitations, and development instructions
- Planning docs: `docs/PLAN.md`, `docs/ROADMAP.md`, `docs/ECOSYSTEM.md`

### Notes

- **Alpha:** API may change until 1.0. Multi-value fields, nested models, sync/remove, and file I/O are planned for **0.2+**.
- **[SparqlModel](https://github.com/eddiethedean/sqarqlmodel)** integration (optional `rdfmodel` dependency) is targeted from **0.2**; see `docs/ECOSYSTEM.md`.

[0.1.0]: https://github.com/eddiethedean/rdfmodel/releases/tag/v0.1.0
