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
print("round-trip OK")
