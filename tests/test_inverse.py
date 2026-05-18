"""Inverse predicate import."""

from __future__ import annotations

import warnings

from rdflib import Graph, URIRef

from triplemodel import TripleModel, rdf_field, sync_to_graph
from triplemodel.config import RDF_TYPE
from triplemodel.fields import owned_predicates

EX = "http://example.org/"


class Employee(TripleModel):
    class Rdf:
        namespace = f"{EX}emp/"
        type_uri = f"{EX}Employee"
        id_field = "slug"

    slug: str
    manager: str | None = rdf_field(
        f"{EX}hasManager",
        inverse=f"{EX}manages",
        default=None,
    )


def test_import_via_inverse_predicate() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    bob_model = Employee.from_graph(g, str(bob))
    assert bob_model.slug == "bob"

    alice_model = Employee.from_graph(g, str(alice))
    assert alice_model.manager == str(bob)


def test_owned_predicates_includes_inverse() -> None:
    preds = owned_predicates(Employee)
    assert f"{EX}manages" in preds


def test_sync_replace_clears_inverse_links() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    alice_model = Employee(slug="alice", manager=None)
    sync_to_graph(alice_model, g, mode="replace")

    assert Employee.from_graph(g, str(alice)).manager is None
    assert (bob, URIRef(f"{EX}manages"), alice) not in g


def test_sync_patch_clears_inverse_links() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    alice_model = Employee(slug="alice", manager=None)
    sync_to_graph(alice_model, g, mode="patch")

    assert Employee.from_graph(g, str(alice)).manager is None
    assert (bob, URIRef(f"{EX}manages"), alice) not in g


class Team(TripleModel):
    class Rdf:
        namespace = f"{EX}team/"
        type_uri = f"{EX}Team"
        id_field = "slug"

    slug: str
    lead: str | None = rdf_field(
        f"{EX}hasLead",
        inverse=f"{EX}leadsTeam",
        default=None,
    )


class Department(TripleModel):
    class Rdf:
        namespace = f"{EX}dept/"
        type_uri = f"{EX}Department"
        id_field = "slug"
        embed = "iri"

    slug: str
    team: Team | None = rdf_field(f"{EX}hasTeam", default=None)


class DepartmentBnode(TripleModel):
    class Rdf:
        namespace = f"{EX}dept/"
        type_uri = f"{EX}DepartmentBnode"
        id_field = "slug"
        embed = "bnode"

    slug: str
    team: Team | None = rdf_field(f"{EX}hasTeam", default=None)


def test_sync_replace_clears_inverse_on_stale_nested_iri() -> None:
    team = Team(slug="eng")
    dept = Department(slug="d1", team=team)
    g = dept.to_graph()
    team_uri = URIRef(team.subject_uri())
    lead = URIRef(f"{EX}emp/lead")
    g.add((lead, URIRef(f"{EX}leadsTeam"), team_uri))

    sync_to_graph(Department(slug="d1", team=None), g, mode="replace")
    assert (lead, URIRef(f"{EX}leadsTeam"), team_uri) not in g


def test_sync_replace_clears_inverse_on_stale_nested_bnode() -> None:
    team = Team(slug="eng")
    dept = DepartmentBnode(slug="d1", team=team)
    g = dept.to_graph()
    team_bnode = next(
        o
        for o in g.objects(URIRef(dept.subject_uri()), URIRef(f"{EX}hasTeam"))
        if not isinstance(o, URIRef)
    )
    lead = URIRef(f"{EX}emp/lead")
    g.add((lead, URIRef(f"{EX}leadsTeam"), team_bnode))

    sync_to_graph(DepartmentBnode(slug="d1", team=None), g, mode="replace")
    assert (lead, URIRef(f"{EX}leadsTeam"), team_bnode) not in g


