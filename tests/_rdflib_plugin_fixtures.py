"""Minimal rdflib plugin classes for register_* passthrough tests."""

from __future__ import annotations

from rdflib.parser import InputSource, Parser
from rdflib.serializer import Serializer
from pyoxigraph import Literal, NamedNode


class MinimalTestParser(Parser):
    """Parses a single hard-coded N-Triples line from string sources."""

    def parse(self, source: InputSource, sink) -> None:
        stream = source.getCharacterStream()
        raw = stream.read() if stream is not None else ""
        line = raw.strip().splitlines()[0] if raw.strip() else ""
        if not line or line.startswith("#"):
            return
        parts = line.split(None, 2)
        if len(parts) < 3:
            return
        s, p, rest = parts
        o = rest.rsplit(None, 1)[0] if rest.endswith(" .") else rest
        if o.startswith('"'):
            sink.add((NamedNode(s), NamedNode(p), Literal(o.strip('"'))))
        else:
            sink.add((NamedNode(s), NamedNode(p), NamedNode(o)))


class MinimalTestSerializer(Serializer):
    """Writes one triple as N-Triples."""

    def serialize(self, stream, base=None, encoding=None, **kwargs) -> None:
        graph = kwargs.get("graph")
        if graph is None:
            return
        for s, p, o in graph:
            if isinstance(o, Literal):
                stream.write(f'{s} {p} "{o}" .\n'.encode(encoding or "utf-8"))
            else:
                stream.write(f"{s} {p} {o} .\n".encode(encoding or "utf-8"))
            break
