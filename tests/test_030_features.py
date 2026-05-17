"""Tests for TripleModel 0.3.0 features (lists, lang, opaque, bnode, skolem, ResourceRef)."""

from __future__ import annotations

import warnings
from typing import Annotated, Any

import pytest
from pydantic import ValidationError
from rdflib import BNode, Graph, Literal, RDF, URIRef, XSD

from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.config import get_rdf_config
from triplemodel.fields.resource_ref import ResourceRef
from triplemodel.io.import_ import _term_to_field, _union_conversion_order
from triplemodel.io.skolem import apply_de_skolemize, apply_skolemize
from triplemodel.metadata.cardinality import scalar_python_type, union_member_types
from triplemodel.terms import python_to_term, term_to_python
from triplemodel.terms.bnode import (
    nested_bnode_key,
    remove_bnode_subgraph,
    stable_bnode,
)
from triplemodel.terms.lang import Lang, LangString
from triplemodel.terms.opaque import OpaqueLiteral

DC = "http://purl.org/dc/terms/"
EX = "http://example.org/"
FOAF = "http://xmlns.com/foaf/0.1/"
ADDRESS = "http://example.org/address"


class Mailbox(TripleModel):
    class Rdf:
        namespace = "http://example.org/mailbox/"
        type_uri = "http://example.org/Mailbox"
        id_field = "slug"

    slug: str = "m1"
    address: str = rdf_field(ADDRESS)


class PersonBnodeStable(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        embed = "bnode"
        blank_node_policy = "stable"

    slug: str
    mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)


class Linked(TripleModel):
    class Rdf:
        namespace = EX
        id_field = "slug"

    slug: str
    ref: ResourceRef = rdf_field("http://example.org/ref")


class OpaqueHolder(TripleModel):
    class Rdf:
        namespace = EX
        id_field = "slug"

    slug: str
    data: OpaqueLiteral = rdf_field("http://example.org/data")


class CustomUnion(TripleModel):
    class Rdf:
        namespace = EX
        id_field = "slug"

    slug: str
    val: str | int = rdf_field("http://example.org/val")


def test_invalid_blank_node_policy_warns():
    class Weird(TripleModel):
        class Rdf:
            namespace = EX
            blank_node_policy = "bogus"

        slug: str

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cfg = get_rdf_config(Weird)
    assert cfg.blank_node_policy == "fresh"
    assert any("blank_node_policy" in str(x.message) for x in w)


def test_stable_bnode_same_id_when_nested_content_unchanged():
    mbox = Mailbox(address="a@example.org")
    p = PersonBnodeStable(slug="x", mbox=mbox)
    g = p.to_graph()
    subj = URIRef(p.subject_uri())
    pred = URIRef(f"{FOAF}mbox")
    first = next(iter(g.objects(subj, pred)))
    sync_to_graph(PersonBnodeStable(slug="x", mbox=mbox), g, mode="replace")
    second = next(iter(g.objects(subj, pred)))
    assert first == second


def test_clear_stale_bnode_when_mbox_cleared():
    p = PersonBnodeStable(slug="x", mbox=Mailbox(address="a@example.org"))
    g = p.to_graph()
    n = len(g)
    sync_to_graph(PersonBnodeStable(slug="x", mbox=None), g, mode="patch")
    assert len(g) < n
    assert PersonBnodeStable.from_graph(g, p.subject_uri()).mbox is None


def test_skolemize_and_de_skolemize():
    g = Graph()
    b = BNode()
    g.add((b, RDF.type, URIRef(f"{FOAF}Person")))
    sk = apply_skolemize(g, skolemize=True)
    assert apply_skolemize(g, skolemize=False) is g
    de = apply_de_skolemize(sk, de_skolemize=True)
    assert apply_de_skolemize(de, de_skolemize=False) is de


def test_resource_ref_roundtrip():
    inst = Linked(slug="a", ref=ResourceRef("http://example.org/resource/1"))
    restored = Linked.from_graph(inst.to_graph(), inst.subject_uri())
    assert restored.ref == ResourceRef("http://example.org/resource/1")
    assert str(restored.ref) == "http://example.org/resource/1"


