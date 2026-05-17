# TripleModel

[![CI](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/triplemodel)](https://pypi.org/project/triplemodel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://github.com/eddiethedean/triplemodel)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE)
[![Documentation](https://readthedocs.org/projects/triplemodel/badge/?version=latest)](https://triplemodel.readthedocs.io/en/latest/?badge=latest)

**Typed Pydantic models for RDF.** Declare fields once, get correct triples in and out of [rdflib](https://github.com/RDFLib/rdflib) `Graph` objects — no manual `graph.add` for every property.

| | |
|--|--|
| **Install** | `pip install triplemodel` |
| **Import** | `from triplemodel import TripleModel, rdf_field` |
| **Docs** | [triplemodel.readthedocs.io](https://triplemodel.readthedocs.io/) |

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

TripleModel is the **mapping layer** between Pydantic-shaped domain models and RDF triples: subject IRIs, XSD literals, nested resources, `rdf:List`, language tags, and graph sync. It is **stateless** and in-memory today; [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (sessions, SPARQL, ORM) is planned to build on top — see the [ecosystem guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md).

> **0.3.0 is alpha.** APIs may change before 1.0. See the [changelog](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md) and [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md).

## Install

```bash
pip install triplemodel
```

**Requirements:** Python 3.10+, Pydantic 2, rdflib 7.

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

assert Person.from_graph(graph, alice.subject_uri()) == alice
print(alice.subject_uri())
```

```text
http://example.org/people/alice
```

Unmapped fields are ignored on export/import — useful for computed or application-only data.

## What you get in 0.3

| Area | Capability |
|------|------------|
| **Mapping** | Nested `class Rdf` + `rdf_field()` or `Annotated[..., Predicate(...)]` |
| **Identity** | Subject IRIs from `namespace` + `id_field` (percent-encoded ids) |
| **Scalars** | `str`, `int`, `float`, `bool`, `date`, `datetime`; IRI-like `str` → `URIRef` |
| **Collections** | `set[T]` → multiple objects per predicate; `list[T]` → ordered `rdf:List` |
| **Literals** | `LangString`, `Lang()`, `OpaqueLiteral`, `ResourceRef` |
| **Nesting** | Child `TripleModel` with `Rdf.embed` `"iri"` or `"bnode"` |
| **Graph writes** | `to_graph` / `sync_to_graph` with `add`, `replace`, or `patch` |
| **Namespaces** | `Rdf.prefixes`, CURIE predicates (`"foaf:name"`), `bind_namespaces` |
| **Typing** | PEP 561 `py.typed` |

**Coming later** ([roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md)): file `parse` / `serialize` (0.4), named graphs (0.5), SPARQL helpers (0.6).

### `list` vs `set` (0.3 breaking change)

In **0.2**, both `list[T]` and `set[T]` meant “several triples on the same predicate.” In **0.3**:

| Annotation | RDF shape |
|------------|-----------|
| `set[str]` | Multiple objects on one predicate (unordered) |
| `list[str]` | One `rdf:List` (`rdf:first` / `rdf:rest`) |

There is no compatibility shim — update annotations when upgrading from 0.2.

## A richer model (0.3)

Language tags, RDF lists, and nested blank-node embeds:

```python
from typing import Annotated

from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.terms.lang import Lang, LangString
from triplemodel.vocab import DC, FOAF

class Address(TripleModel):
    class Rdf:
        namespace = "http://example.org/address/"
        type_uri = "http://example.org/Address"
        id_field = "slug"

    slug: str = "home"
    street: str = rdf_field("http://example.org/street")


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "bnode"
        prefixes = {"foaf": str(FOAF), "dc": str(DC)}

    slug: str
    title: LangString = rdf_field(f"{DC}title")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    address: Address | None = rdf_field("http://example.org/home", default=None)


person = Person(
    slug="alice",
    title=LangString("Alice's profile", "en"),
    nick=["Al", "Alice"],
    address=Address(street="1 Main St"),
)
graph = person.to_graph()

person.nick = ["Alice"]
sync_to_graph(person, graph, mode="replace")
again = Person.from_graph(graph, person.subject_uri())
print(again.nick)
```

```text
['Alice']
```

Runnable version: [`examples/exit_criteria_03.py`](examples/exit_criteria_03.py) (same models; see also [`examples/doc/snippets/`](examples/doc/snippets/)).

## How mapping works

### `class Rdf` — resource metadata

| Attribute | Role |
|-----------|------|
| `namespace` | Base IRI; subject = namespace + encoded `id_field` value |
| `type_uri` | `rdf:type` on export; filter for `all_from_graph()` |
| `id_field` | Python field whose value becomes the subject id segment |
| `embed` | `"iri"` (default) or `"bnode"` for nested models |
| `prefixes` | CURIE map → `Graph.bind` on new graphs |
| `graph_mode` | Default `to_graph` mode when `mode=` is omitted |
| `blank_node_policy` | `"fresh"` or `"stable"` nested bnodes |
| `skolemize_export` / `skolemize_import` | Blank-node skolemization defaults |

Override the subject per call with `uri=` when the IRI still lives under `namespace`:

```python
graph = alice.to_graph(uri="http://example.org/people/alice")
```

Helpers: `subject_base()`, `id_from_subject_uri()`.

### Fields → predicates

```python
name: str = rdf_field("foaf:name")  # with Rdf.prefixes

from typing import Annotated
from triplemodel import Predicate

title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]
title_fr: Annotated[str, Predicate(f"{DC}title"), Lang("fr")]
```

Subclasses **inherit** a parent `Rdf` when the child does not define one. A child `class Rdf:` **replaces** the parent config entirely — never use an empty nested `Rdf` on a subclass.

### Scalar → RDF (export)

| Python | RDF |
|--------|-----|
| `str` (plain) | `xsd:string` |
| `str` with URI scheme (`http:`, `urn:`, …) | `URIRef` |
| `int`, `float`, `bool`, `date`, `datetime` | XSD literal |
| `LangString`, `ResourceRef`, `OpaqueLiteral` | matching literal / IRI |

Register custom types with `register_literal_type` and `LiteralRegistry`.

## Updating an existing graph

Default `to_graph()` uses **`mode="add"`** — it only appends. To remove triples when fields are cleared, use sync modes:

```python
from triplemodel import sync_to_graph

sync_to_graph(person, graph, mode="replace")  # replace all owned triples for this subject
sync_to_graph(person, graph, mode="patch")    # per-predicate replace; lighter touch
```

`replace` clears nested IRI children and list heads before re-export; `patch` updates predicates present in the model and clears empty fields (including on nested resources). See the [updating graphs guide](https://triplemodel.readthedocs.io/en/latest/guides/04-updating-graphs.html).

## API overview

### Instance & class methods

| Method | Description |
|--------|-------------|
| `subject_uri(uri=None)` | Subject IRI for this instance |
| `to_triples(uri=None)` | `(subject, predicate, object)` rows |
| `to_graph(graph=None, uri=None, mode="add", skolemize=None)` | Serialize into a `Graph` |
| `sync_to_graph(graph, uri=None, mode="replace", skolemize=None)` | Sync owned triples in-place |
| `from_graph(graph, uri, ...)` | Load one resource |
| `all_from_graph(graph, type_uri=None, ...)` | Load all resources of this type |
| `rdf_config()` | Resolved `RdfConfig` |

### Common imports

```python
from triplemodel import (
    TripleModel,
    rdf_field,
    Predicate,
    GraphMode,
    sync_to_graph,
    models_to_graph,
    merge_graphs,
    expand_curie,
    bind_namespaces,
    LangString,
    Lang,
    ResourceRef,
    OpaqueLiteral,
    RDF,
    XSD,
)
```

Full API: [Read the Docs API reference](https://triplemodel.readthedocs.io/en/latest/api/index.html).

## More examples

**Batch export**

```python
from rdflib import Graph
from triplemodel import models_to_graph

graph = models_to_graph([alice, bob])
models_to_graph([alice, bob], Graph())  # merge into existing graph
```

**Encoded subject ids**

```python
bob = Person(slug="bob jones", name="Bob")
print(bob.subject_uri())
```

```text
http://example.org/people/bob%20jones
```

**0.2-style multi-object `nick`** (historical): [`examples/foaf_person_02.py`](examples/foaf_person_02.py). On 0.3 use `set[str]` for that pattern.

## TripleModel vs SparqlModel

| You need | Package |
|----------|---------|
| Pydantic ↔ triples on an in-memory `Graph` | **triplemodel** |
| File I/O, datasets, SPARQL sessions, cascade `put` | **[SparqlModel](https://github.com/eddiethedean/sqarqlmodel)** (planned TripleModel dependency) |

## Known limitations

- **In-memory only** until 0.4 (`parse` / `serialize` on the roadmap).
- **BNode embed** is experimental; prefer `embed="iri"` for stable linking.
- **Collections** — `list[T]` / `set[T]` require scalar `T`; `list[TripleModel]` is not supported.
- **BNode subjects** are skipped by `all_from_graph()`.
- **Default add mode** does not remove stale triples — use `sync_to_graph` or `mode="replace"`.

Details: [user guides](https://triplemodel.readthedocs.io/en/latest/guides/index.html) · [RDF lists & lang](https://triplemodel.readthedocs.io/en/latest/guides/09-rdf-lists-and-lang.html).

## Development

```bash
git clone https://github.com/eddiethedean/triplemodel.git && cd triplemodel
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff format src tests && ruff check src tests
ty check src tests
PYTHONPATH=src python examples/exit_criteria_03.py
PYTHONPATH=src:. python examples/doc/regenerate_outputs.py  # refresh doc output files
```

CI: Python 3.10–3.13; `tests/test_doc_examples.py` runs every snippet under `examples/doc/snippets/`. Release process: [RELEASING.md](RELEASING.md).

## Documentation

| Resource | Link |
|----------|------|
| User guides | [guides index](https://triplemodel.readthedocs.io/en/latest/guides/index.html) |
| API reference | [api](https://triplemodel.readthedocs.io/en/latest/api/index.html) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| Roadmap | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Ecosystem | [docs/ECOSYSTEM.md](docs/ECOSYSTEM.md) |

## License

MIT — see [LICENSE](LICENSE).
