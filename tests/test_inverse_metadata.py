"""Coverage for inverse predicate metadata helpers."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from triplemodel.fields.metadata import (
    InverseOf,
    inverse_for_field,
    inverse_from_annotation,
    rdf_field,
)


def test_inverse_for_field_json_extra() -> None:
    info = Field(json_schema_extra={"rdf_predicate": "ex:p", "rdf_inverse": "ex:inv"})
    assert inverse_for_field(info) == "ex:inv"


def test_inverse_for_field_metadata() -> None:
    from triplemodel import TripleModel

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"

        slug: str = "x"
        ref: Annotated[str | None, InverseOf("ex:inv")] = rdf_field("ex:p", default=None)

    assert inverse_for_field(M.model_fields["ref"]) == "ex:inv"


def test_inverse_from_annotation() -> None:
    ann = Annotated[str, InverseOf("ex:inv")]
    assert inverse_from_annotation(ann) == "ex:inv"
    assert inverse_from_annotation(str) is None
    assert inverse_from_annotation(Annotated[str, "meta"]) is None


def test_inverse_for_field_from_annotation_only() -> None:
    from triplemodel.metadata.cardinality import field_annotation

    class Holder:
        ref: Annotated[str | None, InverseOf("ex:inv")]

    import typing

    field = typing.get_type_hints(Holder, include_extras=True)["ref"]
    info = Field()
    # Simulate a field whose annotation carries InverseOf only.
    info.annotation = field
    assert inverse_for_field(info) == "ex:inv"
    assert field_annotation(info) is field


def test_rdf_field_inverse_kwarg() -> None:
    from triplemodel import TripleModel

    class M(TripleModel):
        class Rdf:
            namespace = "http://ex/"
            type_uri = "http://ex/T"
            id_field = "slug"

        slug: str = "x"
        ref: str | None = rdf_field("ex:p", inverse="ex:inv", default=None)

    info = M.model_fields["ref"]
    assert inverse_for_field(info) == "ex:inv"
