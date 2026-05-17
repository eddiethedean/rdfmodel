"""RDF configuration attached to Pydantic models."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping
from urllib.parse import quote, unquote

EmbedMode = Literal["iri", "bnode"]
GraphMode = Literal["add", "replace", "patch"]


def subject_base(namespace: str) -> str:
    """Return the prefix used when appending an id to ``namespace``."""
    return namespace if namespace.endswith(("/", "#")) else namespace + "/"


def id_from_subject_uri(namespace: str, uri: str) -> str | None:
    """Extract the id segment from ``uri`` when it was built from ``namespace``."""
    base = subject_base(namespace)
    if not uri.startswith(base):
        return None
    return unquote(uri[len(base) :])


def _freeze_prefixes(raw: object) -> Mapping[str, str]:
    if not raw:
        return MappingProxyType({})
    if isinstance(raw, Mapping):
        return MappingProxyType({str(k): str(v) for k, v in raw.items()})
    return MappingProxyType({})


@dataclass(frozen=True)
class RdfConfig:
    """RDF metadata for an :class:`~triplemodel.TripleModel` subclass."""

    namespace: str = ""
    type_uri: str | None = None
    id_field: str | None = None
    """Model field whose value is appended to ``namespace`` for the subject IRI."""
    prefixes: Mapping[str, str] = MappingProxyType({})
    embed: EmbedMode = "iri"
    graph_mode: GraphMode = "add"

    @property
    def prefixes_dict(self) -> dict[str, str]:
        return dict(self.prefixes)

    def subject_uri(self, instance: Any) -> str:
        if not self.namespace:
            raise ValueError(
                "Rdf.namespace is required to derive a subject IRI; "
                "set it on the model's Rdf class or pass uri= explicitly."
            )
        if not self.id_field:
            raise ValueError(
                "Rdf.id_field is required to derive a subject IRI; "
                "set it on the model's Rdf class or pass uri= explicitly."
            )
        raw = getattr(instance, self.id_field, None)
        if raw is None or raw == "":
            raise ValueError(
                f"Cannot build subject IRI: field {self.id_field!r} is empty."
            )
        if isinstance(raw, str) and (
            raw.startswith("http://")
            or raw.startswith("https://")
            or raw.startswith("urn:")
        ):
            return raw
        base = subject_base(self.namespace)
        segment = quote(str(raw), safe="")
        return f"{base}{segment}"


def effective_graph_mode(
    mode: GraphMode | None,
    cfg: RdfConfig,
    *,
    sync: bool = False,
) -> GraphMode:
    """Resolve ``mode``; default sync to ``replace`` when ``graph_mode`` is unset (``add``)."""
    if mode is not None:
        return mode
    if sync and cfg.graph_mode == "add":
        return "replace"
    return cfg.graph_mode


def get_rdf_config(model_cls: type) -> RdfConfig:
    for cls in model_cls.__mro__:
        if cls is object:
            continue
        rdf = getattr(cls, "Rdf", None)
        if rdf is not None:
            embed = getattr(rdf, "embed", "iri") or "iri"
            mode = getattr(rdf, "graph_mode", "add") or "add"
            if embed not in ("iri", "bnode"):
                warnings.warn(
                    f"{cls.__name__}.Rdf.embed={embed!r} is invalid; using 'iri'.",
                    UserWarning,
                    stacklevel=2,
                )
                embed = "iri"
            if mode not in ("add", "replace", "patch"):
                warnings.warn(
                    f"{cls.__name__}.Rdf.graph_mode={mode!r} is invalid; using 'add'.",
                    UserWarning,
                    stacklevel=2,
                )
                mode = "add"
            return RdfConfig(
                namespace=getattr(rdf, "namespace", "") or "",
                type_uri=getattr(rdf, "type_uri", None),
                id_field=getattr(rdf, "id_field", None),
                prefixes=_freeze_prefixes(getattr(rdf, "prefixes", None)),
                embed=embed,
                graph_mode=mode,
            )
    return RdfConfig()


# Namespace constants used by the package
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"

RDF_TYPE = f"{RDF}type"
