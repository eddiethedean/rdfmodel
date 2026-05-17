# Nested models

Embed another `TripleModel` as a field value (for example a `Mailbox` inside `Person`). TripleModel exports the child’s triples and links the parent to the child subject.

## IRI embedding (recommended)

Set `embed = "iri"` on the parent’s `Rdf` class (this is the default):

```python
from triplemodel import TripleModel, rdf_field
from triplemodel.vocab import FOAF

class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field("http://example.org/address")


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "iri"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)
```

```python
alice = Person(
    slug="alice",
    name="Alice",
    mbox=Mailbox(address="alice@example.org"),
)
graph = alice.to_graph()
restored = Person.from_graph(graph, alice.subject_uri())
assert restored.mbox.address == "alice@example.org"
```

The child subject IRI comes from the **child** model’s `Rdf` config (`namespace` + `id_field`), not the parent’s. Each nested type should define its own `class Rdf`.

## Optional nested field

`mbox: Mailbox | None = None` exports nothing when `None`. Under `sync_to_graph(..., mode="replace")`, the parent’s link triple is removed when you clear `mbox`.

## Blank node embedding (experimental)

```python
class Rdf:
    embed = "bnode"
```

The child is exported with a fresh blank node subject; import loads a bounded description around that node. Prefer **IRI embed** for stable round-trips and linking across graphs until **0.3** blank-node hardening lands.

## Multiple parents, one graph

```python
from triplemodel import models_to_graph

people = [alice, bob]  # each with its own Mailbox
graph = models_to_graph(people)
by_slug = {p.slug: p for p in Person.all_from_graph(graph)}
```

Each child mailbox keeps a distinct subject IRI when `slug` differs on the child model.

## Full example

See {doc}`../examples` (source: `examples/foaf_person_02.py` on GitHub) for nick (list), mbox (nested), prefixes, and clearing `age` with sync.

**Next:** [Namespaces and CURIEs →](06-namespaces-and-curies.md)
