"""Warnings for parse/serialize kwargs not supported by pyoxigraph."""

from __future__ import annotations

import warnings
from typing import Any

_PARSE_SUPPORTED = frozenset(
    {
        "lenient",
        "without_named_graphs",
        "rename_blank_nodes",
        "base_iri",
        "base",
    }
)

_SERIALIZE_SUPPORTED = frozenset({"base_iri", "base"})


def _normalize_kwarg_key(key: str) -> str:
    return key.lower().replace("_", "")


def warn_ignored_parse_kwargs(
    kwargs: dict[str, Any], *, stacklevel: int = 3
) -> dict[str, Any]:
    """Return pyoxigraph-supported kwargs; warn on the rest (e.g. JSON-LD context)."""
    if not kwargs:
        return {}
    supported: dict[str, Any] = {}
    ignored: list[str] = []
    for key, value in kwargs.items():
        norm = _normalize_kwarg_key(key)
        if norm in {_normalize_kwarg_key(k) for k in _PARSE_SUPPORTED}:
            if norm == "withoutnamedgraphs":
                supported["without_named_graphs"] = value
            elif norm == "renameblanknodes":
                supported["rename_blank_nodes"] = value
            elif norm in ("baseiri", "base"):
                supported["base_iri"] = value
            else:
                supported[key] = value
        elif norm == "publicid":
            continue
        else:
            ignored.append(key)
    if ignored:
        warnings.warn(
            "parse() ignored unsupported keyword arguments for the pyoxigraph "
            f"backend: {sorted(ignored)}. "
            "Rdf.jsonld_context and context= are not supported in TripleModel 0.10.",
            UserWarning,
            stacklevel=stacklevel,
        )
    return supported


def warn_ignored_serialize_kwargs(
    kwargs: dict[str, Any], *, stacklevel: int = 3
) -> dict[str, Any]:
    """Return pyoxigraph-supported serialize kwargs; warn on the rest."""
    if not kwargs:
        return {}
    supported: dict[str, Any] = {}
    ignored: list[str] = []
    for key, value in kwargs.items():
        norm = _normalize_kwarg_key(key)
        if norm in {_normalize_kwarg_key(k) for k in _SERIALIZE_SUPPORTED}:
            supported["base_iri"] = value
        else:
            ignored.append(key)
    if ignored:
        warnings.warn(
            "serialize() ignored unsupported keyword arguments for the pyoxigraph "
            f"backend: {sorted(ignored)}. "
            "Rdf.jsonld_context and context= are not supported in TripleModel 0.10.",
            UserWarning,
            stacklevel=stacklevel,
        )
    return supported


def warn_jsonld_context_config(*, stacklevel: int = 3) -> None:
    """Warn that Rdf.jsonld_context has no effect on the pyoxigraph backend."""
    warnings.warn(
        "Rdf.jsonld_context is not supported by the pyoxigraph backend in TripleModel "
        "0.10; JSON-LD parse/serialize uses document-embedded context only.",
        UserWarning,
        stacklevel=stacklevel,
    )
