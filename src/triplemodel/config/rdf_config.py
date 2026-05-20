"""RDF configuration attached to Pydantic models."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol
from urllib.parse import quote, unquote

from pydantic import BaseModel
from triplemodel.store import RdfDataset as Dataset, RdfGraph as Graph

EmbedMode = Literal["iri", "bnode"]
GraphMode = Literal["add", "replace", "patch"]
BlankNodePolicy = Literal["fresh", "stable"]


class SubjectUriInstance(Protocol):
    """Instance providing attribute values for :meth:`RdfConfig.subject_uri`."""


def subject_base(namespace: str) -> str:
    """Return the prefix used when appending an id to ``namespace``."""
    return namespace if namespace.endswith(("/", "#")) else namespace + "/"


def id_from_subject_uri(namespace: str, uri: str) -> str | None:
    """Extract the id segment from ``uri`` when it was built from ``namespace``."""
    base = subject_base(namespace)
    if not uri.startswith(base):
        return None
    return unquote(uri[len(base) :])


def _empty_prefixes() -> Mapping[str, str]:
    return MappingProxyType({})


def freeze_prefixes(
    raw: Mapping[str, str] | list[tuple[str, str]] | None,
) -> Mapping[str, str]:
    if not raw:
        return MappingProxyType({})
    if isinstance(raw, list):
        return MappingProxyType({str(k): str(v) for k, v in raw})
    if not isinstance(raw, Mapping):
        return MappingProxyType({})
    return MappingProxyType({str(k): str(v) for k, v in raw.items()})


@dataclass(frozen=True)
class RdfConfig:
    """RDF metadata for an :class:`~triplemodel.TripleModel` subclass."""

    namespace: str = ""
    type_uri: str | None = None
    instance_of: str | tuple[str, ...] | None = None
    """Property URI(s) for classification (e.g. ``wdt:P31``) when not using ``rdf:type``."""
    instance_type_uri: str | tuple[str, ...] | None = None
    """Object URI(s) to filter ``instance_of`` (e.g. ``wd:Q5119`` for capital city)."""
    id_field: str | None = None
    """Model field whose value is appended to ``namespace`` for the subject IRI."""
    prefixes: Mapping[str, str] = field(default_factory=_empty_prefixes)
    embed: EmbedMode = "iri"
    graph_mode: GraphMode = "add"
    blank_node_policy: BlankNodePolicy = "fresh"
    skolemize_export: bool = False
    skolemize_import: bool = False
    base_uri: str | None = None
    """Default base IRI for ``Graph.parse`` (rdflib ``publicID``)."""
    jsonld_context: dict[str, Any] | str | None = None
    """Reserved for API stability; not applied on pyoxigraph (warns if set)."""
    graph_iri: str | None = None
    """Named graph IRI for Dataset contexts; ``None`` uses the default graph."""
    resolve_subclass: bool = True
    """When dispatching, match ``rdfs:subClassOf`` ancestors of ``rdf:type``."""
    strict_import: bool = False
    """Raise when the graph has predicates on the subject outside owned fields."""
    warn_unmapped_fields: bool = False
    """Warn when the graph has predicates on the subject outside owned fields."""

    @property
    def prefixes_dict(self) -> dict[str, str]:
        return dict(self.prefixes)

    @property
    def instance_of_predicates(self) -> tuple[str, ...]:
        raw = self.instance_of
        if raw is None:
            return ()
        if isinstance(raw, str):
            return (raw,) if raw else ()
        return tuple(p for p in raw if p)

    @property
    def instance_type_uris(self) -> tuple[str, ...]:
        raw = self.instance_type_uri
        if raw is None:
            return ()
        if isinstance(raw, str):
            return (raw,) if raw else ()
        return tuple(t for t in raw if t)

    def subject_uri(self, instance: SubjectUriInstance) -> str:
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


def _normalize_graph_iri(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        raise ValueError("graph_iri must be a non-empty IRI when set.")
    return text


def resolve_graph_iri(
    model: BaseModel,
    cfg: RdfConfig | None = None,
) -> str | None:
    """Return the named graph IRI for ``model`` (class config, then instance override)."""
    resolved = cfg or get_rdf_config(type(model))
    graph_iri_method = getattr(model, "graph_iri", None)
    if callable(graph_iri_method):
        override = graph_iri_method()
        if override is not None:
            return _normalize_graph_iri(override)
    instance_value = getattr(model, "_graph_iri", None)
    if instance_value is not None:
        return _normalize_graph_iri(instance_value)
    return resolved.graph_iri


def get_graph_context(
    container: Graph | Dataset,
    graph_iri: str | None = None,
) -> Graph:
    """Return the rdflib ``Graph`` context for triple I/O within ``container``."""
    if not isinstance(container, Dataset):
        return container
    dataset = container
    if graph_iri is None:
        return dataset.default_graph
    normalized = _normalize_graph_iri(graph_iri)
    assert normalized is not None
    return dataset.graph(normalized)


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
            bnode_policy = getattr(rdf, "blank_node_policy", "fresh") or "fresh"
            if bnode_policy not in ("fresh", "stable"):
                warnings.warn(
                    f"{cls.__name__}.Rdf.blank_node_policy={bnode_policy!r} is invalid; "
                    "using 'fresh'.",
                    UserWarning,
                    stacklevel=2,
                )
                bnode_policy = "fresh"
            prefixes = freeze_prefixes(getattr(rdf, "prefixes", None))
            base_uri = getattr(rdf, "base_uri", None)
            jsonld_context = getattr(rdf, "jsonld_context", None)
            graph_iri_raw = getattr(rdf, "graph_iri", None)
            if graph_iri_raw is None:
                graph_iri_raw = getattr(rdf, "graph", None)
            graph_iri = (str(graph_iri_raw).strip() if graph_iri_raw else None) or None
            resolve_subclass = bool(getattr(rdf, "resolve_subclass", True))
            strict_import = bool(getattr(rdf, "strict_import", False))
            warn_unmapped_fields = bool(getattr(rdf, "warn_unmapped_fields", False))
            return RdfConfig(
                namespace=getattr(rdf, "namespace", "") or "",
                type_uri=getattr(rdf, "type_uri", None),
                instance_of=getattr(rdf, "instance_of", None),
                instance_type_uri=getattr(rdf, "instance_type_uri", None),
                id_field=getattr(rdf, "id_field", None),
                prefixes=prefixes,
                embed=embed,
                graph_mode=mode,
                blank_node_policy=bnode_policy,
                skolemize_export=bool(getattr(rdf, "skolemize_export", False)),
                skolemize_import=bool(getattr(rdf, "skolemize_import", False)),
                base_uri=str(base_uri) if base_uri else None,
                jsonld_context=jsonld_context,
                graph_iri=graph_iri,
                resolve_subclass=resolve_subclass,
                strict_import=strict_import,
                warn_unmapped_fields=warn_unmapped_fields,
            )
    return RdfConfig()
