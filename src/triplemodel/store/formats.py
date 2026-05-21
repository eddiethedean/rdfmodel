"""Map format names to pyoxigraph ``RdfFormat`` and reject unsupported legacy formats."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pyoxigraph import QueryResultsFormat, RdfFormat

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


_RDF_FORMAT_TO_NAME: dict[RdfFormat, str] = {
    RdfFormat.TURTLE: "turtle",
    RdfFormat.TRIG: "trig",
    RdfFormat.N_TRIPLES: "nt",
    RdfFormat.N_QUADS: "nquads",
    RdfFormat.RDF_XML: "xml",
    RdfFormat.N3: "n3",
    RdfFormat.JSON_LD: "json-ld",
    RdfFormat.STREAMING_JSON_LD: "json-ld",
}


def rdf_format_to_name(fmt: RdfFormat) -> str:
    """Map a :class:`~pyoxigraph.RdfFormat` to a TripleModel format string."""
    try:
        return _RDF_FORMAT_TO_NAME[fmt]
    except KeyError as exc:
        raise ValueError(f"Unsupported pyoxigraph RdfFormat: {fmt!r}") from exc


def format_from_hint(
    hint: str | Path | None, explicit_format: str | None
) -> str | None:
    """Resolve format via :meth:`RdfFormat.from_extension` / :meth:`RdfFormat.from_media_type`."""
    if explicit_format:
        return explicit_format
    if hint is None:
        return None
    text = str(hint).strip()
    parsed = urlparse(text)
    path_text = parsed.path if parsed.scheme in ("http", "https", "file") else text
    suffix = Path(path_text).suffix.lower()
    if suffix:
        ox = RdfFormat.from_extension(suffix.lstrip("."))
        if ox is not None:
            return rdf_format_to_name(ox)
    media_key = text.lower()
    ox_media = RdfFormat.from_media_type(media_key)
    if ox_media is not None:
        return rdf_format_to_name(ox_media)
    return None


def format_supports_datasets(fmt: str) -> bool:
    """Return True when ``fmt`` can carry named graphs (TriG, N-Quads)."""
    normalized = fmt.lower().replace("_", "-")
    return normalized in ("trig", "nquads", "n-quads", "nq")


def format_supports_rdf_star(fmt: str) -> bool:
    """Return True when pyoxigraph can parse RDF-star in ``fmt`` (Turtle family)."""
    normalized = fmt.lower().replace("_", "-")
    return normalized in (
        "turtle",
        "ttl",
        "trig",
        "nt",
        "ntriples",
        "n-triples",
        "nquads",
        "n-quads",
        "nq",
    )


_QUERY_RESULTS_MAP: dict[str, QueryResultsFormat] = {
    "sparql-results+json": QueryResultsFormat.JSON,
    "json": QueryResultsFormat.JSON,
    "sparql-results+xml": QueryResultsFormat.XML,
    "xml": QueryResultsFormat.XML,
    "text/csv": QueryResultsFormat.CSV,
    "csv": QueryResultsFormat.CSV,
    "text/tab-separated-values": QueryResultsFormat.TSV,
    "tsv": QueryResultsFormat.TSV,
}


def to_query_results_format(fmt: str) -> QueryResultsFormat:
    """Resolve a SPARQL results format name to :class:`~pyoxigraph.QueryResultsFormat`."""
    normalized = fmt.lower().replace("_", "-")
    try:
        return _QUERY_RESULTS_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown SPARQL results format: {fmt!r}") from exc


def query_results_format_from_hint(
    hint: str | Path | None,
    explicit_format: str | None,
) -> str:
    """Infer SPARQL results format from a path suffix or explicit name."""
    if explicit_format:
        return explicit_format
    if hint is None:
        raise ValueError(
            "Cannot infer SPARQL results format: pass format= or a path with a known suffix."
        )
    suffix = Path(str(hint)).suffix.lower()
    if suffix == ".srx":
        return "sparql-results+xml"
    if suffix == ".srj":
        return "sparql-results+json"
    if suffix == ".csv":
        return "text/csv"
    if suffix == ".tsv":
        return "text/tab-separated-values"
    if suffix == ".json":
        return "sparql-results+json"
    raise ValueError(
        f"Cannot infer SPARQL results format from {hint!r}; pass format= explicitly."
    )
