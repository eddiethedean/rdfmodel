# RDFModel

**Pydantic models for RDF graphs.** Declare your domain as typed Python classes, serialize to [rdflib](https://github.com/RDFLib/rdflib) triples, and hydrate back — without hand-written mapping code for every predicate.

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

## Why RDFModel?

| Without RDFModel | With RDFModel |
|------------------|---------------|
| Manually `graph.add((s, p, o))` for each field | `person.to_graph()` |
| Parse triples by hand into dataclasses | `Person.from_graph(graph, uri)` |
| Repeat predicate IRIs and subject logic per project | `rdf_field()` + nested `Rdf` config |

RDFModel is a thin bridge: it does not replace rdflib parsers, stores, or SPARQL — it orchestrates them around **Pydantic-shaped** domain models. See [ROADMAP.md](ROADMAP.md) for planned releases through **1.0.0**.

## Requirements

- Python **3.10+**
- [Pydantic](https://docs.pydantic.dev/) v2
- [rdflib](https://rdflib.readthedocs.io/) v7

## Install

```bash
pip install rdfmodel
```

## Quick start

```python
from rdfmodel import RdfModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"

class Person(RdfModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)

alice = Person(slug="alice", name="Alice", age=30)

# Export to an in-memory rdflib Graph
graph = alice.to_graph()
print(alice.subject_uri())  # http://example.org/people/alice

# Import one resource by subject IRI
same = Person.from_graph(graph, alice.subject_uri())
assert same == alice

# Import every foaf:Person in the graph
everyone = Person.all_from_graph(graph)
```

## How it works

### 1. Nested `Rdf` config

Each model subclass declares RDF metadata on a nested class:

| Attribute | Purpose |
|-----------|---------|
| `namespace` | Base IRI for subject resources |
| `type_uri` | Value for `rdf:type` on export; filter on `all_from_graph()` |
| `id_field` | Model field whose value forms the subject IRI path segment |

Subject IRIs are built as `{namespace}/{id}` (a `/` is added to `namespace` when needed). **Id values are percent-encoded** in the path, so spaces and reserved characters round-trip safely.

Override the subject for a single export/import with `uri=`:

```python
alice.to_graph(uri="http://custom.example/alice")
Person.from_graph(graph, "http://custom.example/alice")
```

### 2. Field → predicate mapping

Map Pydantic fields to predicate IRIs with **`rdf_field()`**:

```python
name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
```

Or attach metadata on the type with **`Annotated`** and **`Predicate`**:

```python
from typing import Annotated
from rdfmodel import Predicate

title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]
```

Fields without a predicate mapping are **ignored** on export and import (useful for computed or local-only attributes).

### 3. Term conversion

On export, Python values become RDF terms:

| Python | RDF |
|--------|-----|
| `str` (not IRI-like) | `xsd:string` literal |
| `str` starting with `http://`, `https://`, `urn:` | `URIRef` |
| `int`, `float`, `bool`, `date`, `datetime` | XSD-typed literals |

On import, literals are converted back using the field’s type annotation.

## API overview

**Instance methods**

| Method | Description |
|--------|-------------|
| `subject_uri(uri=None)` | Subject IRI (derived or explicit) |
| `to_triples(uri=None)` | List of `(subject, predicate, object)` tuples |
| `to_graph(graph=None, uri=None)` | Serialize into an rdflib `Graph` |

**Class methods**

| Method | Description |
|--------|-------------|
| `from_graph(graph, uri)` | Hydrate one instance from triples about `uri` |
| `all_from_graph(graph, type_uri=None)` | Load all resources of this model’s RDF type |
| `rdf_config()` | Resolved `RdfConfig` for this class |

**Module-level helpers** (same behavior, usable without subclassing `RdfModel`):

`model_to_graph`, `model_to_triples`, `models_to_graph`, `graph_to_model`, `graph_to_models`

**Constants:** `RDF`, `RDFS`, `XSD`, `RDF_TYPE` — common namespace IRIs.

## Batch export

```python
from rdfmodel import models_to_graph

people = [
    Person(slug="alice", name="Alice"),
    Person(slug="bob", name="Bob"),
]
graph = models_to_graph(people)
```

Pass an existing `Graph` to merge into it:

```python
graph = Graph()
models_to_graph(people, graph)
```

## What’s in 0.1.0

- `RdfModel` base class (Pydantic v2, `validate_assignment=True`)
- Subject IRI derivation with safe prefix matching on import
- `rdf:type` from `Rdf.type_uri`
- Round-trip for XSD scalars: `str`, `int`, `float`, `bool`, `date`, `datetime`
- In-memory `Graph` I/O only (parse/serialize and SPARQL are on the [roadmap](ROADMAP.md))

## Current limitations

- **Single value per predicate** — multiple objects for the same predicate import only the first ([0.2.0](ROADMAP.md)).
- **Unmapped fields are omitted** — no predicate mapping means no triples.
- **Blank nodes** — `BNode` objects cannot be imported into `str` fields ([0.3.0](ROADMAP.md)).
- **Flat models only** — no nested `RdfModel` embedding or RDF lists yet.

## Development

```bash
git clone https://github.com/RDFModel/RDFModel.git
cd RDFModel
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                    # 100% coverage enforced
ruff check src tests
```

CI runs on Python 3.10, 3.12, and 3.13.

## License

MIT — see [LICENSE](LICENSE).
