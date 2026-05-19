"""Tests for TripleModel 0.4.1 real-world ergonomics."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from pyoxigraph import BlankNode as BNode, Literal, NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.config.constants import RDF_TYPE

from triplemodel import (
    TripleModel,
    load_graph,
    load_models,
    load_models_from_graph,
    rdf_field,
    ref_field,
)
from triplemodel.io.import_ import graph_to_models

ROOT = Path(__file__).resolve().parents[1]
REALWORLD = ROOT / "examples" / "realworld" / "data"
REALWORLD_SCRIPTS = ROOT / "examples" / "realworld"


def test_gmonth_and_gmonthday_import() -> None:
    from triplemodel.store.namespaces import XSD as RdfXSD

    class Event(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/Event"
            id_field = "slug"

        slug: str
        month: str = rdf_field(
            "http://ex/month", literal_datatype=str(RdfXSD.gMonth.value)
        )
        day: str = rdf_field(
            "http://ex/day", literal_datatype=str(RdfXSD.gMonthDay.value)
        )

    g = Graph()
    g.add(
        (NamedNode("http://ex/e1"), NamedNode(RDF_TYPE), NamedNode("http://ex/Event"))
    )
    g.add(
        (
            NamedNode("http://ex/e1"),
            NamedNode("http://ex/month"),
            Literal("--05", datatype=RdfXSD.gMonth),
        )
    )
    g.add(
        (
            NamedNode("http://ex/e1"),
            NamedNode("http://ex/day"),
            Literal("--05-17", datatype=RdfXSD.gMonthDay),
        )
    )
    ev = Event.from_graph(g, "http://ex/e1")
    assert ev.month == "--05"
    assert ev.day == "--05-17"


def test_gyear_imports_as_int() -> None:
    class Org(TripleModel):
        class Rdf:
            namespace = "https://example.org/org/"
            type_uri = "https://schema.org/NGO"
            id_field = "slug"

        slug: str
        year: int = rdf_field(
            "https://schema.org/foundingDate", literal_datatype="xsd:gYear"
        )

    g = Graph()
    g.parse(
        data=(
            "@prefix schema: <https://schema.org/> .\n"
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
            "<https://example.org/org/wwf> a schema:NGO ; "
            'schema:foundingDate "1961"^^xsd:gYear .'
        ),
        format="turtle",
    )
    org = Org.from_graph(g, "https://example.org/org/wwf")
    assert org.year == 1961


def test_load_models_from_graph_multi_class() -> None:
    class A(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/TypeA"
            id_field = "slug"

        slug: str
        name: str = rdf_field("http://ex/name")

    class B(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/TypeB"
            id_field = "slug"

        slug: str
        title: str = rdf_field("http://ex/title")

    ttl = """
    @prefix ex: <http://ex/> .
    ex:a1 a ex:TypeA ; ex:name "Alice" .
    ex:b1 a ex:TypeB ; ex:title "Book" .
    """
    g = Graph()
    g.parse(data=ttl, format="turtle")
    bundles = load_models_from_graph(g, A, B)
    assert len(bundles[A]) == 1
    assert cast(A, bundles[A][0]).name == "Alice"
    assert cast(B, bundles[B][0]).title == "Book"


def test_load_models_path_multi_class(tmp_path: Path) -> None:
    class A(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/TypeA"
            id_field = "slug"

        slug: str

    class B(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/TypeB"
            id_field = "slug"

        slug: str

    path = tmp_path / "mix.ttl"
    path.write_text(
        "@prefix ex: <http://ex/> .\nex:a1 a ex:TypeA .\nex:b1 a ex:TypeB .\n",
        encoding="utf-8",
    )
    bundles = load_models(path, A, B)
    assert isinstance(bundles, dict)
    assert len(bundles[A]) == 1
    assert len(bundles[B]) == 1


def test_instance_of_discovery() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Capital(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = "wdt:P31"
            instance_type_uri = f"{WD}Q174844"
            id_field = "qid"
            prefixes = {
                "wd": WD,
                "wdt": WDT,
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            }

        qid: str
        label_en: str | None = rdf_field("rdfs:label", default=None)

    g = Graph()
    g.parse(
        data=(
            f"@prefix wd: <{WD}> .\n"
            f"@prefix wdt: <{WDT}> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
            f'wd:Q90 rdfs:label "Paris"@en ; wdt:P31 wd:Q174844 .\n'
            f'wd:Q99 rdfs:label "Other"@en ; wdt:P31 wd:Q5 .\n'
        ),
        format="turtle",
    )
    capitals = graph_to_models(g, Capital, validate_type=False)
    assert len(capitals) == 1
    assert capitals[0].label_en == "Paris"


def test_ref_field_hydrates_nested() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Country(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            id_field = "qid"
            prefixes = {"wd": WD, "rdfs": "http://www.w3.org/2000/01/rdf-schema#"}

        qid: str
        label_en: str | None = rdf_field("rdfs:label", default=None)

    class City(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            id_field = "qid"
            prefixes = {
                "wd": WD,
                "wdt": WDT,
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            }

        qid: str
        country: Country = ref_field("wdt:P17", model=Country)

    g = Graph()
    g.parse(
        data=(
            f"@prefix wd: <{WD}> .\n"
            f"@prefix wdt: <{WDT}> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
            'wd:Q142 rdfs:label "France"@en .\n'
            'wd:Q90 rdfs:label "Paris"@en ; wdt:P17 wd:Q142 .\n'
        ),
        format="turtle",
    )
    city = City.from_graph(g, f"{WD}Q90", validate_type=False)
    assert city.country.label_en == "France"


def test_ref_field_import_ignores_parent_bnode_embed() -> None:
    EX = "http://ex/"

    class Child(TripleModel):
        class Rdf:
            namespace = f"{EX}c/"
            type_uri = f"{EX}Child"
            id_field = "slug"

        slug: str
        name: str = rdf_field(f"{EX}name")

    class Parent(TripleModel):
        class Rdf:
            namespace = f"{EX}p/"
            type_uri = f"{EX}Parent"
            id_field = "slug"
            embed = "bnode"

        slug: str
        kid: Child = ref_field(f"{EX}rel", model=Child)

    g = Graph()
    g.parse(
        data=(
            f"@prefix ex: <{EX}> .\n"
            f'<{EX}c/alice> a ex:Child ; ex:name "Alice" .\n'
            f"<{EX}p/p1> a ex:Parent ; ex:rel <{EX}c/alice> .\n"
        ),
        format="turtle",
    )
    parent = Parent.from_graph(g, f"{EX}p/p1")
    assert parent.kid.name == "Alice"


def test_ref_field_rejects_bnode_object() -> None:
    from triplemodel.io.import_ import import_field_value
    from triplemodel.metadata.cardinality import field_cardinality

    EX = "http://ex/"

    class Child(TripleModel):
        class Rdf:
            namespace = f"{EX}c/"
            type_uri = f"{EX}Child"
            id_field = "slug"

        slug: str

    class Parent(TripleModel):
        class Rdf:
            namespace = f"{EX}p/"
            type_uri = f"{EX}Parent"
            id_field = "slug"

        slug: str
        kid: Child = ref_field(f"{EX}rel", model=Child)

    fi = Parent.model_fields["kid"]
    assert field_cardinality(fi) == "ref"
    g = Graph()
    bnode = BNode()
    with pytest.raises(ValueError, match="expected a URI resource"):
        import_field_value(
            g,
            [bnode],
            fi,
            "kid",
            f"{EX}rel",
            f"{EX}p/p1",
            embed="iri",
            on_duplicate="warn",
        )


def test_ref_field_rejects_inverse() -> None:
    class Child(TripleModel):
        class Rdf:
            namespace = "http://ex/c/"
            type_uri = "http://ex/Child"
            id_field = "slug"

        slug: str

    with pytest.raises(ValueError, match="inverse="):

        class Parent(TripleModel):
            class Rdf:
                namespace = "http://ex/p/"
                type_uri = "http://ex/Parent"
                id_field = "slug"

            slug: str
            kid: Child = ref_field(
                "http://ex/rel", model=Child, inverse="http://ex/inv"
            )


def test_instance_of_validate_type_fails() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Item(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = "wdt:P31"
            instance_type_uri = f"{WD}Q999"
            id_field = "qid"
            prefixes = {"wd": WD, "wdt": WDT}

        qid: str

    g = Graph()
    g.parse(
        data=(f"@prefix wd: <{WD}> .\n@prefix wdt: <{WDT}> .\nwd:Q1 wdt:P31 wd:Q1 .\n"),
        format="turtle",
    )
    with pytest.raises(ValueError, match="instance_of"):
        Item.from_graph(g, f"{WD}Q1")


def test_instance_of_without_type_uri_filter() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Thing(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = "wdt:P31"
            id_field = "qid"
            prefixes = {"wd": WD, "wdt": WDT}

        qid: str

    g = Graph()
    g.parse(
        data=f"@prefix wd: <{WD}> .\n@prefix wdt: <{WDT}> .\nwd:Q1 wdt:P31 wd:Q2 .\n",
        format="turtle",
    )
    things = graph_to_models(g, Thing, validate_type=True)
    assert len(things) == 1


def test_load_models_requires_class() -> None:
    with pytest.raises(TypeError, match="at least one"):
        load_models("x.ttl")  # ty: ignore[no-matching-overload]


def test_load_models_from_graph_type_check() -> None:
    class NotModel:
        pass

    with pytest.raises(TypeError, match="TripleModel"):
        load_models_from_graph(Graph(), NotModel)  # ty: ignore[invalid-argument-type]


def test_validate_skips_fields_without_predicates() -> None:
    from typing import Annotated

    from pydantic import Field

    from triplemodel.fields.metadata import Predicate

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"
            prefixes = {"ex": "http://ex/"}

        slug: str
        ghost: str = Field()
        title: Annotated[str, Predicate("http://ex/title")]

    from triplemodel.fields.validation import validate_model_predicates

    validate_model_predicates(M)


def test_coverage_gaps_041() -> None:
    from typing import Annotated

    from triplemodel.config import RdfConfig
    from triplemodel.fields.metadata import Predicate, ref_link_for_field
    from triplemodel.fields.resolver import owned_predicates
    from triplemodel.fields.validation import validate_model_predicates
    from triplemodel.io.discovery import discover_subjects_by_instance_of

    assert discover_subjects_by_instance_of(Graph(), RdfConfig()) == []

    cfg = RdfConfig(instance_type_uri=("wd:Q1", ""))
    assert cfg.instance_type_uris == ("wd:Q1",)

    class WithPred(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            instance_of = "http://ex/instance"
            id_field = "slug"
            prefixes = {"ex": "http://ex/"}

        slug: str
        title: Annotated[str, Predicate("http://ex/title")]

    validate_model_predicates(WithPred)
    assert "http://ex/instance" in owned_predicates(WithPred)

    class WithInv(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"
            prefixes = {}

        slug: str
        name: str = rdf_field("http://ex/name", inverse="unknown:inv")

    validate_model_predicates(WithInv)

    class WithList(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"

        slug: str
        tags: list[str] = rdf_field("http://ex/tags")

    assert WithList(slug="s", tags=["a"]).to_triples()

    from pydantic.fields import FieldInfo

    fi = FieldInfo(annotation=str)
    assert ref_link_for_field(fi) is False

    class ChildRef(TripleModel):
        class Rdf:
            namespace = "http://ex/c/"
            type_uri = "http://ex/Child"
            id_field = "slug"

        slug: str

    class Parent(TripleModel):
        class Rdf:
            namespace = "http://ex/p/"
            type_uri = "http://ex/Parent"
            id_field = "slug"

        slug: str
        kid: ChildRef | None = ref_field("http://ex/rel", model=ChildRef, default=None)

    assert ref_link_for_field(Parent.model_fields["kid"]) is True

    class Unmapped(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"

        slug: str
        note: str  # no rdf mapping

    validate_model_predicates(Unmapped)

    parent = Parent(slug="p1")
    assert parent.kid is None
    triples = parent.to_triples()
    assert all(t[1] != "http://ex/rel" for t in triples)

    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Typed(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = "wdt:P31"
            instance_type_uri = f"{WD}Q1"
            id_field = "qid"
            prefixes = {"wd": WD, "wdt": WDT}

        qid: str

    g2 = Graph()
    g2.parse(
        data=f"@prefix wd: <{WD}> .\n@prefix wdt: <{WDT}> .\nwd:Q9 wdt:P31 wd:Q1 .\n",
        format="turtle",
    )
    Typed.from_graph(g2, f"{WD}Q9", validate_type=True)

    class Child2(TripleModel):
        class Rdf:
            namespace = "http://ex/c/"
            type_uri = "http://ex/Child2"
            id_field = "slug"

        slug: str

    class UsesBadExtra(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T2"
            id_field = "slug"

        slug: str
        link: Child2 = ref_field(
            "http://ex/l",
            model=Child2,
            json_schema_extra=cast(Any, 5),
        )


def test_predicate_has_local_name_helpers() -> None:
    from triplemodel.fields.validation import predicate_has_local_name

    assert predicate_has_local_name("http://ex.org/foo") is True
    assert predicate_has_local_name("http://ex.org/") is False
    assert predicate_has_local_name("nocolon") is False
    assert predicate_has_local_name("ex:term") is True


def test_instance_of_validate_without_type_uri_object() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class Thing(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = ("wdt:P31",)
            id_field = "qid"
            prefixes = {"wd": WD, "wdt": WDT}

        qid: str

    g = Graph()
    g.parse(
        data=f"@prefix wd: <{WD}> .\n@prefix wdt: <{WDT}> .\nwd:Q1 wdt:P31 wd:Q2 .\n",
        format="turtle",
    )
    things = graph_to_models(g, Thing)
    assert len(things) == 1


def test_export_literal_datatype_full_uri() -> None:
    class Doc(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/Doc"
            id_field = "slug"

        slug: str
        code: int = rdf_field(
            "http://ex/code",
            literal_datatype="http://www.w3.org/2001/XMLSchema#integer",
        )

    doc = Doc(slug="d", code=42)
    rows = doc.to_triples()
    assert cast(Literal, rows[-1][2]).datatype is not None


def test_predicate_curie_without_local_name_raises() -> None:
    with pytest.raises(ValueError, match="no local name"):

        class Bad(TripleModel):
            class Rdf:
                namespace = "http://ex/"
                type_uri = "http://ex/T"
                id_field = "slug"
                prefixes = {"ex": "http://ex/"}

            slug: str
            x: str = rdf_field("ex:")


def test_gyear_export_literal_datatype() -> None:
    from triplemodel.config.constants import XSD as XSD_IRI
    from triplemodel.store.namespaces import XSD as RdfXSD

    class Org(TripleModel):
        class Rdf:
            namespace = "https://example.org/org/"
            type_uri = "https://schema.org/NGO"
            id_field = "slug"
            prefixes = {"xsd": XSD_IRI}

        slug: str
        year: int = rdf_field(
            "https://schema.org/foundingDate", literal_datatype="xsd:gYear"
        )

    org = Org(slug="x", year=2000)
    rows = org.to_triples()
    year_rows = [r for r in rows if "foundingDate" in r[1]]
    assert len(year_rows) == 1
    assert cast(Literal, year_rows[0][2]).datatype == RdfXSD.gYear


def test_schema_org_ngos_gyear_from_bundled_ttl() -> None:
    SCHEMA = "https://schema.org/"

    class NgoOrganization(TripleModel):
        class Rdf:
            namespace = "https://example.org/org/"
            type_uri = f"{SCHEMA}NGO"
            id_field = "slug"
            prefixes = {"schema": SCHEMA}

        slug: str
        name: str = rdf_field("schema:name")
        founding_year: int | None = rdf_field(
            "schema:foundingDate", default=None, literal_datatype="xsd:gYear"
        )

    path = REALWORLD / "schema_org_ngos.ttl"
    ngos = NgoOrganization.parse_file(path)
    wwf = next(o for o in ngos if o.slug == "wwf")
    assert wwf.founding_year == 1961


def test_nobel_load_models_single_parse() -> None:
    import sys

    sys.path.insert(0, str(REALWORLD_SCRIPTS))
    from nobel_laureates import Laureate, NobelPrize  # noqa: E402  # ty: ignore[unresolved-import]

    path = REALWORLD / "nobel_laureates_1901.ttl"
    bundles = load_models(path, Laureate, NobelPrize)
    assert len(bundles[Laureate]) >= 1
    assert len(bundles[NobelPrize]) >= 1


def test_wikidata_capitals_instance_of_and_ref() -> None:
    WD = "http://www.wikidata.org/entity/"
    WDT = "http://www.wikidata.org/prop/direct/"

    class WikidataItem(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            id_field = "qid"
            prefixes = {"wd": WD, "rdfs": "http://www.w3.org/2000/01/rdf-schema#"}

        qid: str
        label_en: str | None = rdf_field("rdfs:label", default=None)

    class CapitalCity(TripleModel):
        class Rdf:
            namespace = WD
            type_uri = ""
            instance_of = "wdt:P31"
            instance_type_uri = f"{WD}Q174844"
            id_field = "qid"
            prefixes = {
                "wd": WD,
                "wdt": WDT,
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            }

        qid: str
        label_en: str | None = rdf_field("rdfs:label", default=None)
        population: int = rdf_field("wdt:P1082")
        country: WikidataItem = ref_field("wdt:P17", model=WikidataItem)

    path = REALWORLD / "wikidata_capitals.ttl"
    graph = load_graph(source=path, bind_prefixes=CapitalCity.Rdf.prefixes)
    cities = CapitalCity.all_from_graph(graph, validate_type=False)
    assert len(cities) == 2
    paris = next(c for c in cities if c.qid.endswith("Q90"))
    assert paris.country.label_en == "France"
