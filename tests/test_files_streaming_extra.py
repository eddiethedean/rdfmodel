"""Coverage for load_models_streaming edge paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from triplemodel import TripleModel, load_models_streaming, rdf_field
from triplemodel.config import RDF_TYPE

EX = "http://example.org/"


class StreamOrg(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Org"
        id_field = "slug"

    slug: str
    label: str = rdf_field(f"{EX}label")


class StreamPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def test_load_models_streaming_multi_class(tmp_path: Path) -> None:
    path = tmp_path / "data.nt"
    path.write_text(
        f"<{EX}a> <{RDF_TYPE}> <{EX}Org> .\n"
        f'<{EX}a> <{EX}label> "A" .\n'
        f"<{EX}b> <{RDF_TYPE}> <{EX}Person> .\n"
        f'<{EX}b> <{EX}name> "B" .\n',
        encoding="utf-8",
    )
    result = load_models_streaming(path, StreamOrg, StreamPerson, chunk_size=10)
    assert isinstance(result, dict)
    assert len(result[StreamOrg]) == 1
    assert len(result[StreamPerson]) == 1


def test_streaming_store_identifier_helpers(tmp_path: Path) -> None:
    from triplemodel.io.files import _streaming_store_identifier

    sql_id = _streaming_store_identifier(tmp_path / "x.nt", "sqlalchemy", None)
    assert sql_id.startswith("sqlite:///")
    bdb_id = _streaming_store_identifier(tmp_path / "x.nt", "berkeleydb", None)
    assert bdb_id.endswith(".db")
    assert (
        _streaming_store_identifier(tmp_path / "x.nt", "memory", "custom") == "custom"
    )


def test_parse_into_store_graph_bind_prefixes(tmp_path: Path) -> None:
    from triplemodel.io.files import parse_into_store_graph

    path = tmp_path / "one.nt"
    path.write_text(
        f"<{EX}z> <{RDF_TYPE}> <{EX}Org> .\n",
        encoding="utf-8",
    )
    graph = parse_into_store_graph(
        path,
        store="memory",
        identifier="",
        bind_prefixes={"ex": EX},
    )
    assert len(graph) >= 1


def test_streaming_store_identifier_plain_path(tmp_path: Path) -> None:
    from triplemodel.io.files import _streaming_store_identifier

    p = tmp_path / "data.nt"
    assert _streaming_store_identifier(p, "memory", None) == str(p)


def test_load_models_streaming_invalid_model_class(tmp_path: Path) -> None:
    path = tmp_path / "one.nt"
    path.write_text(f"<{EX}z> <{RDF_TYPE}> <{EX}Org> .\n", encoding="utf-8")

    class NotModel:
        pass

    with pytest.raises(TypeError, match="TripleModel"):
        load_models_streaming(path, NotModel)  # ty: ignore[invalid-argument-type]


def test_load_models_streaming_requires_class() -> None:
    with pytest.raises(TypeError, match="at least one"):
        load_models_streaming("x.nt")  # type: ignore[call-arg]
