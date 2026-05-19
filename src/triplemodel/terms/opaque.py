"""Preserve RDF literals with unknown or custom datatypes."""

from __future__ import annotations

from dataclasses import dataclass

from pyoxigraph import Literal, NamedNode

from triplemodel.store.terms import term_str


@dataclass(frozen=True)
class OpaqueLiteral:
    """A literal value preserved with its original datatype URI."""

    value: str
    datatype: str | None = None

    @classmethod
    def from_literal(cls, term: Literal) -> OpaqueLiteral:
        dt = term.datatype
        return cls(str(term.value), term_str(dt) if dt is not None else None)

    def to_literal(self) -> Literal:
        if self.datatype:
            return Literal(self.value, datatype=NamedNode(self.datatype))
        return Literal(self.value)
