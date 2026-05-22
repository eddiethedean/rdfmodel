# File I/O (parse and serialize)

TripleModel maps model classes to **pyoxigraph** parse and serialize so you can load and save RDF documents directly on a `Store` or `Dataset`.

## Serialize to a string or file

```python
from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"

class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF}

    slug: str
    name: str = rdf_field("foaf:name")

person = Person(slug="alice", name="Alice")
ttl = person.serialize(format="turtle")
person.serialize(destination="alice.ttl")
```

## Parse from a string, file, or URL

```python
people = Person.parse(data=ttl, format="turtle")
people = Person.parse_file("alice.ttl")
people = Person.parse_url("https://example.org/data.ttl")
```

Format is inferred from the file suffix when omitted (`.ttl` → Turtle, `.trig` → TriG, and so on). When the suffix is unknown to TripleModel’s map, ``infer_format`` falls back to [pyoxigraph ``RdfFormat.from_extension`` / ``from_media_type``](https://pyoxigraph.readthedocs.io/en/stable/).

### Parse flags

``parse_into_graph``, ``parse_url_into_graph``, dataset/model ``parse`` accept:

- ``lenient=True`` — tolerate certain syntax issues (pyoxigraph parser)
- ``without_named_graphs=True`` — drop named-graph structure on import
- ``rename_blank_nodes=True`` — rename blank nodes during parse

You can still pass additional pyoxigraph options via ``**format_kwargs``.

### Canonical N-Triples

``graph.serialize(format="nt")`` uses pyoxigraph’s canonical N-Triples writer — useful for stable file diffs of the same graph shape.

### URL fetch security

`parse_url` and `parse_url_into_graph` use Python’s `urllib` to fetch remote RDF. Do not pass untrusted URLs without your own allowlist or proxy controls — a malicious URL could target internal networks (SSRF). Load trusted content into a local `Store` first when data comes from users or external systems.

## Base URI for relative IRIs

Set `Rdf.base_uri` (or pass `base=` to `parse`) so relative IRIs in Turtle resolve correctly (`base_iri` on low-level `Store.parse`):

```python
class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        base_uri = "http://example.org/people/"
        ...
```

## JSON-LD context

`Rdf.jsonld_context` is kept for API compatibility but **does not affect** parse or serialize on the pyoxigraph backend (TripleModel 0.10). Setting it emits a `UserWarning`; JSON-LD uses only context embedded in the document.

## Subclass dispatch

When a document contains several `rdf:type` values and you have registered subclasses, use `dispatch=True`:

```python
instances = TripleModel.parse(data=ttl, format="turtle", dispatch=True)
```

Each subject is loaded as the most specific registered model class. **Note:** `Person.parse(..., dispatch=True)` loads **every** registered `rdf:type` in the graph, not only `Person`; `type_uri=` is ignored when `dispatch=True`.

Low-level helpers: `graph_to_model_dispatch` and `all_from_graph_dispatch` (accept `resolver=`, `registry=`, `de_skolemize=`).

## Import options on class methods

`from_graph`, `all_from_graph`, and `parse` / `parse_file` / `parse_url` accept `resolver=` and `registry=` for custom predicate resolution and literal conversion. `all_from_graph` and `graph_to_models` also accept `de_skolemize=`.

## Inverse predicates

Map `owl:inverseOf`-style data on import with `inverse=` on `rdf_field` or `InverseOf` metadata (not on `list` / `set` fields). Export writes only the forward predicate. On `sync_to_graph(..., mode="replace")` or `mode="patch"`, all incoming inverse triples for inverse fields are cleared before re-export (including reassignment and dropped nested IRI/bnode children). If both forward and inverse triples exist for the same field, import uses the forward objects and warns (or raises with `on_duplicate="error"`).

### Paired fields (`back_populates`)

For bidirectional navigation metadata across two model classes (SparqlModel `Relationship(..., back_populates=...)` parity), link the inverse-side field with `back_populates=` on `rdf_field`. This does **not** change import/export: one side still uses `inverse=` for reading inverse triples; the peer field declares the matching forward predicate.

```python
class Person(TripleModel):
    employer: str | None = rdf_field(
        "ex:employer",
        inverse="ex:employee",
        back_populates=inverse_pair("Organization", "linked_person"),
    )

class Organization(TripleModel):
    linked_person: str | None = rdf_field(
        "ex:employee",
        back_populates=inverse_pair("Person", "employer"),
    )
```

At class creation, TripleModel validates that each side’s `back_populates` points back to the other field and that `inverse=` predicates match the peer’s forward predicate. Optional `Rdf.ontology_registry = OntologyRegistry(...)` checks `owl:inverseOf` in the ontology file.

Read-only graph navigation (no ORM session):

```python
uris = subjects_via_back_populates(person, "employer", graph)
orgs = models_via_back_populates(person, "employer", graph)
```

Use a string model name in `inverse_pair("Organization", ...)` when the peer class is declared later in the same module. Single-field `inverse=` without a peer model remains valid for one-sided mappings.

## Multi-class load (one parse)

When one Turtle file contains several `rdf:type`s (Nobel laureates and prizes, DCAT catalog and datasets):

```python
from triplemodel import load_graph, load_models, load_models_from_graph

bundles = load_models("catalog.ttl", DataCatalog, Dataset, Distribution)
catalogs = bundles[DataCatalog]

graph = load_graph("catalog.ttl", bind_prefixes=DataCatalog.Rdf.prefixes)
bundles = load_models_from_graph(graph, DataCatalog, Dataset)
```

For a single heterogeneous list by registered `rdf:type`, use `parse_file(..., dispatch=True)` instead.

See {doc}`11-real-world-patterns` for Wikidata typing, `ref_field`, and XSD `gYear`.

## Module helpers

```python
from triplemodel import load_models, dump_model

people = load_models("people.ttl", Person)
dump_model(person, "out.ttl", format="turtle")
```