def test_sync_patch_clears_inverse_on_stale_nested_bnode() -> None:
    team = Team(slug="eng")
    dept = DepartmentBnode(slug="d1", team=team)
    g = dept.to_graph()
    team_bnode = next(
        o
        for o in g.objects(URIRef(dept.subject_uri()), URIRef(f"{EX}hasTeam"))
        if not isinstance(o, URIRef)
    )
    lead = URIRef(f"{EX}emp/lead")
    g.add((lead, URIRef(f"{EX}leadsTeam"), team_bnode))

    sync_to_graph(DepartmentBnode(slug="d1", team=None), g, mode="patch")
    assert (lead, URIRef(f"{EX}leadsTeam"), team_bnode) not in g


def test_sync_replace_clears_stale_inverse_on_manager_change() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    carol = URIRef(f"{EX}emp/carol")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((carol, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    sync_to_graph(Employee(slug="alice", manager=str(carol)), g, mode="replace")
    assert (bob, URIRef(f"{EX}manages"), alice) not in g
    assert (alice, URIRef(f"{EX}hasManager"), carol) in g


def test_sync_patch_clears_inverse_on_stale_nested_iri() -> None:
    team = Team(slug="eng")
    dept = Department(slug="d1", team=team)
    g = dept.to_graph()
    team_uri = URIRef(team.subject_uri())
    lead = URIRef(f"{EX}emp/lead")
    g.add((lead, URIRef(f"{EX}leadsTeam"), team_uri))

    sync_to_graph(Department(slug="d1", team=None), g, mode="patch")
    assert (lead, URIRef(f"{EX}leadsTeam"), team_uri) not in g


def test_import_forward_and_inverse_conflict_warns() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    carol = URIRef(f"{EX}emp/carol")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((alice, URIRef(f"{EX}hasManager"), bob))
    g.add((carol, URIRef(f"{EX}manages"), alice))

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model = Employee.from_graph(g, str(alice))
    assert len(w) == 1
    assert "forward predicate" in str(w[0].message).lower()
    assert model.manager == str(bob)


def test_field_clears_inverse_list_and_set_branches() -> None:
    from triplemodel.io.sync.inverse_ops import _field_clears_inverse

    assert _field_clears_inverse([], "list") is True
    assert _field_clears_inverse([None], "list") is True
    assert _field_clears_inverse(set(), "set") is True
    assert _field_clears_inverse("not-a-list", "list") is False
    assert _field_clears_inverse("bob", "scalar") is False
    assert _field_clears_inverse(None, "scalar") is True


def test_walk_embed_follows_bnode_link_in_graph() -> None:
    from triplemodel.config import get_rdf_config
    from triplemodel.fields.resolver import default_resolver
    from triplemodel.io.sync.inverse_ops import _walk_embed_instances

    class Inner(TripleModel):
        class Rdf:
            namespace = f"{EX}inner/"
            type_uri = f"{EX}Inner"
            id_field = "slug"

        slug: str

    class Outer(TripleModel):
        class Rdf:
            namespace = f"{EX}outer/"
            type_uri = f"{EX}Outer"
            id_field = "slug"
            embed = "bnode"

        slug: str
        inner: Inner | None = rdf_field(f"{EX}inner", default=None)

    outer = Outer(slug="o", inner=Inner(slug="i"))
    g = outer.to_graph()
    cfg = get_rdf_config(Outer)
    walked = list(
        _walk_embed_instances(
            outer, URIRef(outer.subject_uri()), cfg, g, default_resolver
        )
    )
    assert len(walked) == 2


def test_clear_inverse_bnode_embed_without_graph_link() -> None:
    class Inner(TripleModel):
        class Rdf:
            namespace = f"{EX}inner/"
            type_uri = f"{EX}Inner"
            id_field = "slug"

        slug: str
        note: str | None = rdf_field(
            f"{EX}note",
            inverse=f"{EX}invNote",
            default=None,
        )

    class Outer(TripleModel):
        class Rdf:
            namespace = f"{EX}outer/"
            type_uri = f"{EX}Outer"
            id_field = "slug"
            embed = "bnode"

        slug: str
        inner: Inner | None = rdf_field(f"{EX}inner", default=None)

    g = Graph()
    outer = Outer(slug="o", inner=Inner(slug="i", note=None))
    sync_to_graph(outer, g, mode="replace")


def test_clear_inverse_walk_skips_unmapped_nested_predicate() -> None:
    from triplemodel.io.sync.inverse_ops import clear_inverse_links

    class Inner(TripleModel):
        class Rdf:
            namespace = f"{EX}inner/"
            id_field = "slug"

        slug: str

    class Outer(TripleModel):
        class Rdf:
            namespace = f"{EX}outer/"
            type_uri = f"{EX}Outer"
            id_field = "slug"
            embed = "iri"

        slug: str
        inner: Inner | None = None

    g = Graph()
    outer = Outer.model_construct(slug="o", inner=Inner(slug="i"))
    clear_inverse_links(g, outer, subject=f"{EX}outer/o")


def test_clear_inverse_walk_skips_missing_bnode_link() -> None:
    from triplemodel.config import get_rdf_config
    from triplemodel.fields.resolver import default_resolver
    from triplemodel.io.sync.inverse_ops import (
        _walk_embed_instances,
        clear_inverse_links,
    )
    from triplemodel.terms.iri import subject_ref

    class Inner(TripleModel):
        class Rdf:
            namespace = f"{EX}inner/"
            type_uri = f"{EX}Inner"
            id_field = "slug"

        slug: str

    class Outer(TripleModel):
        class Rdf:
            namespace = f"{EX}outer/"
            type_uri = f"{EX}Outer"
            id_field = "slug"
            embed = "bnode"

        slug: str
        inner: Inner | None = rdf_field(f"{EX}inner", default=None)

    g = Graph()
    outer = Outer(slug="o", inner=Inner(slug="i"))
    cfg = get_rdf_config(Outer)
    subj = subject_ref(f"{EX}outer/o")
    walked = list(_walk_embed_instances(outer, subj, cfg, g, default_resolver))
    assert len(walked) == 1
    clear_inverse_links(g, outer, subject=f"{EX}outer/o")


def test_import_forward_inverse_conflict_raises() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    carol = URIRef(f"{EX}emp/carol")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((alice, URIRef(f"{EX}hasManager"), bob))
    g.add((carol, URIRef(f"{EX}manages"), alice))

    import pytest

    with pytest.raises(ValueError, match="forward predicate"):
        Employee.from_graph(g, str(alice), on_duplicate="error")


def test_sync_replace_clears_inverse_when_field_set() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))

    alice_model = Employee(slug="alice", manager=str(bob))
    sync_to_graph(alice_model, g, mode="replace")
    assert (bob, URIRef(f"{EX}manages"), alice) not in g
    assert (alice, URIRef(f"{EX}hasManager"), bob) in g


def test_inverse_on_list_field_rejected_at_class_definition() -> None:
    import pytest

    with pytest.raises(ValueError, match="inverse= is not supported on list"):

        class BadListInverse(TripleModel):
            class Rdf:
                namespace = EX
                id_field = "slug"

            slug: str
            tags: list[str] = rdf_field(
                f"{EX}tags",
                inverse=f"{EX}tagged",
                default_factory=list,
            )


def test_import_multiple_inverse_subjects_warns() -> None:
    g = Graph()
    alice = URIRef(f"{EX}emp/alice")
    bob = URIRef(f"{EX}emp/bob")
    carol = URIRef(f"{EX}emp/carol")
    g.add((alice, URIRef(RDF_TYPE), URIRef(f"{EX}Employee")))
    g.add((bob, URIRef(f"{EX}manages"), alice))
    g.add((carol, URIRef(f"{EX}manages"), alice))

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model = Employee.from_graph(g, str(alice))
    assert any("Multiple objects" in str(x.message) for x in w)
    assert model.manager == str(bob)