def test_resource_ref_validation():
    invalid_ref: Any = ""
    with pytest.raises(ValidationError):
        Linked(slug="a", ref=invalid_ref)
    with pytest.raises(ValueError, match="must not be empty"):
        ResourceRef._validate("")
    assert ResourceRef._validate(ResourceRef("http://example.org/r")) == ResourceRef(
        "http://example.org/r"
    )
    assert ResourceRef._validate("http://example.org/other") == ResourceRef(
        "http://example.org/other"
    )
    term = python_to_term(ResourceRef("http://example.org/r"))
    assert isinstance(term, URIRef)


def test_opaque_literal_roundtrip():
    lit = Literal("payload", datatype=URIRef("http://example.org/customType"))
    opaque = OpaqueLiteral.from_literal(lit)
    assert opaque.datatype == "http://example.org/customType"
    assert OpaqueHolder(slug="a", data=opaque).data.value == "payload"
    term = python_to_term(opaque)
    restored = term_to_python(term, OpaqueLiteral)
    assert isinstance(restored, OpaqueLiteral)
    assert restored == opaque
    assert restored.to_literal().datatype == lit.datatype


def test_unknown_datatype_preserved_without_target_type():
    lit = Literal("x", datatype=URIRef("http://example.org/unknown"))
    result = term_to_python(lit, None)
    assert isinstance(result, OpaqueLiteral)


def test_html_xml_literal_as_str():
    html = Literal("<p>x</p>", datatype=RDF.HTML)
    html_str = term_to_python(html, str)
    assert isinstance(html_str, str)
    assert "x" in html_str
    xml = Literal("<r/>", datatype=RDF.XMLLiteral)
    assert term_to_python(xml, str) == "<r/>"


def test_lang_metadata_on_field():
    class Doc(TripleModel):
        class Rdf:
            namespace = EX
            id_field = "slug"

        slug: str
        title: Annotated[str, Lang("fr")] = rdf_field(f"{DC}title")

    d = Doc(slug="d", title="Bonjour")
    g = d.to_graph()
    from rdflib import Literal as RdfLiteral

    lit = list(g.objects(URIRef(d.subject_uri()), URIRef(f"{DC}title")))[0]
    assert isinstance(lit, RdfLiteral)
    assert lit.language == "fr"


def test_bnode_helpers():
    node = stable_bnode("key")
    assert stable_bnode("key") == node
    g = Graph()
    g.add((node, RDF.type, URIRef("http://example.org/T")))
    remove_bnode_subgraph(g, node)
    assert len(g) == 0
    assert nested_bnode_key("s", "p", object())  # noqa: B008


def test_union_conversion_order_helpers():
    assert _union_conversion_order(BNode(), (str, int)) == (str, int)
    lit = Literal("1", datatype=XSD.integer)
    assert _union_conversion_order(lit, (str, int))[0] is int
    lit2 = Literal("hi", datatype=XSD.string)
    assert _union_conversion_order(lit2, (str, int))[0] is str
    custom = Literal("x", datatype=XSD.decimal)
    assert _union_conversion_order(custom, (str, int)) == (str, int)


def test_term_to_field_union_failure():
    with pytest.raises(ValueError, match="Cannot convert object"):
        _term_to_field(
            BNode(),
            None,
            "val",
            "http://example.org/val",
            EX + "a",
            field_info=CustomUnion.model_fields["val"],
        )


def test_opaque_literal_without_datatype():
    plain = OpaqueLiteral("text", None)
    assert plain.to_literal().datatype is None


def test_langstring_without_lang_tag():
    term = python_to_term(LangString("plain", None))
    assert isinstance(term, Literal)
    assert term.language is None


def test_term_to_python_unknown_datatype_no_target():
    lit = Literal("v", datatype=URIRef("http://example.org/custom"))
    out = term_to_python(lit, None)
    assert isinstance(out, OpaqueLiteral)


