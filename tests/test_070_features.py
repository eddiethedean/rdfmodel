"""Coverage for 0.7.0 graph algorithms and RDFS helpers."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel, Field
from pyoxigraph import Literal, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import (
    IriId,
    Transitive,
    TripleModel,
    VocabularyRegistry,
    cbd_model,
    graph_diff,
    graphs_equal,
    hydrate_refs,
    rdf_field,
    subclass_uris,
    transitive_subjects,
)
from triplemodel.fields import transitive_for_field
from triplemodel.config import RDF_TYPE
from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.io.import_ import graph_to_model
from triplemodel.io.rdfs import resolve_model_class_with_rdfs

EX = "http://ex.org/"
PART = f"{EX}partOf"


class Leaf(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Leaf"
        id_field = "slug"
        prefixes = {"ex": EX}

    slug: str
    parts: set[str] = rdf_field(PART, default_factory=set, transitive=True)


class Plain(BaseModel):
    x: int = 1


def test_graphs_equal_without_skolemize():
    g1 = Graph()
    g2 = Graph()
    g1.add((NamedNode(f"{EX}a"), NamedNode(f"{EX}p"), Literal(1)))
    g2.add((NamedNode(f"{EX}a"), NamedNode(f"{EX}p"), Literal(1)))
    assert graphs_equal(g1, g2, normalize_bnodes=False)


def test_graph_diff_equal_property():
    g = Graph()
    d = graph_diff(g, g)
    assert d.equal


def test_model_diff_requires_triplemodel():
    class NotTM(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}T"
            id_field = "slug"

        slug: str

    with pytest.raises(TypeError, match="TripleModel"):
        __import__("triplemodel.io.compare", fromlist=["model_diff"]).model_diff(
            Plain(), Plain()
        )


def test_cbd_model_dispatch():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}P"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{EX}name")

    g = Graph()
    s = NamedNode(f"{EX}a")
    g.add((s, NamedNode(RDF_TYPE), NamedNode(f"{EX}P")))
    g.add((s, NamedNode(f"{EX}name"), Literal("A")))
    inst = cbd_model(P, g, s, dispatch=True)
    assert inst.name == "A"


def test_hydrate_refs_resource_ref_and_empty_fields():
    class Country(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Country"
            id_field = "uri"

        uri: Annotated[str, IriId()]
        label: str = rdf_field(f"{EX}label")

    class X(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}X"
            id_field = "code"

        code: str
        country: ResourceRef | None = None

    g = Graph()
    c_uri = "http://example.org/c"
    g.add((NamedNode(c_uri), NamedNode(RDF_TYPE), NamedNode(f"{EX}Country")))
    g.add((NamedNode(c_uri), NamedNode(f"{EX}label"), Literal("C")))
    x = X(code="x", country=ResourceRef(c_uri))
    out = hydrate_refs([x], g, "country", spec={"country": Country})
    assert out[0].country is not None
    assert isinstance(out[0].country, Country)
    none_country = X(code="n", country=None)
    assert (
        hydrate_refs([none_country], g, "country", spec={"country": Country})[0]
        is none_country
    )
    assert hydrate_refs([x], g) == [x]


def test_hydrate_refs_edge_cases():
    class Country(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Country"
            id_field = "uri"

        uri: Annotated[str, IriId()]
        label: str = rdf_field(f"{EX}label")

    class X(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}X"
            id_field = "code"

        code: str
        link: str = ""

    assert hydrate_refs([], Graph()) == []
    g = Graph()
    x = X(code="x", link="http://example.org/c")
    g.add(
        (
            NamedNode("http://example.org/c"),
            NamedNode(RDF_TYPE),
            NamedNode(f"{EX}Country"),
        )
    )
    g.add((NamedNode("http://example.org/c"), NamedNode(f"{EX}label"), Literal("C")))
    out = hydrate_refs([x], g, "link", spec={"link": Country})
    country = out[0].link
    assert isinstance(country, Country)
    assert country.label == "C"

    with pytest.raises(ValueError, match="not a nested"):
        hydrate_refs([X(code="x", link="bad")], g, "link")

    y = X(code="y", link="")
    assert hydrate_refs([y], g, "link", spec={"link": Country})[0] is y
    z = X(code="z", link="not-a-uri")
    assert hydrate_refs([z], g, "link", spec={"link": Country})[0] is z


def test_ref_uri_subject_uri_and_resource_ref():
    from triplemodel.io.hydrate import _ref_uri

    assert _ref_uri(ResourceRef("http://example.org/c")) == "http://example.org/c"

    class BadUri:
        def subject_uri(self) -> str:
            raise ValueError("no id")

    assert _ref_uri(BadUri()) is None
    assert _ref_uri("urn:example:id") == "urn:example:id"


def test_transitive_set_import():
    g = Graph()
    root = NamedNode(f"{EX}root")
    a = NamedNode(f"{EX}a")
    b = NamedNode(f"{EX}b")
    g.add((root, NamedNode(RDF_TYPE), NamedNode(f"{EX}Leaf")))
    g.add((root, NamedNode(PART), a))
    g.add((a, NamedNode(PART), b))
    m = graph_to_model(g, Leaf, root)
    assert PART in str(m.parts) or len(m.parts) >= 1


def test_subclass_uris_and_transitive_subjects():
    g = Graph()
    a, b = NamedNode(f"{EX}a"), NamedNode(f"{EX}b")
    g.add((a, NamedNode(f"{EX}partOf"), b))
    from triplemodel.store.terms import term_str

    assert term_str(b) in subclass_uris(g, term_str(a)) or term_str(a) in subclass_uris(
        g, term_str(a)
    )
    subs = transitive_subjects(g, PART, b)
    assert term_str(a) in subs


def test_resolve_no_registered_type():
    g = Graph()
    s = NamedNode(f"{EX}unknown")
    g.add((s, NamedNode(RDF_TYPE), NamedNode(f"{EX}Nothing")))
    with pytest.raises(ValueError, match="No registered"):
        resolve_model_class_with_rdfs(g, s)


def test_transitive_for_field_metadata():
    from typing import Annotated as Ann

    class M(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}M"
            id_field = "slug"

        slug: str
        tags: set[str] = rdf_field(PART, default_factory=set, transitive=True)
        via_meta: Ann[set[str], Transitive()] = Field(default_factory=set)

    assert transitive_for_field(M.model_fields["tags"])
    assert transitive_for_field(M.model_fields["via_meta"])


def test_rdfs_pick_most_specific_empty_typed():
    from triplemodel.io.rdfs import _pick_most_specific

    class NoTypeA(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = ""
            id_field = "slug"

        slug: str

    class NoTypeB(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = ""
            id_field = "slug"

        slug: str

    g = Graph()
    picked = _pick_most_specific(g, [NoTypeA, NoTypeB])
    assert picked in (NoTypeA, NoTypeB)


def test_rdfs_no_candidate_exact_type():
    g = Graph()
    s = NamedNode(f"{EX}orphan")
    g.add((s, NamedNode(RDF_TYPE), NamedNode(f"{EX}Unregistered")))
    with pytest.raises(ValueError, match="No registered"):
        resolve_model_class_with_rdfs(g, s, use_subclass=False)


def test_vocabulary_registry_bind():
    reg = VocabularyRegistry()
    reg.register(Leaf)
    g = Graph()
    reg.bind_vocab(g)
    assert len(list(g.namespaces())) >= 1
