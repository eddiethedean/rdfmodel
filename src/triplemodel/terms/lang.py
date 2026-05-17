"""Language-tagged RDF literals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    """Field metadata: serialize ``str`` values with a fixed language tag."""

    code: str


@dataclass(frozen=True)
class LangString:
    """A literal string value with an optional language tag."""

    value: str
    lang: str | None = None
