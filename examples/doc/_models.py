"""Shared models for documentation example snippets."""

from __future__ import annotations

from typing import Annotated

from triplemodel import IriId, TripleModel, rdf_field
from triplemodel.vocab import FOAF

FOAF_NS = str(FOAF)
EX = "http://example.org/people/"


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF_NS}Person"
        id_field = "slug"
        prefixes = {"foaf": FOAF_NS}
        embed = "iri"

    slug: str
    name: str = rdf_field("foaf:name")
    nick: list[str] = rdf_field("foaf:nick", default_factory=list)
    tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)
    age: int | None = rdf_field("foaf:age", default=None)
    mbox: "Mailbox | None" = rdf_field("foaf:mbox", default=None)


class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field("http://example.org/address")


class ExternalResource(TripleModel):
    class Rdf:
        namespace = "http://example.org/"
        type_uri = "http://example.org/External"
        id_field = "uri"

    uri: Annotated[str, IriId()]
    title: str = rdf_field("http://example.org/title")
