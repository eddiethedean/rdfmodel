"""MultiLangString: multiple @lang literals on one predicate."""

from __future__ import annotations

import warnings

from pyoxigraph import Literal, NamedNode

from triplemodel import (
    MultiLangString,
    TripleModel,
    graph_value,
    model_to_triples,
    objects_for_field,
    rdf_field,
    sync_to_graph,
)
from triplemodel.terms import python_to_term
from triplemodel.terms.lang import LangString
from triplemodel.vocab import RDFS

EX = "http://example.org/"
RDFS_LABEL = f"{RDFS}label"


class Resource(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Resource"
        id_field = "slug"

    slug: str
    label: MultiLangString = rdf_field(RDFS_LABEL)


def test_multi_lang_roundtrip():
    res = Resource(
        slug="r1",
        label=MultiLangString({"en": "Hello", "fr": "Bonjour"}),
    )
    restored = Resource.from_graph(res.to_graph(), res.subject_uri())
    assert restored.label == MultiLangString(
        {
            "en": LangString("Hello", "en"),
            "fr": LangString("Bonjour", "fr"),
        }
    )


def test_multi_lang_model_to_triples():
    res = Resource(slug="r1", label=MultiLangString(en="A", de="B"))
    rows = [(s, p, o) for s, p, o in model_to_triples(res) if p == RDFS_LABEL]
    assert len(rows) == 2
    langs = set()
    for _s, _p, obj in rows:
        term = python_to_term(obj) if not isinstance(obj, Literal) else obj
        assert isinstance(term, Literal)
        assert term.language is not None
        langs.add(term.language)
    assert langs == {"en", "de"}


def test_multi_lang_import_duplicate_per_lang_warns():
    g = Resource(slug="x", label=MultiLangString()).to_graph()
    subj = NamedNode(f"{EX}x")
    pred = NamedNode(RDFS_LABEL)
    g.add((subj, pred, Literal("One", language="en")))
    g.add((subj, pred, Literal("Two", language="en")))
    g.add((subj, pred, Literal("Bonjour", language="fr")))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        restored = Resource.from_graph(g, f"{EX}x", on_duplicate="warn")
    assert len(w) == 1
    assert restored.label["en"] == LangString("One", "en")
    assert restored.label["fr"] == LangString("Bonjour", "fr")


def test_multi_lang_import_duplicate_error():
    g = Resource(slug="x", label=MultiLangString()).to_graph()
    subj = NamedNode(f"{EX}x")
    pred = NamedNode(RDFS_LABEL)
    g.add((subj, pred, Literal("One", language="en")))
    g.add((subj, pred, Literal("Two", language="en")))
    try:
        Resource.from_graph(g, f"{EX}x", on_duplicate="error")
    except ValueError as exc:
        assert "Conflicting values for language 'en'" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_multi_lang_sync_replace_clears_stale_lang():
    res = Resource(slug="r1", label=MultiLangString(en="Hi", fr="Salut"))
    g = res.to_graph()
    res.label = MultiLangString(en="Hello")
    sync_to_graph(res, g, mode="replace")
    restored = Resource.from_graph(g, res.subject_uri())
    assert restored.label == MultiLangString(en="Hello")
    assert "fr" not in restored.label.by_lang


def test_multi_lang_pydantic_dict_coercion():
    res = Resource.model_validate(
        {"slug": "r1", "label": {"en": "Hello", "fr": "Bonjour"}}
    )
    assert res.label["en"] == LangString("Hello", "en")


def test_multi_lang_direction_roundtrip():
    res = Resource(
        slug="r1",
        label=MultiLangString({"ar": LangString("مرحبا", "ar", direction="rtl")}),
    )
    g = res.to_graph()
    pred = NamedNode(RDFS_LABEL)
    lit = next(
        o
        for o in g.objects(NamedNode(res.subject_uri()), pred)
        if isinstance(o, Literal) and o.language == "ar"
    )
    assert lit.direction is not None
    restored = Resource.from_graph(g, res.subject_uri())
    assert restored.label["ar"].direction == "rtl"


def test_graph_value_and_objects_for_field():
    res = Resource(slug="r1", label=MultiLangString(en="A", de="B"))
    g = res.to_graph()
    uri = res.subject_uri()
    ml = graph_value(g, uri, RDFS_LABEL, Resource, "label")
    assert ml == MultiLangString(en="A", de="B")
    objs = objects_for_field(g, uri, Resource, "label")
    assert set(objs) == {LangString("A", "en"), LangString("B", "de")}


def test_python_to_term_multi_lang_raises():
    import pytest

    with pytest.raises(TypeError, match="MultiLangString"):
        python_to_term(MultiLangString(en="x"))


def test_multi_lang_mapping_api():
    ml = MultiLangString(en="A", fr="B")
    assert len(ml) == 2
    assert bool(ml)
    assert list(ml) == [("en", LangString("A", "en")), ("fr", LangString("B", "fr"))]
    assert ml.get("de") is None
    assert ml.get("de", LangString("x", "de")) == LangString("x", "de")
    assert not MultiLangString()


def test_multi_lang_pydantic_invalid_type():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Resource.model_validate({"slug": "r1", "label": 42})

    with pytest.raises(TypeError, match="Expected MultiLangString or dict"):
        MultiLangString._pydantic_validate(42, None)


def test_multi_lang_import_skips_non_literals():
    from triplemodel.io.import_ import import_multi_lang_field

    ml = import_multi_lang_field(
        [NamedNode(f"{EX}iri"), Literal("Hi", language="en")],
        "label",
        RDFS_LABEL,
        f"{EX}x",
        on_duplicate="first",
    )
    assert ml == MultiLangString(en="Hi")


def test_multi_lang_patch_clears_empty():
    from triplemodel.io.sync.modes import predicates_to_patch

    res = Resource(slug="r1", label=MultiLangString())
    assert RDFS_LABEL in predicates_to_patch(res)


def test_multi_lang_skips_untagged_literals():
    g = Resource(slug="x", label=MultiLangString()).to_graph()
    subj = NamedNode(f"{EX}x")
    pred = NamedNode(RDFS_LABEL)
    g.add((subj, pred, Literal("plain")))
    g.add((subj, pred, Literal("Tagged", language="en")))
    restored = Resource.from_graph(g, f"{EX}x")
    assert restored.label == MultiLangString(en="Tagged")
