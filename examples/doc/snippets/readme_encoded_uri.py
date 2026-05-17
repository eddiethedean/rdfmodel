from triplemodel import TripleModel, rdf_field

FOAF = "http://xmlns.com/foaf/0.1/"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")


bob = Person(slug="bob jones", name="Bob")
print(bob.subject_uri())
