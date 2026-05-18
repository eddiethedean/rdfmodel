"""Validate RDF field mappings at model class definition time."""

from __future__ import annotations

import warnings
from urllib.parse import urlparse

from pydantic import BaseModel

from triplemodel.config import get_rdf_config
from triplemodel.fields.metadata import (
    inverse_for_field,
    predicate_for_field,
    predicate_from_annotation,
)
from triplemodel.metadata.cardinality import field_annotation
from triplemodel.namespaces import resolve_predicate
from triplemodel.terms.iri import looks_like_iri


def predicate_has_local_name(iri: str) -> bool:
    """True when ``iri`` has a non-empty local name after ``#`` or a path segment."""
    if not looks_like_iri(iri):
        if ":" in iri:
            _prefix, local = iri.split(":", 1)
            return bool(local)
        return False
    if "#" in iri:
        local = iri.rsplit("#", 1)[1]
        return bool(local)
    parsed = urlparse(iri)
    path = (parsed.path or "").rstrip("/")
    if not path or path == "/":
        return False
    segment = path.rsplit("/", 1)[-1]
    return bool(segment)


def validate_predicate_iri(
    model_cls: type[BaseModel],
    field_name: str,
    raw_predicate: str,
    resolved: str,
) -> None:
    """Raise when ``resolved`` is not a usable property IRI."""
    if not predicate_has_local_name(resolved):
        raise ValueError(
            f"{model_cls.__name__}.{field_name}: rdf_predicate {raw_predicate!r} "
            f"resolves to {resolved!r}, which has no local name after '#' or '/'. "
            "Use a full property IRI or CURIE (e.g. rdfs:label, not rdfs# alone)."
        )


def warn_predicate_equals_prefix_namespace(
    model_cls: type[BaseModel],
    field_name: str,
    resolved: str,
    prefixes: dict[str, str],
) -> None:
    """Warn when a predicate IRI equals a declared prefix namespace URI."""
    for prefix, ns_uri in prefixes.items():
        if resolved == ns_uri or resolved.rstrip("#/") == ns_uri.rstrip("#/"):
            warnings.warn(
                f"{model_cls.__name__}.{field_name}: predicate {resolved!r} equals "
                f"prefix {prefix!r} namespace {ns_uri!r}; "
                "did you mean a property under that namespace?",
                UserWarning,
                stacklevel=4,
            )
            return


def validate_model_predicates(model_cls: type[BaseModel]) -> None:
    """Validate all mapped predicates on ``model_cls`` at class definition."""
    cfg = get_rdf_config(model_cls)
    prefixes = cfg.prefixes_dict
    for name, field_info in model_cls.model_fields.items():
        raw = predicate_for_field(field_info) or predicate_from_annotation(
            field_annotation(field_info)
        )
        if raw is None:
            continue
        try:
            resolved = resolve_predicate(raw, prefixes)
        except ValueError:
            continue
        validate_predicate_iri(model_cls, name, raw, resolved)
        warn_predicate_equals_prefix_namespace(model_cls, name, resolved, prefixes)
        inv_raw = inverse_for_field(field_info)
        if inv_raw is not None:
            try:
                inv_resolved = resolve_predicate(inv_raw, prefixes)
            except ValueError:
                continue
            validate_predicate_iri(model_cls, name, inv_raw, inv_resolved)
            warn_predicate_equals_prefix_namespace(
                model_cls, name, inv_resolved, prefixes
            )
