# TripleModel

[![CI](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/triplemodel/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/triplemodel)](https://pypi.org/project/triplemodel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://github.com/eddiethedean/triplemodel)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/eddiethedean/triplemodel/blob/main/LICENSE)
[![Documentation](https://readthedocs.org/projects/triplemodel/badge/?version=latest)](https://triplemodel.readthedocs.io/en/latest/?badge=latest)

**Typed Pydantic models for RDF.** Declare fields once, get correct triples in and out of [pyoxigraph](https://github.com/oxigraph/pyoxigraph) `Store` objects — no manual quad writes for every property.

| | |
|--|--|
| **Install** | `pip install triplemodel` |
| **Import** | `from triplemodel import TripleModel, rdf_field` |
| **Docs** | [triplemodel.readthedocs.io](https://triplemodel.readthedocs.io/) |

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

TripleModel is the **mapping layer** between Pydantic-shaped domain models and RDF triples: subject IRIs, XSD literals, nested resources, `rdf:List`, language tags, graph sync, and file parse/serialize. It is **stateless** (no ORM session); [SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (sessions, SPARQL, ORM) builds on top — see the [ecosystem guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/ECOSYSTEM.md).

> **0.10.0 is beta.** Public API is frozen from 0.9 until 1.0 — see [API stability](https://github.com/eddiethedean/triplemodel/blob/main/docs/API_STABILITY.md), [changelog](https://github.com/eddiethedean/triplemodel/blob/main/CHANGELOG.md), [migration guide](https://github.com/eddiethedean/triplemodel/blob/main/docs/MIGRATION_0.10.md), and [roadmap](https://github.com/eddiethedean/triplemodel/blob/main/docs/ROADMAP.md). Optional extra: `pip install triplemodel[shacl]`.

## Install

```bash
pip install triplemodel
```

**Requirements:** Python 3.10+, Pydantic 2, pyoxigraph 0.5+.

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

## Features

| Area | Capability |
|------|------------|
| **Mapping** | Nested `class Rdf` + `rdf_field()` or `Annotated[..., Predicate(...)]`; predicate validation at class definition |
| **Identity** | Subject IRIs from `namespace` + `id_field` (percent-encoded ids); `IriId` for full-IRI ids |
| **Scalars** | `str`, `int`, `float`, `bool`, `date`, `datetime`; IRI-like `str` → `URIRef`; `literal_datatype` (e.g. `xsd:gYear`) |
| **Collections** | `set[T]` → multiple objects per predicate; `list[T]` → ordered `rdf:List` |
| **Literals** | `LangString`, `Lang()`, `OpaqueLiteral`, `ResourceRef` |
| **Nesting** | Child `TripleModel` with `Rdf.embed` `"iri"` or `"bnode"`; `ref_field` for URI foreign keys |
| **Typing** | `Rdf.instance_of` for Wikidata-style property classification (`wdt:P31`, etc.) |
| **Graph writes** | `to_graph` / `sync_to_graph` with `add`, `replace`, or `patch` |
| **Namespaces** | `Rdf.prefixes`, CURIE predicates (`"foaf:name"`), `bind_namespaces` |
| **Named graphs** | `Rdf.graph_iri`, `to_dataset` / `from_dataset`, TriG / N-Quads via `Dataset` |
| **File I/O** | `parse` / `parse_file` / `parse_url`, `serialize`, `load_graph`, `load_dataset`, `load_models`, `load_models_from_graph`, `load_models_from_dataset`, `dump_model` (Turtle, TriG, N-Triples, JSON-LD, …) |
| **Dispatch** | `parse(..., dispatch=True)`, `graph_to_model_dispatch`, `all_from_graph_dispatch` by `rdf:type` |
| **Inverse predicates** | `rdf_field(..., inverse=...)` for import; forward predicate on export |
| **Validation** | Optional SHACL via `triplemodel[shacl]` and `shacl_shapes=` on export |
| **Package typing** | PEP 561 `py.typed` |
| **SPARQL** | `ask`, `construct_models`, `select_models`, `load_sparql`, `apply_update`, `prepare_model_query` |
| **Graph algorithms** | `graphs_equal`, `graph_diff`, `model_diff`, `cbd_graph` / `cbd_model`, `hydrate_refs`, `model_join` |
| **RDFS** | Subclass-aware dispatch, `transitive_objects` / `transitive_subjects`, `VocabularyRegistry`, `Transitive` import |
| **Scale & stores** | `iter_graph_to_models`, `load_models_streaming`, `parse_into_store_graph`, `open_graph` (`memory` / `disk`) |
| **Strict import** | `Rdf.strict_import`, `Rdf.warn_unmapped_fields` on `graph_to_model` |
| **Plugins** | `triplemodel.plugins` — `register_predicate_resolver`, literal/resource registration |
| **Codegen** | Experimental `triplemodel-codegen` CLI (OWL/RDFS → stub models) |

### `list` vs `set`

| Annotation | RDF shape |
|------------|-----------|
| `set[str]` | Multiple objects on one predicate (unordered) |
| `list[str]` | One ordered `rdf:List` (`rdf:first` / `rdf:rest`) |

Use **`set`** for tags or duplicate predicates; use **`list`** when the graph should contain a real RDF list.

## Full example

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
| `base_uri` | Default `publicID` for resolving relative IRIs on parse |
| `jsonld_context` | Default JSON-LD `@context` when `format` is json-ld |

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
| `to_graph(graph=None, *, uri=None, mode="add", ...)` | Serialize into a `Graph` |
| `sync_to_graph(graph, *, uri=None, mode="replace", ...)` | Sync owned triples in-place on this instance |
| `from_graph(graph, uri, *, resolver=, registry=, ...)` | Load one resource |
| `all_from_graph(graph, *, type_uri=None, resolver=, registry=, de_skolemize=, ...)` | Load all resources of this type |
| `parse` / `parse_file` / `parse_url` | Parse RDF and return `list[TripleModel]` (class methods; optional `dispatch=True`) |
| `serialize` | Write instance triples to a file or string |
| `rdf_config()` | Resolved `RdfConfig` |

### Common imports

```python
from triplemodel import (
    TripleModel,
    rdf_field,
    ref_field,
    Predicate,
    IriId,
    GraphMode,
    sync_to_graph,
    models_to_graph,
    load_graph,
    load_models,
    load_models_from_graph,
    load_models_from_dataset,
    load_dataset,
    parse_into_dataset,
    model_to_dataset,
    models_to_dataset,
    get_graph_context,
    graph_to_model_dispatch,
    all_from_graph_dispatch,
    ask,
    apply_update,
    construct_models,
    select_models,
    load_sparql,
    open_sparql_graph,
    prepare_model_query,
    run_sparql,
    init_bindings_from_model,
    init_ns_from_model,
    graph_from_construct_result,
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
from triplemodel import Store
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

**Multiple tags on one predicate** — use `set[str] = rdf_field("foaf:topic", default_factory=set)`.

**Runnable scripts:** [`examples/exit_criteria_03.py`](examples/exit_criteria_03.py), [`examples/readme_examples.py`](examples/readme_examples.py), [`examples/realworld/`](examples/realworld/) (Nobel, DCAT, Wikidata, Schema.org), and [`examples/doc/snippets/`](examples/doc/snippets/).

## TripleModel vs SparqlModel

| You need | Package |
|----------|---------|
| Pydantic ↔ triples on an in-memory `Graph` | **triplemodel** |
| File I/O, datasets, SPARQL sessions, cascade `put` | **[SparqlModel](https://github.com/eddiethedean/sqarqlmodel)** (planned TripleModel dependency) |

## Known limitations

- **Union queries** — `from_dataset` reads one named graph only; use `Dataset.query` for union semantics (see the [datasets guide](https://triplemodel.readthedocs.io/en/latest/guides/12-datasets-and-named-graphs.html)).
- **BNode embed** is experimental; prefer `embed="iri"` for stable linking.
- **Collections** — `list[T]` / `set[T]` require scalar `T`; `list[TripleModel]` and `set[TripleModel]` are not supported.
- **Inverse predicates** — import uses forward or inverse triples (forward wins on conflict); `sync_to_graph` in `add`, `replace`, or `patch` clears incoming inverse triples before writing forward predicates (including reassignment and dropped nested IRI/bnode children). Export writes forward predicates only.
- **Discovery** — `all_from_graph()` and dispatch discovery match subjects via forward owned predicates (and `rdf:type` / `instance_of`); resources reachable only through inverse triples are not discovered.
- **Dispatch parse** — `parse(..., dispatch=True)` loads every registered `rdf:type` (not only the class you call `.parse` on); `type_uri=` is ignored when `dispatch=True`.
- **Skolemize** — `skolemize` / `de_skolemize` on import or export mutate the **entire** shared `Graph`, not only the resource being loaded or synced. `sync_to_graph(..., mode="patch")` runs skolemize after cleanup and export; `replace` / `add` skolemize via `write_model_add` before appending new triples.
- **BNode embed + fresh policy** — with default `blank_node_policy="fresh"`, `replace` / `patch` remove and re-export nested blank nodes on every sync even when the nested value is unchanged; use `embed="iri"` or `blank_node_policy="stable"` for stable identities.
- **BNode subjects** are skipped by `all_from_graph()` and by `parse(..., dispatch=True)` / `all_from_graph_dispatch()`.
- **Subclass dispatch** — `parse(..., dispatch=True)` and `all_from_graph_dispatch()` resolve subjects via `Rdf.resolve_subclass` (RDFS closure when enabled); unregistered types are omitted without error.
- **Default add mode** does not remove stale triples — use `sync_to_graph` or `mode="replace"`.
- **`sync_to_graph()`** defaults to `replace` when `Rdf.graph_mode` is `"add"` (unlike `to_graph()`, which defaults to add).

Details: [user guides](https://triplemodel.readthedocs.io/en/latest/guides/index.html) · [RDF lists & lang](https://triplemodel.readthedocs.io/en/latest/guides/09-rdf-lists-and-lang.html).

## Development

```bash
git clone https://github.com/eddiethedean/triplemodel.git && cd triplemodel
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,shacl,docs]"
make ci              # pytest, lint, docs (matches GitHub Actions)
make release-check   # before tagging: examples + twine check
```

CI: Python 3.10–3.13. Release process: [RELEASING.md](RELEASING.md).

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
