# RDFModel

**Pydantic models for RDF graphs** — declare your domain with type-safe Python models, serialize to [rdflib](https://github.com/RDFLib/rdflib) graphs, and hydrate back without hand-written triple plumbing.

Install the Python package **`rdfmodel`**:

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
graph = alice.to_graph()

same_person = Person.from_graph(graph, alice.subject_uri())
```

Use `Annotated` with `Predicate` if you prefer metadata on the type:

```python
from typing import Annotated
from rdfmodel import Predicate, RdfModel

class Document(RdfModel):
  class Rdf:
    namespace = "http://example.org/docs/"
    type_uri = "http://example.org/Document"
    id_field = "slug"

  slug: str
  title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]
```

Load every instance of an RDF class from a graph:

```python
people = Person.all_from_graph(graph)
```

## What’s in 0.1.x

- `RdfModel` base class (Pydantic v2)
- Field → predicate mapping via `rdf_field()` or `Predicate`
- Subject IRI from `Rdf.namespace` + `Rdf.id_field` (id values are percent-encoded in the path)
- `rdf:type` from `Rdf.type_uri`
- Round-trip for common XSD scalars (`str`, `int`, `float`, `bool`, `date`, `datetime`)
- String values that look like IRIs become `URIRef` objects in the graph

### Current limitations

- **Single value per predicate** — if a graph has multiple objects for the same predicate on one subject, only the first is imported (multi-valued fields are planned for 0.2.0).
- **Unmapped fields are omitted** — model fields without `rdf_field()` or `Predicate` are not written to or read from the graph.
- **Blank nodes** — BNode objects cannot be imported into `str` fields (support planned for 0.3.0).

Pre-**1.0.0** releases will wrap every [rdflib](https://github.com/RDFLib/rdflib) feature that fits typed Pydantic models (parsers, datasets, SPARQL, stores, and more). See [ROADMAP.md](ROADMAP.md) for the coverage matrix and path to **1.0.0**.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
