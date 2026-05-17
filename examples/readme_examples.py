#!/usr/bin/env python3
"""Run all self-contained README examples. Executed by tests/test_readme_examples.py."""

from __future__ import annotations

from typing import Annotated

from rdflib import Graph

from triplemodel import (
    Predicate,
    TripleModel,
    id_from_subject_uri,
    models_to_graph,
    rdf_field,
    subject_base,
)

FOAF = "http://xmlns.com/foaf/0.1/"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


def quick_start() -> None:
    alice = Person(slug="alice", name="Alice", age=30)
    graph = alice.to_graph()
    print(alice.subject_uri())
    assert Person.from_graph(graph, alice.subject_uri()) == alice
    assert len(Person.all_from_graph(graph)) == 1


def uri_override() -> None:
    alice = Person(slug="alice", name="Alice")
    custom_uri = "http://example.org/people/alice"
    graph = alice.to_graph(uri=custom_uri)
    assert Person.from_graph(graph, custom_uri) == alice


def subject_helpers() -> None:
    assert subject_base("http://example.org/people") == "http://example.org/people/"
    assert (
        id_from_subject_uri(
            "http://example.org/people",
            "http://example.org/people/alice",
        )
        == "alice"
    )


def annotated_predicate() -> None:
    class Document(TripleModel):
        class Rdf:
            namespace = "http://example.org/docs/"
            type_uri = "http://example.org/Doc"
            id_field = "slug"

        slug: str
        title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]

    doc = Document(slug="x", title="Hello")
    g = doc.to_graph()
    assert Document.from_graph(g, doc.subject_uri()).title == "Hello"


def batch_export() -> None:
    people = [
        Person(slug="alice", name="Alice"),
        Person(slug="bob", name="Bob"),
    ]
    graph = models_to_graph(people)
    assert len(list(graph)) >= 4
    existing = Graph()
    models_to_graph(people, existing)
    assert len(list(existing)) >= 4


def encoded_subject_ids() -> None:
    bob = Person(slug="bob jones", name="Bob")
    uri = bob.subject_uri()
    assert "%20" in uri
    assert Person.from_graph(bob.to_graph(), uri) == bob


def main() -> None:
    quick_start()
    uri_override()
    subject_helpers()
    annotated_predicate()
    batch_export()
    encoded_subject_ids()
    print("All README examples OK.")


if __name__ == "__main__":
    main()
