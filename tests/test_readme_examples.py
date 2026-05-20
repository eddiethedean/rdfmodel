"""Executable checks for README (and doc) code examples."""

from __future__ import annotations

from typing import Annotated

from triplemodel.store import RdfGraph as Graph

from triplemodel import (
    Predicate,
    TripleModel,
    id_from_subject_uri,
    models_to_graph,
    rdf_field,
    subject_base,
)
from tests._type_uri import module_type_uri

PERSON_TYPE = module_type_uri("Person")

FOAF = "http://xmlns.com/foaf/0.1/"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = PERSON_TYPE
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{FOAF}name")
    age: int | None = rdf_field(f"{FOAF}age", default=None)


def test_readme_quick_start() -> None:
    """README § Quick start."""
    alice = Person(slug="alice", name="Alice", age=30)
    graph = alice.to_graph()
    assert alice.subject_uri() == "http://example.org/people/alice"
    assert Person.from_graph(graph, alice.subject_uri()) == alice
    assert len(Person.all_from_graph(graph)) == 1


def test_readme_uri_override() -> None:
    """README § Concepts — override subject with uri= (namespace-aligned)."""
    alice = Person(slug="alice", name="Alice", age=30)
    custom_uri = "http://example.org/people/alice"
    graph = alice.to_graph(uri=custom_uri)
    assert Person.from_graph(graph, custom_uri) == alice


def test_readme_subject_helpers() -> None:
    """README § Concepts — subject_base / id_from_subject_uri."""
    assert subject_base("http://example.org/people") == "http://example.org/people/"
    assert (
        id_from_subject_uri(
            "http://example.org/people",
            "http://example.org/people/alice",
        )
        == "alice"
    )


def test_readme_annotated_predicate() -> None:
    """README § Field → predicate — Annotated + Predicate."""

    class Document(TripleModel):
        class Rdf:
            namespace = "http://example.org/docs/"
            type_uri = "http://example.org/Doc"
            id_field = "slug"

        slug: str
        title: Annotated[str, Predicate("http://purl.org/dc/terms/title")]

    doc = Document(slug="x", title="Hello")
    g = doc.to_graph()
    restored = Document.from_graph(g, doc.subject_uri())
    assert restored.title == "Hello"


def test_readme_batch_export() -> None:
    """README § Examples — batch export."""
    people = [
        Person(slug="alice", name="Alice"),
        Person(slug="bob", name="Bob"),
    ]
    graph = models_to_graph(people)
    assert len(list(graph)) >= 4

    existing = Graph()
    models_to_graph(people, existing)
    assert len(list(existing)) >= 4


def test_readme_encoded_subject_ids() -> None:
    """README § Examples — encoded subject ids."""
    bob = Person(slug="bob jones", name="Bob")
    uri = bob.subject_uri()
    assert "%20" in uri
    restored = Person.from_graph(bob.to_graph(), uri)
    assert restored == bob


def test_readme_examples_script() -> None:
    """examples/readme_examples.py runs end-to-end."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    subprocess.run(
        [sys.executable, str(root / "examples" / "readme_examples.py")],
        cwd=root,
        check=True,
        env=env,
    )
