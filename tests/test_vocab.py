"""Tests for vocabulary re-exports."""

from __future__ import annotations

import triplemodel.vocab as vocab


def test_vocab_exports():
    assert vocab.FOAF is not None
    assert vocab.DC is not None
    assert "FOAF" in vocab.__all__
