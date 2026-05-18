# TripleModel

**Pydantic models for RDF graphs.** Map typed Python classes to [rdflib](https://rdflib.readthedocs.io/) triples and back — without hand-writing `graph.add` for every field.

```text
Person(slug="alice", name="Alice")  →  (ex:alice, foaf:name, "Alice")  →  Person(...)
```

| | |
|--|--|
| PyPI | `pip install triplemodel` |
| Python | 3.10+ |
| Status | Beta (0.8.x) |

```{toctree}
:hidden:
:maxdepth: 1
:caption: Start here

installation
quickstart
examples
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: User guide

guides/index
guides/01-getting-started
guides/02-mapping-fields-and-subjects
guides/03-multi-valued-fields
guides/04-updating-graphs
guides/05-nested-models
guides/06-namespaces-and-curies
guides/07-custom-literals-and-types
guides/08-working-with-graphs
guides/09-rdf-lists-and-lang
guides/10-file-io
guides/11-real-world-patterns
guides/12-datasets-and-named-graphs
guides/13-sparql-and-endpoints
guides/14-graph-algorithms-and-rdfs
guides/15-stores-scale-and-strict
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: API reference

api/index
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Project

changelog
ROADMAP
PLAN
ECOSYSTEM
ECOSYSTEM_SPARQLMODEL
contributing
releasing
```

## Features

- **Pydantic v2** with declarative RDF mapping (`class Rdf`, `rdf_field`, `Predicate`)
- **Multi-valued fields** — `set[T]` for multiple objects per predicate; `list[T]` for ordered `rdf:List`
- **Language tags & opaque literals** — `LangString`, `Lang()`, `OpaqueLiteral`, `ResourceRef`
- **Nested models** — embed child `TripleModel` resources (IRI or experimental blank node)
- **Sync modes** — `sync_to_graph` and `to_graph(..., mode=)` (`add`, `replace`, `patch`)
- **Prefixes & CURIEs** — `Rdf.prefixes`, compact predicates, Turtle `PREFIX` output
- **Literal registry** — `Decimal`, `UUID`, `Enum`, and custom types
- **Graph helpers** — `merge_graphs`, `graph_value`, `graph_set`, `objects_for_field`

[SparqlModel](https://github.com/eddiethedean/sqarqlmodel) (session / ORM layer) is planned to build on TripleModel — see {doc}`ECOSYSTEM`.

## Indices

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
