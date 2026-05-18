#!/usr/bin/env python3
"""0.8.0 exit criteria: chunked import benchmark (FOAF-shaped graph)."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

from rdflib import Graph, Literal, URIRef

from triplemodel import TripleModel, iter_graph_to_models, load_models_streaming, rdf_field
from triplemodel.config import RDF_TYPE
from triplemodel.vocab import FOAF

EX = "http://example.org/people/"
FOAF_PERSON = f"{FOAF}Person"
FOAF_NAME = f"{FOAF}name"
COUNT = int(os.environ.get("TRIPLEMODEL_BENCH_COUNT", "100000"))


class Person(TripleModel):
    class Rdf:
        namespace = EX
        type_uri = FOAF_PERSON
        id_field = "slug"
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


def _write_nt(path: Path, count: int) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for i in range(count):
            subj = f"<{EX}p{i}>"
            fh.write(f"{subj} <{RDF_TYPE}> <{FOAF_PERSON}> .\n")
            fh.write(f'{subj} <{FOAF_NAME}> "Person {i}" .\n')


def _strict_import_smoke() -> None:
    g = Graph()
    subj = URIRef(f"{EX}strict0")
    g.add((subj, URIRef(RDF_TYPE), URIRef(FOAF_PERSON)))
    g.add((subj, URIRef(FOAF_NAME), Literal("OK")))
    people = list(
        iter_graph_to_models(g, Person, chunk_size=10, strict_import=True)
    )
    assert len(people) == 1 and people[0][0].name == "OK"
    print("strict_import smoke OK")


def _store_smoke(nt_path: Path) -> None:
    try:
        from rdflib import Graph as RdfGraph

        RdfGraph(store="SQLAlchemy", identifier="sqlite:///:memory:").close()
    except Exception:
        print("store smoke skipped (install triplemodel[sqlalchemy])")
        return
    people = load_models_streaming(
        nt_path,
        Person,
        store="sqlalchemy",
        chunk_size=min(500, max(COUNT, 1)),
    )
    assert len(people) == COUNT
    print(f"sqlalchemy store smoke OK ({len(people)} people)")


def main() -> None:
    _strict_import_smoke()
    with tempfile.TemporaryDirectory() as tmp:
        nt_path = Path(tmp) / "people.nt"
        _write_nt(nt_path, COUNT)
        t0 = time.perf_counter()
        chunks = 0
        total = 0
        g = Graph()
        g.parse(source=str(nt_path), format="nt")
        for chunk in iter_graph_to_models(g, Person, chunk_size=500):
            chunks += 1
            total += len(chunk)
        elapsed = time.perf_counter() - t0
        assert total == COUNT, f"expected {COUNT} people, got {total}"
        print(f"chunked import: {total} people in {chunks} chunks, {elapsed:.2f}s")

        t1 = time.perf_counter()
        streamed = load_models_streaming(nt_path, Person, chunk_size=500)
        elapsed_stream = time.perf_counter() - t1
        assert len(streamed) == COUNT
        print(
            f"streaming load: {len(streamed)} people, {elapsed_stream:.2f}s "
            f"(TRIPLEMODEL_BENCH_COUNT={COUNT})"
        )
        if os.environ.get("TRIPLEMODEL_STORE", "").lower() == "sqlalchemy":
            _store_smoke(nt_path)
    print("0.8.0 chunked/streaming import OK")


if __name__ == "__main__":
    main()
    sys.exit(0)
