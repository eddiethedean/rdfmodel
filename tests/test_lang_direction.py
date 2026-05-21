"""LangString text direction round-trip."""

from __future__ import annotations

from pyoxigraph import Literal

from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.lang import LangString


def test_langstring_direction_roundtrip() -> None:
    ls = LangString("hello", lang="en", direction="ltr")
    term = python_to_term(ls)
    assert isinstance(term, Literal)
    assert term.language == "en"
    assert str(term.direction).lower() == "ltr"
    back = term_to_python(term, LangString)
    assert back == ls


def test_invalid_direction_raises() -> None:
    try:
        LangString("x", direction="up")
    except ValueError as exc:
        assert "direction" in str(exc)
    else:
        raise AssertionError("expected ValueError")
