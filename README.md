# TripleModel

[![CI](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://github.com/eddiethedean/triplemodel)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE)
[![Documentation](https://readthedocs.org/projects/triplemodel/badge/?version=latest)](https://triplemodel.readthedocs.io/en/latest/?badge=latest)

**Pydantic models for RDF graphs.** Map typed Python classes to [rdflib](https://github.com/RDFLib/rdflib) triples and back — without hand-writing `graph.add` for every field.

| | |
|--|--|
| PyPI / import | `triplemodel` |
| Base class | `TripleModel` |

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

**TripleModel** is the **typed mapping layer** in a small ecosystem: Pydantic models ↔ RDF triples via field types and predicates. [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (session, SPARQL queries, ORM) is planned to depend on TripleModel from **0.2** — see the [ecosystem guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md).

> **0.2.0 is alpha.** The API may change until 1.0. See [CHANGELOG](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md) and the [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).

## Features

- **Pydantic v2** models with `validate_assignment=True`
- **Declarative mapping** — nested `Rdf` config + `rdf_field()` or `Annotated[..., Predicate(...)]`
- **Subject IRIs** — build from `namespace` + `id_field`, percent-encoded segments, safe import (no prefix collisions)
- **XSD round-trip** — `str`, `int`, `float`, `bool`, `date`, `datetime`; IRI-like strings → `URIRef`
- **Stateless I/O** — `to_graph` / `from_graph` / `all_from_graph` / `models_to_graph` on in-memory `Graph`
- **Multi-valued fields** — `list[T]` / `set[T]` round-trip multiple objects per predicate
- **Nested models** — embed child `TripleModel` instances (`Rdf.embed`: `"iri"` or `"bnode"`)
- **Sync modes** — `sync_to_graph` / `to_graph(..., mode="replace"|"patch")` remove stale owned triples when fields are cleared
- **Prefixes & CURIEs** — `Rdf.prefixes`, `rdf_field("foaf:name")`, `bind_namespaces`
- **Typed package** — `py.typed` for type checkers

**Not in 0.2.0** (on the [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md)): file parse/serialize (0.4), RDF lists and full blank-node strategy (0.3), SPARQL helpers (0.6).

## Requirements

- Python **3.10+**
- [Pydantic](https://docs.pydantic.dev/) v2
- [rdflib](https://rdflib.readthedocs.io/) v7

## Install

```bash
pip install triplemodel
```

## Quick start

```python
from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)

alice = Person(slug="alice", name="Alice", age=30)

graph = alice.to_graph()
print(alice.subject_uri())  # http://example.org/people/alice

assert Person.from_graph(graph, alice.subject_uri()) == alice
assert len(Person.all_from_graph(graph)) == 1
```

## Concepts

### RDF metadata (`class Rdf`)

| Attribute | Role |
|-----------|------|
| `namespace` | Base IRI for subject resources |
| `type_uri` | Emitted as `rdf:type`; used to filter `all_from_graph()` |
| `id_field` | Field value appended to `namespace` for the subject IRI |

Subject IRIs use `subject_base(namespace)` + percent-encoded id (`quote` / `unquote`). Override the subject IRI per call with `uri=` (round-trip works when the URI still matches `namespace`):

```python
alice = Person(slug="alice", name="Alice")
custom_uri = "http://example.org/people/alice"
graph = alice.to_graph(uri=custom_uri)
assert Person.from_graph(graph, custom_uri) == alice
```

Shared helpers (also on the package root):

```python
from triplemodel import id_from_subject_uri, subject_base

base = subject_base("http://example.org/people")  # ensures trailing / or #
id_from_subject_uri("http://example.org/people", "http://example.org/people/alice")  # "alice"
```

### Field → predicate

```python
name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
```

Or with **`Annotated`**:

```python
from typing import Annotated
from triplemodel import Predicate

title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]
```

Fields **without** a predicate mapping are skipped on export and import (handy for computed or app-only fields).

Subclasses **inherit** a parent’s nested `Rdf` class when the child does not define `Rdf`. If the child declares `class Rdf:`, it **replaces** the parent’s config entirely — do not use an empty nested `Rdf` on a subclass.

### Term conversion

| Python | RDF (export) |
|--------|----------------|
| `str` (not IRI-like) | `xsd:string` literal |
| `str` with an RFC 3986 scheme (`http:`, `https:`, `urn:`, `mailto:`, `file:`, …) | `URIRef` |
| `int`, `float`, `bool`, `date`, `datetime` | XSD-typed literal |

Import uses each field’s type annotation. `BNode` objects cannot be coerced into `str` fields.

## API reference

### `TripleModel` methods

| | Method | Description |
|---|--------|-------------|
| Instance | `subject_uri(uri=None)` | Subject IRI |
| Instance | `to_triples(uri=None)` | `(subject, predicate, object)` tuples |
| Instance | `to_graph(graph=None, uri=None, mode="add")` | Serialize into a `Graph` (`mode`: `add`, `replace`, `patch`) |
| Instance | `sync_to_graph(graph, uri=None, mode="replace")` | Update owned triples in an existing graph |
| Class | `from_graph(graph, uri, validate_type=True, on_duplicate="warn")` | Load one resource |
| Class | `all_from_graph(graph, type_uri=None, validate_type=True, on_duplicate="warn")` | Load all resources of this `type_uri` |
| Class | `rdf_config()` | Resolved `RdfConfig` |

### Module-level API

| Name | Description |
|------|-------------|
| `rdf_field`, `Predicate`, `OnDuplicate`, `GraphMode` | Field metadata, duplicate policy, sync modes |
| `sync_to_graph`, `expand_curie`, `bind_namespaces`, `merge_graphs` | Sync, CURIEs, namespaces, graph merge |
| `RdfConfig`, `TripleModel` | Config dataclass and base model |
| `model_to_graph`, `model_to_triples`, `models_to_graph` | Export without subclassing |
| `graph_to_model`, `graph_to_models` | Import into a model class |
| `subject_base`, `id_from_subject_uri` | Subject IRI building and parsing |
| `RDF`, `RDFS`, `XSD`, `RDF_TYPE` | Common namespace IRIs |

## Examples

### Batch export into one graph

```python
from rdflib import Graph
from triplemodel import TripleModel, models_to_graph, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")


people = [
    Person(slug="alice", name="Alice"),
    Person(slug="bob", name="Bob"),
]
graph = models_to_graph(people)

# Or merge into an existing graph (rdflib Graph() is falsy when empty — pass explicitly)
existing = Graph()
models_to_graph(people, existing)
```

### Encoded subject ids

```python
from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")


bob = Person(slug="bob jones", name="Bob")
uri = bob.subject_uri()  # .../bob%20jones
restored = Person.from_graph(bob.to_graph(), uri)
assert restored == bob
```

## TripleModel vs SparqlModel

| Need | Use |
|------|-----|
| Turn a model instance into triples / load from a `Graph` | **TripleModel** (`pip install triplemodel`) |
| Turtle/JSON-LD files, namespaces, datasets (roadmap) | **TripleModel** |
| `session.put`, queries, cascade delete, HTTP store | **[SparqlModel](https://github.com/eddiethedean/sqarqlmodel)** |

Details: [project plan](https://github.com/eddiethedean/triplemodel/blob/main/docs/PLAN.md) · [ecosystem guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md).

## Limitations (0.2.x)

- **Scalar duplicates** — multiple objects on a non-collection field still warn/error via `on_duplicate` (collections import all values).
- **BNode embed** — `Rdf.embed="bnode"` is experimental; named IRI embed (`"iri"`) is preferred until 0.3.
- **RDF lists** — use `list[T]` for multiple objects per predicate, not `rdf:List` syntax ([0.3.0](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md)).
- **In-memory graphs only** — no `parse` / `serialize` until [0.4.0](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).
- **Stale triples on re-export** — use [`sync_to_graph`](https://github.com/eddiethedean/triplemodel/blob/main/docs/guides/04-updating-graphs.md) or `to_graph(..., mode="replace")` to remove cleared fields; default `mode="add"` only appends.
- **`from_graph` type check** — when `Rdf.type_uri` is set, import requires that triple unless `validate_type=False`.
- **`uri=` override** — `from_graph` can only derive `id_field` when the subject URI is under `Rdf.namespace`; off-namespace URIs fail validation unless you add triples another way.
- **Empty child `class Rdf:`** — shadows the parent and clears `namespace` / `type_uri` / `id_field`; omit `Rdf` on the child to inherit.
- **`type_uri=""` or other falsy config** — treated as unset (no `rdf:type` on export, no type filter on import).
- **`id_from_subject_uri`** — returns the URI suffix after the namespace base (may include extra `/` segments); not a single-segment validator.
- **`id_field` values `False` or `0`** — are valid ids (not treated as empty).
- **BNode subjects** — skipped in `all_from_graph()`.
- **Non-XSD boolean literals** — `bool` fields without `xsd:boolean` use a loose truthiness heuristic on import.
- **Union field types** (e.g. `str | int`) rely on rdflib `toPython()` when the annotation is not a single scalar type.
- **`Rdf.graph_mode`** — parsed into config but not wired; `to_graph()` / `sync_to_graph()` still use explicit `mode=` (default `"add"` / `"replace"`).
- **Multi-value collections** — `list[T]` / `set[T]` are for scalar `T` only; `list[TripleModel]` / `set[TripleModel]` are rejected until a future release.

## Development

```bash
git clone https://github.com/eddiethedean/triplemodel.git
cd triplemodel
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff format src tests && ruff check src tests
ty check src tests
sphinx-build -b html docs docs/_build/html -W
PYTHONPATH=src python examples/readme_examples.py
```

CI runs on Python 3.10, 3.11, 3.12, and 3.13. Release steps: [RELEASING.md](https://github.com/eddiethedean/triplemodel/blob/main/RELEASING.md).

## Documentation

**Read the Docs:** [triplemodel.readthedocs.io](https://triplemodel.readthedocs.io/)

| Doc | Description |
|-----|-------------|
| [User guides](https://triplemodel.readthedocs.io/en/latest/guides/index.html) | Step-by-step topics (mapping, sync, nested models, …) |
| [API reference](https://triplemodel.readthedocs.io/en/latest/api/index.html) | Generated from docstrings |
| [Docs sources](https://github.com/eddiethedean/triplemodel/tree/main/docs) | Sphinx / MyST source on GitHub |
| [CHANGELOG](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md) | Release notes |
| [Roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md) | Versions and rdflib parity |
| [Plan](https://github.com/eddiethedean/triplemodel/blob/main/docs/PLAN.md) | Strategy and priorities |
| [Ecosystem](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md) | triplemodel ↔ SparqlModel boundaries |

## License

MIT — see [LICENSE](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE).
