"""Parse and serialize SPARQL result documents."""

from __future__ import annotations

import io
from pathlib import Path

from pyoxigraph import (
    QueryBoolean,
    parse_query_results as ox_parse_query_results,
)

from triplemodel.store.formats import (
    query_results_format_from_hint,
    to_query_results_format,
)
from triplemodel.store.sparql_result import SparqlResult


def parse_query_results(
    source: str | Path | io.BytesIO | bytes | None = None,
    *,
    data: str | bytes | None = None,
    format: str | None = None,
    path: str | Path | None = None,
) -> SparqlResult:
    """Parse a SPARQL results file into :class:`~triplemodel.store.sparql_result.SparqlResult`."""
    if data is not None and source is not None:
        raise ValueError("Pass source= or data=, not both.")
    if data is None and source is None and path is None:
        raise ValueError("parse_query_results requires source=, data=, or path=.")
    hint: str | Path | None = path
    if hint is None and data is None and isinstance(source, (str, Path)):
        hint = source
    fmt_name = query_results_format_from_hint(hint, format)
    ox_format = to_query_results_format(fmt_name)
    if data is not None:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        raw = ox_parse_query_results(payload, format=ox_format)
    elif path is not None:
        raw = ox_parse_query_results(format=ox_format, path=str(path))
    elif source is not None:
        if isinstance(source, io.BytesIO):
            raw = ox_parse_query_results(source.read(), format=ox_format)
        else:
            raw = ox_parse_query_results(format=ox_format, path=str(source))
    form = "ask" if isinstance(raw, QueryBoolean) else "select"
    return SparqlResult.from_pyoxigraph(raw, form=form)


__all__ = ["parse_query_results"]
