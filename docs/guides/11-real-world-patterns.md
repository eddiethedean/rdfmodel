# Real-world patterns (0.4.1)

Examples in [`examples/realworld/`](https://github.com/eddiethedean/triplemodel/blob/main/examples/realworld/README.md) demonstrate these APIs.

## One parse, many model classes

```python
from triplemodel import load_graph, load_models, load_models_from_graph

graph = load_graph("data.ttl", bind_prefixes=Laureate.Rdf.prefixes)
bundles = load_models_from_graph(graph, Laureate, NobelPrize)

# Or from a path (single Graph.parse):
bundles = load_models("data.ttl", Laureate, NobelPrize)
laureates = bundles[Laureate]
```

When loading multiple classes from a path, `load_models` parses once using the **first** model class’s `Rdf.prefixes` and `Rdf.base_uri`. Pass a shared prefix map on all involved models, or use `load_graph` + `load_models_from_graph` when vocabs differ.

Use `parse(..., dispatch=True)` when you want one heterogeneous list keyed by `rdf:type` registration, not separate buckets per class.

Subjects are discovered via forward mapped predicates (and `rdf:type` / `Rdf.instance_of`), not inverse predicates — resources that appear only as objects of inverse triples are omitted from `all_from_graph()` and dispatch loads.

## Wikidata-style typing (`instance_of`)

When data uses `wdt:P31` instead of `rdf:type`:

```python
class CapitalCity(TripleModel):
    class Rdf:
        namespace = "http://www.wikidata.org/entity/"
        type_uri = ""
        instance_of = "wdt:P31"
        instance_type_uri = "http://www.wikidata.org/entity/Q174844"
        id_field = "qid"
        prefixes = {"wd": "...", "wdt": "...", "rdfs": "..."}

cities = CapitalCity.all_from_graph(graph)
```

## URI foreign keys (`ref_field`)

```python
from triplemodel import ref_field

class CapitalCity(TripleModel):
    country: WikidataItem = ref_field("wdt:P17", model=WikidataItem)
```

Import hydrates the linked resource from the same graph. Export writes the URI link only (not the full country description).

`ref_field` always follows **URI** semantics on import (the object must be a `URIRef`), regardless of the parent model’s `Rdf.embed` setting. Parent `embed` applies only to full nested embeds, not foreign-key links.

## XSD partial dates (`gYear`)

```python
founding_year: int | None = rdf_field(
    "schema:foundingDate", default=None, literal_datatype="xsd:gYear"
)
```

Register `xsd` in `Rdf.prefixes` when using CURIE datatypes. `xsd:gYear` literals import as `int`; export emits `xsd:gYear` when the field value is an `int` with `literal_datatype="xsd:gYear"`.

## Mapping validation

Invalid property IRIs (for example `rdfs#` without a local name) fail at **class definition** with a clear error.
