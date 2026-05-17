"""Tests for language-tagged literals."""

from __future__ import annotations

from typing import Annotated

from rdflib import Literal

from triplemodel import TripleModel, rdf_field
from triplemodel.terms import python_to_term
from triplemodel.terms.lang import Lang, LangString

DC = "http://purl.org/dc/terms/"
EX = "http://example.org/"


class Document(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{DC}BibliographicResource"
        id_field = "slug"

    slug: str
    title: LangString = rdf_field(f"{DC}title")


class TaggedTitle(TripleModel):
    class Rdf:
        namespace = EX
        id_field = "slug"

    slug: str
    title: Annotated[str, Lang("en")] = rdf_field(f"{DC}title")


def test_langstring_roundtrip():
    doc = Document(slug="d1", title=LangString("Hello", "en"))
    restored = Document.from_graph(doc.to_graph(), doc.subject_uri())
    assert restored.title == LangString("Hello", "en")


def test_annotated_lang_roundtrip():
    doc = TaggedTitle(slug="d1", title="Hello")
    g = doc.to_graph()
    from rdflib import URIRef

    lit = list(g.objects(URIRef(doc.subject_uri()), URIRef(f"{DC}title")))[0]
    assert isinstance(lit, Literal)
    assert lit.language == "en"  # noqa: SLF001 — rdflib Literal.language
    restored = TaggedTitle.from_graph(g, doc.subject_uri())
    assert restored.title == "Hello"


def test_python_to_term_langstring():
    term = python_to_term(LangString("Hi", "fr"))
    assert isinstance(term, Literal)
    assert term.language == "fr"


def test_lang_from_annotation_helper():
    from triplemodel.fields.metadata import lang_from_annotation

    assert lang_from_annotation(Annotated[str, Lang("de")]) == "de"
    assert lang_from_annotation(str) is None
    assert lang_from_annotation(Annotated[str, "not-a-lang-meta"]) is None
