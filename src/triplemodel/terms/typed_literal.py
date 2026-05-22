"""Per-object XSD datatypes for multi-valued literal fields."""

from __future__ import annotations

from dataclasses import dataclass

from pyoxigraph import Literal, NamedNode

from triplemodel.store.namespaces import XSD
from triplemodel.store.terms import term_str

_XSD_STRING = str(XSD.string.value)


@dataclass(frozen=True)
class TypedLiteral:
    """One RDF literal value with its own XSD (or custom) datatype IRI.

    Use as the element type of ``set[TypedLiteral]`` or ``list[TypedLiteral]`` when
    several objects on one predicate may carry **different** ``^^datatype`` IRIs.
    Field-level ``literal_datatype=`` applies one datatype to every object; this type
    preserves each graph literal's datatype independently.
    """

    value: str
    datatype: str | None = None

    def __init__(
        self,
        value: str | int | float | bool,
        datatype: str | None = None,
    ) -> None:
        object.__setattr__(self, "value", str(value))
        object.__setattr__(self, "datatype", datatype)

    @classmethod
    def from_literal(cls, term: Literal) -> TypedLiteral:
        """Build from a pyoxigraph ``Literal`` (language tags are not preserved)."""
        dt = term.datatype
        dt_str = term_str(dt) if dt is not None else None
        if dt_str == _XSD_STRING:
            dt_str = None
        return cls(str(term.value), dt_str)

    def to_literal(self) -> Literal:
        """Serialize to a pyoxigraph ``Literal``."""
        if self.datatype:
            return Literal(self.value, datatype=NamedNode(self.datatype))
        return Literal(self.value)


# Ordered collection alias (SPARQLMojo ``TypedLiteralList`` naming).
TypedLiteralList = list[TypedLiteral]
