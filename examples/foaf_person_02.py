"""0.2.0 exit-criteria demo: multi-value nick, nested mbox, sync removes cleared age."""

from __future__ import annotations


from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.vocab import FOAF

EX = "http://example.org/people/"


class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field("http://example.org/address")


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}
        embed = "iri"

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    mbox: Mailbox | None = rdf_field("foaf:mbox", default=None)
    age: int | None = rdf_field("foaf:age", default=None)


def main() -> None:
    alice = Person(
        slug="alice",
        name="Alice",
        nick=["Al", "Alice"],
        mbox=Mailbox(address="alice@example.org"),
        age=30,
    )
    g = alice.to_graph()
    ttl = g.serialize(format="turtle")
    assert "PREFIX foaf:" in ttl or "foaf:" in ttl

    restored = Person.from_graph(g, alice.subject_uri())
    assert restored.nick == ["Al", "Alice"]
    assert restored.mbox is not None
    assert restored.mbox.address == "alice@example.org"

    alice.age = None
    sync_to_graph(alice, g, mode="replace")
    from pyoxigraph import NamedNode

    subj = NamedNode(alice.subject_uri())
    assert list(g.objects(subj, NamedNode(f"{FOAF}age"))) == []

    print("0.2.0 FOAF example OK")


if __name__ == "__main__":
    main()
