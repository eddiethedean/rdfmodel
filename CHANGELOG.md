# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[0.1.0]: https://github.com/eddiethedean/triplemodel/releases/tag/v0.1.0
