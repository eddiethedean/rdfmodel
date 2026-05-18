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

    sql_id, sql_ephemeral = _streaming_store_identifier(
        tmp_path / "x.nt", "sqlalchemy", None
    )
    assert sql_id.startswith("sqlite:///")
    assert sql_ephemeral is not None
    bdb_id, bdb_ephemeral = _streaming_store_identifier(
        tmp_path / "x.nt", "berkeleydb", None
    )
    assert bdb_id.endswith(".db")
    assert bdb_ephemeral is not None
    custom, ephemeral = _streaming_store_identifier(
        tmp_path / "x.nt", "memory", "custom"
    )
    assert custom == "custom"
    assert ephemeral is None


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
    ident, ephemeral = _streaming_store_identifier(p, "memory", None)
    assert ident == str(p)
    assert ephemeral is None


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


def test_cleanup_ephemeral_store_noop() -> None:
    from triplemodel.io.files import _cleanup_ephemeral_store

    _cleanup_ephemeral_store("sqlite:///unused", "sqlalchemy", None)


def test_cleanup_ephemeral_store_destroy_failure(tmp_path: Path, monkeypatch) -> None:
    from triplemodel.io.files import _cleanup_ephemeral_store

    db = tmp_path / "orphan.sqlite"
    db.write_text("", encoding="utf-8")

    def boom(*_args, **_kwargs):
        raise OSError("destroy failed")

    monkeypatch.setattr("triplemodel.io.stores.destroy_store", boom)
    _cleanup_ephemeral_store(f"sqlite:///{db}", "sqlalchemy", str(db))
    assert not db.exists()


def test_load_models_streaming_close_failure(tmp_path: Path, monkeypatch) -> None:
    from rdflib import Graph, Literal, URIRef

    from triplemodel.io import files as files_mod

    path = tmp_path / "one.nt"
    path.write_text(
        f'<{EX}p0> <{RDF_TYPE}> <{EX}Person> .\n<{EX}p0> <{EX}name> "N" .\n',
        encoding="utf-8",
    )

    def fake_parse(**_kwargs):
        g = Graph()
        subj = URIRef(f"{EX}p0")
        g.add((subj, URIRef(RDF_TYPE), URIRef(f"{EX}Person")))
        g.add((subj, URIRef(f"{EX}name"), Literal("N")))

        def failing_close():
            raise OSError("close failed")

        g.store.close = failing_close  # ty: ignore[invalid-assignment]
        return g

    monkeypatch.setattr(files_mod, "parse_into_graph", fake_parse)
    people = load_models_streaming(path, StreamPerson)
    assert len(people) == 1
