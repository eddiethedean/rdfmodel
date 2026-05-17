"""Tests targeting remaining coverage branches."""

from __future__ import annotations

from enum import Enum
from typing import Union

import pytest
from rdflib import Graph

from triplemodel import TripleModel, model_to_graph, rdf_field
from triplemodel._cardinality import (
    element_type,
    field_cardinality,
    nested_model_type,
    scalar_python_type,
    unwrap_annotation,
)
from triplemodel._config import RdfConfig, get_rdf_config
from triplemodel._embed import add_nested_to_graph
from triplemodel._graph_ops import objects_for_field
from triplemodel._namespaces import expand_curie, resolve_predicate
from triplemodel._registry import converter_for_type, python_to_literal
from triplemodel._sync import predicates_to_patch, sync_to_graph
from triplemodel._types import python_to_term, term_to_python
from rdflib import Literal, XSD

FOAF = "http://xmlns.com/foaf/0.1/"
EX = "http://example.org/people/"


def test_unwrap_union_multi_member():
    assert unwrap_annotation(str | int) == (str | int)


def test_element_type_non_generic():
    assert element_type(int) is int


def test_is_triple_model_type_non_type():
    from triplemodel._cardinality import is_triple_model_type

    assert is_triple_model_type(Union[str, int]) is False


class _Holder(TripleModel):
    val: str | int = rdf_field("http://example.org/v")


def test_scalar_python_type_union_field():
    assert scalar_python_type(_Holder.model_fields["val"]) is None


def test_nested_model_type_non_nested():
    assert nested_model_type(_Holder.model_fields["val"]) is None


def test_field_cardinality_union_scalar():
    assert field_cardinality(_Holder.model_fields["val"]) == "scalar"


def test_config_subject_uri_full_iri_id():
    cfg = RdfConfig(namespace=EX, id_field="slug")
    inst = type("I", (), {"slug": "http://example.org/people/alice"})()
    assert cfg.subject_uri(inst) == "http://example.org/people/alice"


def test_get_rdf_config_invalid_embed_and_mode():
    import warnings

    class Weird(TripleModel):
        class Rdf:
            namespace = EX
            embed = "invalid"
            graph_mode = "invalid"

        slug: str

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cfg = get_rdf_config(Weird)
    assert cfg.embed == "iri"
    assert cfg.graph_mode == "add"
    assert len(w) == 2


def test_rdf_graph_mode_drives_to_graph_without_explicit_mode():
    class PatchPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            graph_mode = "patch"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        age: int | None = rdf_field(f"{FOAF}age", default=None)

    p = PatchPerson(slug="a", name="A", age=30)
    g = p.to_graph()
    p2 = PatchPerson(slug="a", name="A", age=None)
    p2.to_graph(g)
    from rdflib import URIRef

    subj = URIRef(EX + "a")
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []


def test_rdf_graph_mode_patch_on_sync_to_graph():
    from rdflib import URIRef

    from triplemodel import sync_to_graph

    class PatchPerson(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            graph_mode = "patch"

        slug: str
        name: str = rdf_field(f"{FOAF}name")
        age: int | None = rdf_field(f"{FOAF}age", default=None)

    p = PatchPerson(slug="a", name="A", age=30)
    g = p.to_graph()
    sync_to_graph(PatchPerson(slug="a", name="A", age=None), g, mode=None)
    subj = URIRef(EX + "a")
    assert list(g.objects(subj, URIRef(f"{FOAF}age"))) == []


def test_freeze_prefixes_non_mapping():
    from triplemodel._config import _freeze_prefixes

    assert dict(_freeze_prefixes(None)) == {}
    assert dict(_freeze_prefixes([("ex", EX)])) == {}


def test_expand_curie_hash_namespace():
    assert (
        expand_curie("ex:Thing", {"ex": "http://example.org"})
        == "http://example.org#Thing"
    )


def test_resolve_predicate_no_colon():
    assert resolve_predicate("http://example.org/p", {}) == "http://example.org/p"


def test_model_to_graph_replace_mode():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    p = P(slug="a", name="A")
    g = model_to_graph(p, mode="replace")
    assert len(g) >= 2


def test_sync_bind_on_new_graph():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            prefixes = {"foaf": FOAF}

        slug: str
        name: str = rdf_field("foaf:name")

    p = P(slug="a", name="A")
    g = sync_to_graph(p, mode="replace", bind=True)
    assert len(g) >= 1


def test_predicates_to_patch_empty_set():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        tags: set[str] = rdf_field("http://example.org/t", default_factory=set)

    p = P(slug="a", tags=set())
    assert "http://example.org/t" in predicates_to_patch(p)


def test_add_nested_to_graph():
    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str = "b"
        v: str = rdf_field("http://example.org/v")

    class P(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        box: Box | None = None

    g = Graph()
    add_nested_to_graph(g, EX + "p", "http://example.org/has", Box(slug="b", v="x"))
    assert len(g) >= 1


def test_import_nested_invalid_term():
    from triplemodel._embed import import_nested_value
    from rdflib import Literal

    class Box(TripleModel):
        class Rdf:
            namespace = "http://example.org/box/"
            id_field = "slug"

        slug: str = "b"

    with pytest.raises(ValueError, match="Cannot import nested"):
        import_nested_value(Graph(), Literal("x"), Box, embed="iri")


def test_objects_for_field_no_predicate():
    class P(TripleModel):
        slug: str

    with pytest.raises(ValueError, match="no RDF predicate"):
        objects_for_field(Graph(), EX + "a", P, "slug")


def test_registry_no_converter():
    assert python_to_literal(1, str) is None
    assert converter_for_type(str) is None


def test_python_to_term_enum_fallback():
    class C(Enum):
        X = "x"

    term = python_to_term(C.X)
    assert isinstance(term, Literal)


def test_term_to_python_registry_path():
    from decimal import Decimal

    lit = Literal("1.0", datatype=XSD.decimal)
    assert term_to_python(lit, Decimal) == Decimal("1.0")


def test_resolve_field_predicate_with_prefixes():
    from triplemodel._fields import resolve_field_predicate as rfp

    class P(TripleModel):
        name: str = rdf_field("foaf:name")

    assert rfp(P.model_fields["name"], {"foaf": FOAF}) == f"{FOAF}name"
