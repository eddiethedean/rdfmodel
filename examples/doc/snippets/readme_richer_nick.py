
from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.terms.lang import LangString
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
