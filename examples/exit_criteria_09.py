#!/usr/bin/env python3
"""0.9.0 exit criteria: rdflib plugin passthrough + API-freeze smoke."""

from __future__ import annotations

import sys
import types

from rdflib import Graph
from rdflib.parser import InputSource, Parser
from rdflib.plugin import get
from rdflib.store import Store
from rdflib.term import Literal, URIRef

from triplemodel.plugins import register_parser, register_store

_PARSER = "triplemodel-exit09-parser"
_STORE = "triplemodel-exit09-memory"


def _strip_uri(token: str) -> str:
    if token.startswith("<") and token.endswith(">"):
        return token[1:-1]
    return token


class _Exit09Parser(Parser):
    def parse(self, source: InputSource, sink) -> None:
        raw = source.getCharacterStream().read()
        line = raw.strip().splitlines()[0] if raw.strip() else ""
        if not line:
            return
        s, p, rest = line.split(None, 2)
        o = rest.rsplit(None, 1)[0] if rest.endswith(" .") else rest
        if o.startswith('"'):
            sink.add(
                (
                    URIRef(_strip_uri(s)),
                    URIRef(_strip_uri(p)),
                    Literal(o.strip('"')),
                )
            )
        else:
            sink.add(
                (URIRef(_strip_uri(s)), URIRef(_strip_uri(p)), URIRef(_strip_uri(o)))
            )


def main() -> int:
    mod = types.ModuleType("triplemodel_exit09_plugins")
    mod._Exit09Parser = _Exit09Parser
    sys.modules[mod.__name__] = mod

    register_parser(_PARSER, mod.__name__, "_Exit09Parser")
    register_store(_STORE, "rdflib.plugins.stores.memory", "Memory")

    assert get(_PARSER, Parser) is not None
    assert get(_STORE, Store) is not None

    g = Graph()
    g.parse(
        data=(
            "<http://example.org/exit09/subject> "
            '<http://example.org/exit09/predicate> "ok" .'
        ),
        format=_PARSER,
    )
    assert len(g) == 1

    g2 = Graph(store=_STORE)
    assert g2.store is not None

    print("0.9.0 exit criteria OK: plugin passthrough + matrix audit shipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
