# TripleModel

[![CI](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://github.com/eddiethedean/triplemodel)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE)

**Pydantic models for RDF graphs.** Map typed Python classes to [rdflib](https://github.com/RDFLib/rdflib) triples and back — without hand-writing `graph.add` for every field.

| | |
|--|--|
| PyPI / import | `triplemodel` |
| Base class | `TripleModel` |

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

**TripleModel** is the **typed mapping layer** in a small ecosystem: Pydantic models ↔ RDF triples via field types and predicates. [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (session, SPARQL queries, ORM) is planned to depend on TripleModel from **0.2** — see the [ecosystem guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md).

> **0.1.0 is alpha.** The API may change until 1.0. See [CHANGELOG](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md) and the [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).

## Features

- **Pydantic v2** models with `validate_assignment=True`
- **Declarative mapping** — nested `Rdf` config + `rdf_field()` or `Annotated[..., Predicate(...)]`
- **Subject IRIs** — build from `namespace` + `id_field`, percent-encoded segments, safe import (no prefix collisions)
- **XSD round-trip** — `str`, `int`, `float`, `bool`, `date`, `datetime`; IRI-like strings → `URIRef`
- **Stateless I/O** — `to_graph` / `from_graph` / `all_from_graph` / `models_to_graph` on in-memory `Graph`
- **Typed package** — `py.typed` for type checkers

**Not in 0.1.0** (on the [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md)): file parse/serialize, multi-valued fields, nested models, sync/remove, SPARQL helpers.

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

### Term conversion

| Python | RDF (export) |
|--------|----------------|
| `str` (not IRI-like) | `xsd:string` literal |
| `str` with `http://`, `https://`, `urn:` | `URIRef` |
| `int`, `float`, `bool`, `date`, `datetime` | XSD-typed literal |

Import uses each field’s type annotation. `BNode` objects cannot be coerced into `str` fields.

## API reference

### `TripleModel` methods

| | Method | Description |
|---|--------|-------------|
| Instance | `subject_uri(uri=None)` | Subject IRI |
| Instance | `to_triples(uri=None)` | `(subject, predicate, object)` tuples |
| Instance | `to_graph(graph=None, uri=None)` | Serialize into a `Graph` |
| Class | `from_graph(graph, uri)` | Load one resource |
| Class | `all_from_graph(graph, type_uri=None)` | Load all resources of this `type_uri` |
| Class | `rdf_config()` | Resolved `RdfConfig` |

### Module-level API

| Name | Description |
|------|-------------|
| `rdf_field`, `Predicate` | Predicate metadata for fields |
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

## Limitations (0.1.0)

- **Single value per predicate** — multiple objects import only the first ([0.2.0](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md) adds multi-value fields).
- **Flat models** — no nested `TripleModel` or RDF lists yet.
- **In-memory graphs only** — no `parse` / `serialize` until [0.4.0](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).
- **No sync/remove** — re-export does not drop triples for cleared fields until [0.2.0](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).

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
PYTHONPATH=src python examples/readme_examples.py
```

CI runs on Python 3.10, 3.12, and 3.13. Release steps: [RELEASING.md](https://github.com/eddiethedean/triplemodel/blob/main/RELEASING.md).

## Documentation

| Doc | Description |
|-----|-------------|
| [CHANGELOG](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md) | Release notes |
| [Roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md) | Versions and rdflib parity |
| [Plan](https://github.com/eddiethedean/triplemodel/blob/main/docs/PLAN.md) | Strategy and priorities |
| [Ecosystem](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md) | triplemodel ↔ SparqlModel boundaries |

## License

MIT — see [LICENSE](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE).
