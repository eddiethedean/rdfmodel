"""Tests for strict import and warn_unmapped_fields."""

from __future__ import annotations

import pytest
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, graph_to_model, rdf_field
from triplemodel.config import RDF_TYPE

EX = "http://example.org/"


class StrictPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"
        strict_import = True

    slug: str
    name: str = rdf_field(f"{EX}name")


class WarnPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"
        warn_unmapped_fields = True

    slug: str
    name: str = rdf_field(f"{EX}name")


def _person_graph(extra_pred: str | None = None) -> Graph:
    g = Graph()
    subj = NamedNode(f"{EX}alice")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
    g.add((subj, NamedNode(f"{EX}name"), Literal("Alice")))
    if extra_pred:
        g.add((subj, NamedNode(extra_pred), Literal("extra")))
    return g


def test_strict_import_raises_on_unknown_predicate():
    g = _person_graph(f"{EX}unknown")
    with pytest.raises(ValueError, match="not mapped"):
        graph_to_model(g, StrictPerson, f"{EX}alice")


def test_warn_unmapped_fields():
    g = _person_graph(f"{EX}unknown")
    with pytest.warns(UserWarning, match="not mapped"):
        inst = graph_to_model(g, WarnPerson, f"{EX}alice")
    assert inst.name == "Alice"
