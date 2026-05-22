"""Paired inverse metadata (back_populates) across two TripleModel classes."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import Field
from triplemodel.store import RdfGraph as Graph

from triplemodel import (
    OntologyRegistry,
    TripleModel,
    graph_to_model,
    inverse_pair,
    models_via_back_populates,
    rdf_field,
    subjects_via_back_populates,
)
from triplemodel.fields.back_populates import (
    BackPopulates,
    _PENDING_LINKS,
    back_populates_for_field,
    normalize_back_populates,
    store_back_populates_extra,
    subjects_via_back_populates,
)
from triplemodel.fields.metadata import inverse_for_field

EX = "http://example.org/hr/"
EMP = f"{EX}employer"
EE = f"{EX}employee"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ontology.ttl"


class BpOrgForResolve(TripleModel):
    """Module-level model for ``_resolve_model_qualname`` tests."""

    class Rdf:
        namespace = EX
        type_uri = f"{EX}BpOrgForResolve"
        id_field = "slug"
        prefixes = {"ex": EX}

    slug: str


@pytest.fixture(autouse=True)
def _clear_pending_back_populates() -> Iterator[None]:
    _PENDING_LINKS.clear()
    yield
    _PENDING_LINKS.clear()


def _define_models() -> tuple[type[TripleModel], type[TripleModel]]:
    class Person(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Person"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        employer: str | None = rdf_field(
            EMP,
            inverse=EE,
            back_populates=inverse_pair("Organization", "linked_person"),
            default=None,
        )

    class Organization(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Organization"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        linked_person: str | None = rdf_field(
            EE,
            back_populates=inverse_pair("Person", "employer"),
            default=None,
        )

    return Person, Organization


def test_person_organization_pair_metadata():
    Person, Organization = _define_models()
    assert _PENDING_LINKS == []
    p_info = Person.model_fields["employer"]
    o_info = Organization.model_fields["linked_person"]
    bp_p = back_populates_for_field(p_info, owner=Person)
    bp_o = back_populates_for_field(o_info, owner=Organization)
    assert bp_p is not None and bp_p.model is Organization and bp_p.field == "linked_person"
    assert bp_o is not None and bp_o.model is Person and bp_o.field == "employer"
    assert inverse_for_field(p_info) == EE
    assert inverse_for_field(o_info) is None


def test_mismatched_inverse_raises():
    with pytest.raises(ValueError, match="must match forward predicate"):

        class Person(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}Person"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            employer: str | None = rdf_field(
                EMP,
                inverse=f"{EX}wrongInverse",
                back_populates=inverse_pair("Organization", "linked_person"),
                default=None,
            )

        class Organization(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}Organization"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            linked_person: str | None = rdf_field(
                EE,
                back_populates=inverse_pair("Person", "employer"),
                default=None,
            )


def test_ontology_registry_validates_inverse_pair():
    reg = OntologyRegistry.from_ttl(FIXTURE)
    part_uri = "http://example.org/ontology/hasPart"
    part_of_uri = "http://example.org/ontology/partOf"

    class Part(TripleModel):
        class Rdf:
            namespace = "http://example.org/ontology/"
            type_uri = "http://example.org/ontology/Part"
            id_field = "slug"
            prefixes = {"ex": "http://example.org/ontology/"}
            ontology_registry = reg

        slug: str
        has_part: str | None = rdf_field(
            part_uri,
            inverse=part_of_uri,
            back_populates=inverse_pair("Whole", "part_of"),
            default=None,
        )

    class Whole(TripleModel):
        class Rdf:
            namespace = "http://example.org/ontology/"
            type_uri = "http://example.org/ontology/Whole"
            id_field = "slug"
            prefixes = {"ex": "http://example.org/ontology/"}
            ontology_registry = reg

        slug: str
        part_of: str | None = rdf_field(
            part_of_uri,
            inverse=part_uri,
            back_populates=inverse_pair("Part", "has_part"),
            default=None,
        )


def test_ontology_registry_mismatch_raises():
    reg = OntologyRegistry.from_ttl(FIXTURE)

    with pytest.raises(ValueError, match="must match forward predicate"):

        class Part(TripleModel):
            class Rdf:
                namespace = "http://example.org/ontology/"
                type_uri = "http://example.org/ontology/Part"
                id_field = "slug"
                prefixes = {"ex": "http://example.org/ontology/"}
                ontology_registry = reg

            slug: str
            has_part: str | None = rdf_field(
                "http://example.org/ontology/hasPart",
                inverse="http://example.org/ontology/partOf",
                back_populates=inverse_pair("Whole", "part_of"),
                default=None,
            )

        class Whole(TripleModel):
            class Rdf:
                namespace = "http://example.org/ontology/"
                type_uri = "http://example.org/ontology/Whole"
                id_field = "slug"
                prefixes = {"ex": "http://example.org/ontology/"}
                ontology_registry = reg

            slug: str
            part_of: str | None = rdf_field(
                "http://example.org/ontology/NOT-partOf",
                inverse="http://example.org/ontology/hasPart",
                back_populates=inverse_pair("Part", "has_part"),
                default=None,
            )


def test_import_and_navigate_inverse_side():
    Person, Organization = _define_models()
    from pyoxigraph import Literal, NamedNode

    g = Graph()
    org_uri = f"{EX}org/acme"
    person_uri = f"{EX}alice"
    from triplemodel.config import RDF_TYPE

    g.add((NamedNode(person_uri), NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
    g.add((NamedNode(person_uri), NamedNode(f"{EX}slug"), Literal("alice")))
    g.add((NamedNode(org_uri), NamedNode(RDF_TYPE), NamedNode(f"{EX}Organization")))
    g.add((NamedNode(org_uri), NamedNode(f"{EX}slug"), Literal("acme")))
    g.add((NamedNode(org_uri), NamedNode(EE), NamedNode(person_uri)))
    person = graph_to_model(g, Person, uri=person_uri)
    assert getattr(person, "employer") == org_uri
    assert subjects_via_back_populates(person, "employer", g) == [org_uri]
    org = models_via_back_populates(person, "employer", g)[0]
    assert getattr(org, "slug") == "org/acme"


def test_normalize_back_populates_tuple_and_type_error():
    Person, _ = _define_models()
    bp = normalize_back_populates((Person, "employer"))
    assert bp.model is Person and bp.field == "employer"
    with pytest.raises(TypeError, match="back_populates must be"):
        normalize_back_populates("invalid")  # type: ignore[arg-type]


def test_store_back_populates_with_class_ref():
    extra: dict[str, object] = {}
    Person, _ = _define_models()
    store_back_populates_extra(extra, BackPopulates("employer", Person))
    assert "Person" in str(extra["rdf_back_populates_model"])


def test_no_inverse_raises_for_navigation():
    Person, Organization = _define_models()
    g = Graph()

    class Solo(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Solo"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        peer: str | None = rdf_field(
            EMP,
            back_populates=inverse_pair(Organization, "linked_person"),
            default=None,
        )

    with pytest.raises(ValueError, match="no inverse predicate"):
        subjects_via_back_populates(
            Solo(slug="s"), "peer", g
        )


def test_back_populates_wrong_peer_model_raises():
    with pytest.raises(ValueError, match="must back_populates to"):

        class ChainA(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}ChainA"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            x: str | None = rdf_field(
                EMP,
                inverse=EE,
                back_populates=inverse_pair("ChainC", "z"),
                default=None,
            )

        class ChainC(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}ChainC"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            z: str | None = rdf_field(
                EE,
                back_populates=inverse_pair("ChainB", "y"),
                default=None,
            )

        class ChainB(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}ChainB"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            y: str | None = rdf_field(
                EE,
                inverse=EMP,
                back_populates=inverse_pair("ChainA", "x"),
                default=None,
            )


def test_asymmetric_back_populates_raises():
    with pytest.raises(ValueError, match="must back_populates to"):

        class A(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}A"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            w: str | None = rdf_field(
                EMP,
                back_populates=inverse_pair("B", "z"),
                default=None,
            )
            x: str | None = rdf_field(
                EMP,
                inverse=EE,
                back_populates=inverse_pair("B", "y"),
                default=None,
            )

        class B(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}B"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            y: str | None = rdf_field(
                EE,
                inverse=EMP,
                back_populates=inverse_pair("A", "w"),
                default=None,
            )
            z: str | None = rdf_field(EE, default=None)


def test_neither_side_inverse_raises():
    with pytest.raises(ValueError, match="at least one side needs inverse"):

        class A2(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}A2"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            x: str | None = rdf_field(
                EMP,
                back_populates=inverse_pair("B2", "y"),
                default=None,
            )

        class B2(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}B2"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            y: str | None = rdf_field(
                EE,
                back_populates=inverse_pair("A2", "x"),
                default=None,
            )


def test_back_populates_for_field_non_dict_extra():
    info = Field()
    info.json_schema_extra = cast(Any, "nope")
    assert back_populates_for_field(info) is None


def test_models_via_requires_back_populates():
    Person, _ = _define_models()
    g = Graph()
    with pytest.raises(ValueError, match="no back_populates metadata"):
        models_via_back_populates(Person(slug="a"), "slug", g)


def test_validate_link_returns_false_without_peer_back_populates():
    from triplemodel.fields.back_populates import _PendingLink, _validate_link

    class OnlyA(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}OnlyA"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        x: str | None = rdf_field(
            EMP,
            inverse=EE,
            back_populates=inverse_pair("OnlyB", "y"),
            default=None,
        )

    class OnlyB(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}OnlyB"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        y: str | None = rdf_field(EE, default=None)

    link = _PendingLink(
        owner=OnlyA,
        field="x",
        peer_model_qualname=f"{OnlyB.__module__}.OnlyB",
        peer_field="y",
    )
    assert _validate_link(link) is False


def test_validate_link_returns_false_for_unknown_peer():
    from triplemodel.fields.back_populates import _PendingLink, _validate_link

    Person, Organization = _define_models()
    link = _PendingLink(
        owner=Person,
        field="employer",
        peer_model_qualname="no.such.module.Organization",
        peer_field="linked_person",
    )
    assert _validate_link(link) is False
    bad_field = _PendingLink(
        owner=Person,
        field="employer",
        peer_model_qualname=f"{Organization.__module__}.Organization",
        peer_field="no_such_field",
    )
    assert _validate_link(bad_field) is False


def test_validate_link_missing_owner_field_raises():
    from triplemodel.fields.back_populates import _PendingLink, _validate_link

    Person, Organization = _define_models()
    link = _PendingLink(
        owner=Person,
        field="no_such_field",
        peer_model_qualname=f"{Organization.__module__}.Organization",
        peer_field="linked_person",
    )
    with pytest.raises(ValueError, match="references missing field"):
        _validate_link(link)


def test_models_via_resolves_string_peer_model(monkeypatch):
    Person, _ = _define_models()
    monkeypatch.setattr(
        "triplemodel.fields.back_populates.back_populates_for_field",
        lambda _fi, owner=None: BackPopulates("linked_person", "Organization"),
    )
    assert models_via_back_populates(Person(slug="a"), "employer", Graph()) == []


def test_navigation_unknown_field_raises():
    Person, _ = _define_models()
    with pytest.raises(ValueError, match="no field"):
        subjects_via_back_populates(Person(slug="a"), "missing", Graph())
    with pytest.raises(ValueError, match="no field"):
        models_via_back_populates(Person(slug="a"), "missing", Graph())


def test_resolve_model_qualname_from_module_attr():
    from triplemodel.fields.back_populates import _resolve_model_qualname

    qn = f"{BpOrgForResolve.__module__}.BpOrgForResolve"
    assert _resolve_model_qualname(qn) is BpOrgForResolve


def test_back_populates_resolve_lookup_error():
    info = Field(
        json_schema_extra={
            "rdf_back_populates_field": "x",
            "rdf_back_populates_model": "no.such.module.Foo",
        }
    )
    assert back_populates_for_field(info) is None


def test_validate_predicate_pair_ontology_owner_mismatch():
    from triplemodel.fields.back_populates import _validate_predicate_pair

    reg = OntologyRegistry.from_ttl(FIXTURE)
    part_uri = "http://example.org/ontology/hasPart"
    part_of_uri = "http://example.org/ontology/partOf"
    reg.register_inverse(part_uri, "http://example.org/ontology/wrong")
    Person, Organization = _define_models()
    with pytest.raises(ValueError, match="ontology inverse_of"):
        _validate_predicate_pair(
            Person,
            "employer",
            part_uri,
            part_of_uri,
            Organization,
            "linked_person",
            part_of_uri,
            part_uri,
            registry=reg,
        )


def test_back_populates_pair_requires_predicates():
    with pytest.raises(ValueError, match="requires rdf_predicate on both fields"):

        class PredA(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}PredA"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            x: str | None = rdf_field(
                EMP,
                inverse=EE,
                back_populates=inverse_pair("PredB", "y"),
                default=None,
            )

        class PredB(TripleModel):
            class Rdf:
                namespace = EX
                type_uri = f"{EX}PredB"
                id_field = "slug"
                prefixes = {"ex": EX}

            slug: str
            y: str | None = Field(
                default=None,
                json_schema_extra={
                    "rdf_back_populates_field": "x",
                    "rdf_back_populates_model": "PredA",
                },
            )


def test_ontology_registry_inverse_mismatch_on_forward():
    reg = OntologyRegistry.from_ttl(FIXTURE)
    part_uri = "http://example.org/ontology/hasPart"
    part_of_uri = "http://example.org/ontology/partOf"
    reg.register_inverse(part_of_uri, "http://example.org/ontology/wrongInverse")
    with pytest.raises(ValueError, match="ontology inverse_of"):

        class OntoPart(TripleModel):
            class Rdf:
                namespace = "http://example.org/ontology/"
                type_uri = "http://example.org/ontology/OntoPart"
                id_field = "slug"
                prefixes = {"ex": "http://example.org/ontology/"}
                ontology_registry = reg

            slug: str
            has_part: str | None = rdf_field(
                part_uri,
                inverse=part_of_uri,
                back_populates=inverse_pair("OntoWhole", "part_of"),
                default=None,
            )

        class OntoWhole(TripleModel):
            class Rdf:
                namespace = "http://example.org/ontology/"
                type_uri = "http://example.org/ontology/OntoWhole"
                id_field = "slug"
                prefixes = {"ex": "http://example.org/ontology/"}
                ontology_registry = reg

            slug: str
            part_of: str | None = rdf_field(
                part_of_uri,
                inverse=part_uri,
                back_populates=inverse_pair("OntoPart", "has_part"),
                default=None,
            )