def test_term_to_python_unknown_datatype_with_exotic_target():
    lit = Literal("v", datatype=URIRef("http://example.org/custom"))

    class Exotic:
        pass

    assert isinstance(term_to_python(lit, Exotic), OpaqueLiteral)


def test_python_to_term_opaque_and_resource_ref():
    opaque = OpaqueLiteral("x", str(XSD.string))
    assert isinstance(python_to_term(opaque), Literal)
    assert python_to_term(ResourceRef("http://example.org/r")) == URIRef(
        "http://example.org/r"
    )


def test_term_to_python_resource_ref_target():
    assert term_to_python(URIRef("http://example.org/r"), ResourceRef) == ResourceRef(
        "http://example.org/r"
    )
    assert term_to_python(Literal("http://example.org/r"), ResourceRef) == ResourceRef(
        "http://example.org/r"
    )


def test_term_to_field_without_field_info():
    assert (
        _term_to_field(
            Literal("x", datatype=XSD.string),
            str,
            "v",
            "http://example.org/v",
            EX + "a",
        )
        == "x"
    )
    assert (
        _term_to_field(
            Literal("y"),
            None,
            "v",
            "http://example.org/v",
            EX + "a",
            field_info=None,
        )
        is not None
    )


def test_bnode_cleanup_scalar_field_continue():
    from triplemodel.io.sync.nested_cleanup import (
        clear_nested_bnode_children,
        clear_stale_nested_bnode_children,
    )

    class Outer(TripleModel):
        class Rdf:
            namespace = EX
            embed = "bnode"
            id_field = "slug"

        slug: str
        label: str = rdf_field("http://example.org/label")
        mbox: Mailbox | None = rdf_field(f"{FOAF}mbox", default=None)

    cfg = get_rdf_config(Outer)
    outer = Outer(slug="a", label="A", mbox=Mailbox(address="a@example.org"))
    g = outer.to_graph()
    n = len(g)
    clear_nested_bnode_children(outer, g, outer.subject_uri(), config=cfg)
    assert len(g) < n
    clear_stale_nested_bnode_children(
        Outer(slug="a", label="A"), g, EX + "a", config=cfg
    )


def test_term_to_python_none_target_uses_registry():
    from unittest.mock import MagicMock

    from triplemodel.terms.registry import LiteralRegistry

    reg = MagicMock(spec=LiteralRegistry)
    reg.literal_to_python.return_value = "from-registry"
    lit = Literal("x")
    assert term_to_python(lit, None, registry=reg) == "from-registry"


def test_term_to_python_exotic_target_plain_literal():
    class Exotic:
        pass

    assert term_to_python(Literal("hi"), Exotic) == "hi"


def test_scalar_types_opaque_and_resource_ref():
    assert scalar_python_type(OpaqueHolder.model_fields["data"]) is OpaqueLiteral
    assert scalar_python_type(Linked.model_fields["ref"]) is ResourceRef
    assert union_member_types(CustomUnion.model_fields["val"]) == (str, int)


def test_skolem_kwargs_on_model_io():
    class P(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{FOAF}Person"
            id_field = "slug"
            skolemize_export = True
            skolemize_import = True

        slug: str
        name: str = rdf_field(f"{FOAF}name")

    p = P(slug="s", name="S")
    g = p.to_graph(skolemize=True)
    P.from_graph(g, p.subject_uri(), de_skolemize=True)


def test_nested_without_predicate_skips_bnode_cleanup():
    from triplemodel.io.sync.nested_cleanup import (
        clear_nested_bnode_children,
        clear_stale_nested_bnode_children,
    )

    class Inner(TripleModel):
        slug: str

    class Outer(TripleModel):
        class Rdf:
            namespace = EX
            embed = "bnode"
            id_field = "slug"

        slug: str
        inner: Inner | None = None

    cfg = get_rdf_config(Outer)
    g = Graph()
    clear_stale_nested_bnode_children(Outer(slug="a"), g, EX + "a", config=cfg)
    clear_nested_bnode_children(Outer(slug="a"), g, EX + "a", config=cfg)
