"""0.3.0 exit-criteria demo: DC title @lang, blank-node Address, ordered rdf:List nick."""

from __future__ import annotations


from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.terms.lang import LangString
from triplemodel.vocab import DC, FOAF

EX = "http://example.org/people/"


class Address(TripleModel):
    class Rdf:
        namespace = "http://example.org/address/"
        type_uri = "http://example.org/Address"
        id_field = "slug"

    slug: str = "home"
    street: str = rdf_field("http://example.org/street")


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "bnode"
        prefixes = {"foaf": str(FOAF), "dc": str(DC)}

    slug: str
    title: LangString = rdf_field(f"{DC}title")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    address: Address | None = rdf_field("http://example.org/home", default=None)


def main() -> None:
    person = Person(
        slug="alice",
        title=LangString("Alice's profile", "en"),
        nick=["Al", "Alice"],
        address=Address(street="1 Main St"),
    )
    g = person.to_graph()
    restored = Person.from_graph(g, person.subject_uri())
    assert restored.title == LangString("Alice's profile", "en")
    assert restored.nick == ["Al", "Alice"]
    assert restored.address is not None
    assert restored.address.street == "1 Main St"

    person.nick = ["Alice"]
    sync_to_graph(person, g, mode="replace")
    again = Person.from_graph(g, person.subject_uri())
    assert again.nick == ["Alice"]

    print("0.3.0 exit criteria OK")


if __name__ == "__main__":
    main()
