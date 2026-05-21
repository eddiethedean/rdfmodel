"""Map format names to pyoxigraph ``RdfFormat`` and reject unsupported legacy formats."""

from __future__ import annotations

from pyoxigraph import RdfFormat

_FORMAT_MAP: dict[str, RdfFormat] = {
    "turtle": RdfFormat.TURTLE,
    "ttl": RdfFormat.TURTLE,
    "trig": RdfFormat.TRIG,
    "nt": RdfFormat.N_TRIPLES,
    "ntriples": RdfFormat.N_TRIPLES,
    "n-triples": RdfFormat.N_TRIPLES,
    "nquads": RdfFormat.N_QUADS,
    "n-quads": RdfFormat.N_QUADS,
    "nq": RdfFormat.N_QUADS,
    "xml": RdfFormat.RDF_XML,
    "rdf": RdfFormat.RDF_XML,
    "rdf+xml": RdfFormat.RDF_XML,
    "n3": RdfFormat.N3,
    "json-ld": RdfFormat.JSON_LD,
    "jsonld": RdfFormat.JSON_LD,
}

_UNSUPPORTED = frozenset(
    {
        "hext",
        "hextuples",
        "longturtle",
        "lt",
        "trix",
    }
)


def raise_if_unsupported_format(fmt: str) -> None:
    """Raise when ``fmt`` names a format removed in the pyoxigraph engine (0.10+)."""
    normalized = fmt.lower().replace("_", "-")
    if normalized in _UNSUPPORTED:
        msg = (
            f"RDF format {fmt!r} is not supported by pyoxigraph in TripleModel 0.10. "
            "Use Turtle, TriG, N-Triples, N-Quads, RDF/XML, N3, or JSON-LD."
        )
        raise ValueError(msg)


def to_rdf_format(fmt: str) -> RdfFormat:
    """Resolve a format name to :class:`~pyoxigraph.RdfFormat`."""
    raise_if_unsupported_format(fmt)
    normalized = fmt.lower().replace("_", "-")
    try:
        return _FORMAT_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown RDF format: {fmt!r}") from exc
