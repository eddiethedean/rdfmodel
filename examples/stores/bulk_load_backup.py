#!/usr/bin/env python3
"""Bulk load, optimize, backup, and dump an on-disk pyoxigraph store."""

from __future__ import annotations

import tempfile
from pathlib import Path

from triplemodel.io.stores import (
    backup_store,
    bulk_load_into_graph,
    dump_store,
    open_graph,
    optimize_store,
    store_commit,
)

EX = "http://example.org/"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ttl = root / "seed.ttl"
        ttl.write_text(f"@prefix ex: <{EX}> .\nex:item ex:label \"ok\" .\n", encoding="utf-8")
        store_dir = root / "ox-store"
        graph = open_graph("disk", str(store_dir))
        try:
            bulk_load_into_graph(graph, ttl)
            optimize_store(graph=graph)
            backup_store(root / "backup", graph=graph)
            dump_store(root / "dump.nq", graph=graph)
            store_commit(graph)
            print("bulk_load_backup OK")
        finally:
            graph.close()


if __name__ == "__main__":
    main()
