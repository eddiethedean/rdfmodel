"""Tests for OntologyRegistry and apply_hints_to_model."""

from __future__ import annotations

from pathlib import Path

from pyoxigraph import BlankNode, NamedNode
from triplemodel.store import RdfGraph as Graph

from triplemodel import TripleModel, apply_hints_to_model, rdf_field
from triplemodel.config import RDFS
from triplemodel.config.constants import OWL
from triplemodel.fields.metadata import inverse_for_field
from triplemodel.io.rdfs import subclass_uris
from triplemodel.ontology_registry import OntologyRegistry

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ontology.ttl"
EX = "http://example.org/ontology/"
PART = f"{EX}partOf"
HAS = f"{EX}hasPart"
ANIMAL = f"{EX}Animal"
DOG = f"{EX}Dog"


def test_from_ttl_subtypes_and_inverse():
    reg = OntologyRegistry.from_ttl(FIXTURE)
    assert reg.subtypes_of(ANIMAL) == frozenset({ANIMAL, DOG})
    assert reg.inverse_of(HAS) == PART
    assert reg.inverse_of(PART) == HAS


def test_static_register_subclasses():
    reg = OntologyRegistry()
    reg.register_subclasses(ANIMAL, [DOG])
    reg.register_subclasses(DOG, [f"{EX}Puppy"])
    assert reg.subtypes_of(ANIMAL) == frozenset({ANIMAL, DOG, f"{EX}Puppy"})
    assert reg.subtypes_of(DOG) == frozenset({DOG, f"{EX}Puppy"})


def test_static_register_inverse():
    reg = OntologyRegistry()
    reg.register_inverse(HAS, PART)
    assert reg.inverse_of(HAS) == PART
    assert reg.inverse_of(PART) == HAS


def test_subtypes_of_vs_subclass_uris():
    g = Graph()
    animal, dog = NamedNode(ANIMAL), NamedNode(DOG)
    g.add((dog, NamedNode(f"{RDFS}subClassOf"), animal))
    reg = OntologyRegistry.from_graph(g)
    assert DOG in reg.subtypes_of(ANIMAL)
    supers = subclass_uris(g, DOG)
    assert ANIMAL in supers
    assert DOG in supers


def test_apply_hints_mutate():
    class Part(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}Part"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        has_part: str = rdf_field(f"{EX}hasPart")

    reg = OntologyRegistry.from_ttl(FIXTURE)
    applied = apply_hints_to_model(Part, reg, mutate=True)
    assert applied == {"has_part": PART}
    assert inverse_for_field(Part.model_fields["has_part"]) == PART


def test_apply_hints_does_not_overwrite_existing_inverse():
    class M(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}M"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        rel: str = rdf_field(f"{EX}hasPart", inverse=f"{EX}customInv")

    reg = OntologyRegistry.from_ttl(FIXTURE)
    assert apply_hints_to_model(M, reg, mutate=True) == {}


def test_apply_hints_overwrite():
    class M(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}M"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        rel: str = rdf_field(f"{EX}hasPart", inverse=f"{EX}customInv")

    reg = OntologyRegistry.from_ttl(FIXTURE)
    applied = apply_hints_to_model(M, reg, mutate=True, overwrite=True)
    assert applied == {"rel": PART}
    assert inverse_for_field(M.model_fields["rel"]) == PART


def test_inverse_of_unknown():
    reg = OntologyRegistry()
    assert reg.inverse_of("http://example.org/unknown") is None


def test_inverse_of_missing_on_loaded_graph():
    g = Graph()
    g.parse(str(FIXTURE), format="turtle")
    reg = OntologyRegistry.from_graph(g)
    assert reg.inverse_of(f"{EX}unknownProperty") is None


def test_static_subclass_cycle_skips_revisit():
    reg = OntologyRegistry()
    reg.register_subclasses("urn:a", ["urn:b"])
    reg.register_subclasses("urn:b", ["urn:a"])
    assert reg.subtypes_of("urn:a") == frozenset({"urn:a", "urn:b"})


def test_inverse_index_used_without_live_graph_lookup():
    reg = OntologyRegistry.from_ttl(FIXTURE)
    reg._graph = None
    assert reg.inverse_of(HAS) == PART


def test_inverse_of_live_graph_without_index_cache():
    g = Graph()
    g.parse(str(FIXTURE), format="turtle")
    reg = OntologyRegistry()
    reg._graph = g
    assert reg.inverse_of(HAS) == PART
    assert reg.inverse_of(PART) == HAS


def test_index_skips_non_named_inverse_subjects():
    g = Graph()
    bnode = BlankNode("inv1")
    g.add((bnode, NamedNode(f"{OWL}inverseOf"), NamedNode(PART)))
    reg = OntologyRegistry.from_graph(g)
    assert reg._graph_inverse_forward == {}
    assert reg.inverse_of(HAS) is None


def test_load_graph_clears_stale_graph_inverse_index():
    g_with_inverse = Graph()
    g_with_inverse.parse(str(FIXTURE), format="turtle")
    reg = OntologyRegistry.from_graph(g_with_inverse)
    assert reg.inverse_of(HAS) == PART

    g_empty = Graph()
    reg.load_graph(g_empty)
    assert reg.inverse_of(HAS) is None
    assert reg.inverse_of(PART) is None

    reg.register_inverse(HAS, PART)
    assert reg.inverse_of(HAS) == PART


def test_apply_hints_skips_unresolved_predicate_and_no_inverse():
    class NoPred(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}NoPred"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        plain: str

    class UnknownPrefix(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}UnknownPrefix"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        curie: str = rdf_field("missing:hasPart")

    class NoInversePred(TripleModel):
        class Rdf:
            namespace = EX
            type_uri = f"{EX}NoInversePred"
            id_field = "slug"
            prefixes = {"ex": EX}

        slug: str
        label: str = rdf_field(f"{EX}label")

    reg = OntologyRegistry.from_ttl(FIXTURE)
    assert apply_hints_to_model(NoPred, reg) == {}
    assert apply_hints_to_model(UnknownPrefix, reg) == {}
    assert apply_hints_to_model(NoInversePred, reg) == {}
