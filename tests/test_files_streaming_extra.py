"""Coverage for load_models_streaming edge paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

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

    with pytest.warns(DeprecationWarning, match="sqlalchemy"):
        sql_id, sql_ephemeral = _streaming_store_identifier(
            tmp_path / "x.nt", "sqlalchemy", None
        )
    assert sql_id == sql_ephemeral
    assert Path(sql_id).is_dir()
    with pytest.warns(DeprecationWarning, match="berkeleydb"):
        bdb_id, bdb_ephemeral = _streaming_store_identifier(
            tmp_path / "x.nt", "berkeleydb", None
        )
    assert bdb_id == bdb_ephemeral
    disk_id, disk_ephemeral = _streaming_store_identifier(
        tmp_path / "x.nt", "disk", None
    )
    assert disk_id == disk_ephemeral
    assert Path(disk_id).is_dir()
    custom, ephemeral = _streaming_store_identifier(
        tmp_path / "x.nt", "memory", "custom"
    )
    assert custom == "custom"
    assert ephemeral is None


def test_parse_into_store_graph_default_disk(tmp_path: Path) -> None:
    from triplemodel.io.files import parse_into_store_graph

    path = tmp_path / "one.nt"
    path.write_text(
        f"<{EX}z> <{RDF_TYPE}> <{EX}Org> .\n",
        encoding="utf-8",
    )
    graph = parse_into_store_graph(path)
    ephemeral = graph.ephemeral_store_path
    assert ephemeral is not None
    assert Path(ephemeral).is_dir()
    try:
        assert len(graph) >= 1
    finally:
        graph.close()
    assert not Path(ephemeral).exists()


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


def test_parse_into_store_graph_cleans_ephemeral_on_parse_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from triplemodel.io import files as files_mod
    from triplemodel.io.files import parse_into_store_graph

    path = tmp_path / "bad.nt"
    path.write_text("<<< not valid n-triples\n", encoding="utf-8")
    captured: dict[str, str | None] = {}

    orig = files_mod._streaming_store_identifier

    def capture(
        path_arg: str | Path, store: str, explicit: str | None
    ) -> tuple[str, str | None]:
        ident, ephemeral = orig(path_arg, store, explicit)
        captured["ephemeral"] = ephemeral
        return ident, ephemeral

    monkeypatch.setattr(files_mod, "_streaming_store_identifier", capture)

    with pytest.raises(Exception):
        parse_into_store_graph(path)

    ephemeral = captured.get("ephemeral")
    assert ephemeral is not None
    assert not Path(ephemeral).exists()


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

    store_dir = tmp_path / "orphan-store"
    store_dir.mkdir()

    def boom(*_args, **_kwargs):
        raise OSError("destroy failed")

    monkeypatch.setattr("triplemodel.io.stores.destroy_store", boom)
    with pytest.warns(ResourceWarning, match="Failed to remove ephemeral store"):
        _cleanup_ephemeral_store(str(store_dir), "disk", str(store_dir))


def test_load_models_streaming_use_store_branch(tmp_path: Path, monkeypatch) -> None:
    from pyoxigraph import Literal, NamedNode
    from triplemodel.store import RdfGraph as Graph

    from triplemodel.io import files as files_mod

    path = tmp_path / "one.nt"
    path.write_text(
        f'<{EX}p0> <{RDF_TYPE}> <{EX}Person> .\n<{EX}p0> <{EX}name> "N" .\n',
        encoding="utf-8",
    )
    g = Graph()
    subj = NamedNode(f"{EX}p0")
    g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
    g.add((subj, NamedNode(f"{EX}name"), Literal("N")))
    cleaned: list[tuple[str, str, str | None]] = []

    def fake_parse_into_store_graph(_path, **_kwargs):
        return g

    def fake_identifier(_path, _store, explicit):
        if explicit:
            return explicit, None
        return "/tmp/ephemeral-store", "/tmp/ephemeral-store"

    def fake_destroy(ident, *, store="disk", **_kwargs):
        cleaned.append((ident, store, ident))

    monkeypatch.setattr(
        files_mod, "parse_into_store_graph", fake_parse_into_store_graph
    )
    monkeypatch.setattr(files_mod, "_streaming_store_identifier", fake_identifier)
    monkeypatch.setattr("triplemodel.io.stores.destroy_store", fake_destroy)
    people = load_models_streaming(path, StreamPerson, store="disk")
    assert len(people) == 1
    assert cleaned == [("/tmp/ephemeral-store", "disk", "/tmp/ephemeral-store")]


def test_load_models_streaming_close_failure(tmp_path: Path, monkeypatch) -> None:
    from pyoxigraph import Literal, NamedNode
    from triplemodel.store import RdfGraph as Graph

    from triplemodel.io import files as files_mod

    path = tmp_path / "one.nt"
    path.write_text(
        f'<{EX}p0> <{RDF_TYPE}> <{EX}Person> .\n<{EX}p0> <{EX}name> "N" .\n',
        encoding="utf-8",
    )

    def fake_parse(**_kwargs):
        g = Graph()
        subj = NamedNode(f"{EX}p0")
        g.add((subj, NamedNode(RDF_TYPE), NamedNode(f"{EX}Person")))
        g.add((subj, NamedNode(f"{EX}name"), Literal("N")))

        inner = g.store

        class _StoreWithClose:
            def close(self) -> None:
                raise OSError("close failed")

            def __getattr__(self, name: str) -> object:
                return getattr(inner, name)

        g._store = cast(Any, _StoreWithClose())  # noqa: SLF001
        return g

    monkeypatch.setattr(files_mod, "parse_into_graph", fake_parse)
    people = load_models_streaming(path, StreamPerson)
    assert len(people) == 1
