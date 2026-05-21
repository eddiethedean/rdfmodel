"""Store operations (0.11 pyoxigraph surface)."""

from __future__ import annotations

from pathlib import Path

from pyoxigraph import NamedNode, Quad

from triplemodel.io.stores import open_graph, store_commit
from triplemodel.io.stores import (
    backup_store,
    bulk_load_into_graph,
    clear_named_graph,
    dump_store,
    ensure_named_graph,
    iter_quads_for_pattern,
    list_named_graphs,
    load_store,
    optimize_store,
    remove_named_graph,
    store_flush,
)

EX = "http://example.org/"
NG = f"{EX}graph/g1"


def test_bulk_load_dump_backup_roundtrip(tmp_path: Path) -> None:
    ttl = tmp_path / "data.ttl"
    ttl.write_text(
        f'@prefix ex: <{EX}> .\nex:s ex:p "v" .\n',
        encoding="utf-8",
    )
    store_dir = tmp_path / "store"
    graph = open_graph("disk", str(store_dir))
    try:
        bulk_load_into_graph(graph, ttl)
        optimize_store(graph=graph)
        dump_path = tmp_path / "dump.nq"
        dump_store(dump_path, graph=graph)
        backup_dir = tmp_path / "backup"
        backup_store(backup_dir, graph=graph)
        store_commit(graph)
        assert list(iter_quads_for_pattern(graph, NamedNode(f"{EX}s"), None, None))
    finally:
        graph.close()

    graph2 = open_graph("disk", str(store_dir))
    try:
        assert (
            len(list(iter_quads_for_pattern(graph2, NamedNode(f"{EX}s"), None, None)))
            >= 1
        )
        store_flush(graph2)
    finally:
        graph2.close()

    restored = open_graph("disk", str(tmp_path / "store2"))
    try:
        load_store(restored, dump_path)
        assert (
            len(list(iter_quads_for_pattern(restored, NamedNode(f"{EX}s"), None, None)))
            >= 1
        )
    finally:
        restored.close()


def test_named_graph_lifecycle(tmp_path: Path) -> None:
    graph = open_graph("disk", str(tmp_path / "ng-store"))
    try:
        ensure_named_graph(graph, NG)
        assert NG in list_named_graphs(graph)
        graph.store.add(
            Quad(
                NamedNode(f"{EX}a"),
                NamedNode(f"{EX}p"),
                NamedNode(f"{EX}o"),
                NamedNode(NG),
            )
        )
        clear_named_graph(graph, NG)
        remove_named_graph(graph, NG)
        assert NG not in list_named_graphs(graph)
    finally:
        graph.close()


def test_bulk_load_requires_source_or_data() -> None:
    from triplemodel.store import RdfGraph as Graph

    graph = Graph()
    try:
        bulk_load_into_graph(graph)
    except ValueError as exc:
        assert "source=" in str(exc)
    finally:
        graph.close()
