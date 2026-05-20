"""Shared pyoxigraph parse helpers for graph and dataset."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pyoxigraph import RdfFormat
from pyoxigraph import parse as ox_parse


def ox_parse_from_source(
    source: str | Path,
    *,
    format: RdfFormat,
    base_iri: str | None = None,
) -> list:
    """Parse RDF from a filesystem path, URL, or inline string source."""
    path = Path(source)
    if path.exists():
        return list(ox_parse(path.read_bytes(), format=format, base_iri=base_iri))
    parsed = urlparse(str(source))
    if parsed.scheme in ("http", "https", "file"):
        return list(ox_parse(str(source), format=format, base_iri=base_iri))
    return list(ox_parse(str(source).encode("utf-8"), format=format, base_iri=base_iri))
