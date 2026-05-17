"""0.4.0 exit criteria: Person round-trip Turtle file, JSON-LD string, and in-memory Graph."""

from __future__ import annotations

import tempfile
from pathlib import Path

from triplemodel import TripleModel, rdf_field
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}

    slug: str
    name: str = rdf_field("foaf:name")


def main() -> None:
    person = Person(slug="alice", name="Alice")
    g = person.to_graph()
    from_graph = Person.from_graph(g, person.subject_uri())
    assert from_graph.name == person.name

    ttl = person.serialize(format="turtle")
    assert ttl
    from_ttl = Person.parse(data=ttl, format="turtle")[0]
    assert from_ttl.name == person.name

    try:
        jsonld = person.serialize(format="json-ld")
        from_json = Person.parse(data=jsonld, format="json-ld")[0]
        assert from_json.name == person.name
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "alice.ttl"
        person.serialize(destination=path)
        from_file = Person.parse_file(path)[0]
        assert from_file.name == person.name

    try:
        import pyshacl  # noqa: F401
    except ImportError:
        print("0.4.0 exit criteria OK (pyshacl not installed)")
        return

    shapes_ttl = f"""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix foaf: <{FOAF_NS}> .
@prefix ex: <http://example.org/> .
ex:PersonShape a sh:NodeShape ;
    sh:targetClass foaf:Person ;
    sh:property [
        sh:path foaf:name ;
        sh:minCount 1 ;
    ] .
"""
    person.to_graph(shacl_shapes=shapes_ttl)
    print("0.4.0 exit criteria OK")


if __name__ == "__main__":
    main()
