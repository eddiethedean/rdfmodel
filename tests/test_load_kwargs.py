"""Tests for parse vs import kwargs splitting on file loaders."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from triplemodel import TripleModel, load_models, load_models_streaming, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.io.import_ import split_load_kwargs
from tests._type_uri import module_type_uri

EX = "http://example.org/"
PERSON_TYPE = module_type_uri("KPerson")
ORG_TYPE = module_type_uri("KOrg")


class KPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = PERSON_TYPE
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


class KOrg(TripleModel):
    class Rdf:
        namespace = f"{EX}org/"
        type_uri = ORG_TYPE
        id_field = "slug"

    slug: str


def _write_nt(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                f"<{EX}a> <{RDF_TYPE}> <{PERSON_TYPE}> .",
                f'<{EX}a> <{EX}name> "Alice" .',
                f"<{EX}org/o1> <{RDF_TYPE}> <{ORG_TYPE}> .",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_split_load_kwargs():
    parse_kw, import_kw = split_load_kwargs(
        {"format": "nt", "validate_type": False, "foo": "bar"}
    )
    assert parse_kw == {"format": "nt", "foo": "bar"}
    assert import_kw == {"validate_type": False}


def test_load_models_streaming_validate_type_kwarg(tmp_path: Path) -> None:
    path = tmp_path / "data.nt"
    _write_nt(path)
    people = cast(
        list[KPerson],
        load_models_streaming(path, KPerson, validate_type=False),
    )
    assert len(people) == 1
    assert people[0].name == "Alice"


def test_load_models_multi_class_on_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "data.nt"
    _write_nt(path)
    result = load_models(path, KPerson, KOrg, on_duplicate="ignore")
    assert len(result[KPerson]) == 1
    assert len(result[KOrg]) == 1
