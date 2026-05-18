"""Tests for load_models_streaming."""

from __future__ import annotations

from pathlib import Path

import pytest

from triplemodel import TripleModel, load_models_streaming, rdf_field
from triplemodel.config import RDF_TYPE

EX = "http://example.org/"


class StreamPerson(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = f"{EX}Person"
        id_field = "slug"

    slug: str
    name: str = rdf_field(f"{EX}name")


def _write_nt(path: Path, count: int) -> None:
    lines = []
    for i in range(count):
        subj = f"<{EX}p{i}>"
        lines.append(f"{subj} <{RDF_TYPE}> <{EX}Person> .")
        lines.append(f'{subj} <{EX}name> "P{i}" .')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_load_models_streaming_memory_nt(tmp_path: Path) -> None:
    path = tmp_path / "people.nt"
    _write_nt(path, 3)
    people = load_models_streaming(path, StreamPerson, chunk_size=2)
    assert len(people) == 3


def _sqlalchemy_store_available() -> bool:
    try:
        from rdflib import Graph

        Graph(store="SQLAlchemy", identifier="sqlite:///:memory:").close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _sqlalchemy_store_available(),
    reason="rdflib-sqlalchemy store plugin not installed",
)
def test_load_models_streaming_sqlalchemy_store(tmp_path: Path) -> None:
    path = tmp_path / "people.nt"
    _write_nt(path, 2)
    db = tmp_path / "store.sqlite"
    people = load_models_streaming(
        path,
        StreamPerson,
        store="sqlalchemy",
        store_identifier=f"sqlite:///{db}",
        chunk_size=1,
    )
    assert len(people) == 2
