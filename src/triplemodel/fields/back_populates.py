"""Paired inverse metadata across two :class:`~triplemodel.TripleModel` classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pyoxigraph import NamedNode
from triplemodel.store import RdfGraph as Graph
from triplemodel.store.terms import term_str

from triplemodel.config import get_rdf_config
from triplemodel.fields.metadata import (
    inverse_for_field,
    predicate_for_field,
    predicate_from_annotation,
)
from triplemodel.metadata.cardinality import field_annotation
from triplemodel.namespaces import resolve_predicate
from triplemodel.ontology_registry import OntologyRegistry

_BACK_POPULATES_FIELD = "rdf_back_populates_field"
_BACK_POPULATES_MODEL = "rdf_back_populates_model"


@dataclass(frozen=True)
class BackPopulates:
    """Link a field to the inverse-side field on another model (SparqlModel ``back_populates``)."""

    field: str
    model: type[BaseModel] | str


def inverse_pair(model: type[BaseModel] | str, field: str) -> BackPopulates:
    """Shorthand for :class:`BackPopulates`.

    Pass a class or a string name (``inverse_pair(\"Organization\", \"employees\")``)
    when the peer model is declared later in the same module.
    """
    return BackPopulates(field=field, model=model)


BackPopulatesSpec = str | BackPopulates | tuple[type[BaseModel] | str, str]


def normalize_back_populates(spec: BackPopulatesSpec) -> BackPopulates:
    """Normalize ``back_populates`` arguments accepted by :func:`~triplemodel.rdf_field`."""
    if isinstance(spec, BackPopulates):
        return spec
    if isinstance(spec, tuple):
        model, field = spec
        return BackPopulates(field=field, model=model)
    raise TypeError(
        "back_populates must be BackPopulates, inverse_pair(model, field), "
        f"or (model, field); got {type(spec).__name__}"
    )


def _model_qualname(model: type[BaseModel]) -> str:
    return f"{model.__module__}.{model.__qualname__}"


def _resolve_model_qualname(qualname: str) -> type[BaseModel]:
    import sys

    from triplemodel.protocols import iter_registered_model_classes

    parts = qualname.rsplit(".", 1)
    if len(parts) == 2:
        mod_name, attr = parts
        mod = sys.modules.get(mod_name)
        if mod is not None:
            obj = getattr(mod, attr, None)
            if isinstance(obj, type) and issubclass(obj, BaseModel):
                return cast(type[BaseModel], obj)
    short = parts[-1] if parts else qualname
    module_prefix = parts[0] if len(parts) == 2 else ""
    candidates = [
        cls
        for cls in iter_registered_model_classes()
        if cls.__name__ == short and cls.__module__ == module_prefix
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise LookupError(qualname)


def store_back_populates_extra(
    extra: dict[str, object],
    spec: BackPopulates,
) -> None:
    extra[_BACK_POPULATES_FIELD] = spec.field
    if isinstance(spec.model, str):
        extra[_BACK_POPULATES_MODEL] = spec.model
    else:
        extra[_BACK_POPULATES_MODEL] = _model_qualname(spec.model)


def _qualname_from_owner(owner: type[BaseModel], model_ref: str) -> str:
    if "." in model_ref:
        return model_ref
    return f"{owner.__module__}.{model_ref}"


def back_populates_for_field(
    field_info: FieldInfo,
    *,
    owner: type[BaseModel] | None = None,
) -> BackPopulates | None:
    """Return paired-field metadata for ``field_info``, if configured."""
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return None
    extra_dict = cast(dict[str, object], extra)
    field_name = extra_dict.get(_BACK_POPULATES_FIELD)
    model_ref = extra_dict.get(_BACK_POPULATES_MODEL)
    if field_name is None or model_ref is None:
        return None
    qualname = (
        _qualname_from_owner(owner, str(model_ref))
        if owner is not None
        else str(model_ref)
    )
    try:
        model = _resolve_model_qualname(qualname)
    except LookupError:
        return None
    return BackPopulates(field=str(field_name), model=model)


@dataclass
class _PendingLink:
    owner: type[BaseModel]
    field: str
    peer_model_qualname: str
    peer_field: str


_PENDING_LINKS: list[_PendingLink] = []


def _field_predicate(
    model_cls: type[BaseModel],
    field_name: str,
    field_info: FieldInfo,
) -> str | None:
    cfg = get_rdf_config(model_cls)
    raw = predicate_for_field(field_info) or predicate_from_annotation(
        field_annotation(field_info)
    )
    if raw is None:
        return None
    return resolve_predicate(raw, cfg.prefixes_dict)


def _ontology_registry_for(model_cls: type[BaseModel]) -> OntologyRegistry | None:
    for cls in model_cls.__mro__:
        rdf = getattr(cls, "Rdf", None)
        if rdf is None:
            continue
        reg = getattr(rdf, "ontology_registry", None)
        if isinstance(reg, OntologyRegistry):
            return reg
    return None


def _validate_predicate_pair(
    owner: type[BaseModel],
    owner_field: str,
    owner_forward: str,
    owner_inverse: str | None,
    peer: type[BaseModel],
    peer_field: str,
    peer_forward: str,
    peer_inverse: str | None,
    *,
    registry: OntologyRegistry | None,
) -> None:
    if owner_inverse is not None and owner_inverse != peer_forward:
        raise ValueError(
            f"{owner.__name__}.{owner_field}: inverse predicate {owner_inverse!r} "
            f"must match forward predicate on {peer.__name__}.{peer_field} ({peer_forward!r})."
        )
    if peer_inverse is not None and peer_inverse != owner_forward:
        raise ValueError(
            f"{peer.__name__}.{peer_field}: inverse predicate {peer_inverse!r} "
            f"must match forward predicate on {owner.__name__}.{owner_field} ({owner_forward!r})."
        )
    if owner_inverse is None and peer_inverse is None:
        raise ValueError(
            f"{owner.__name__}.{owner_field} and {peer.__name__}.{peer_field}: "
            "at least one side needs inverse= (or InverseOf) for import from the inverse predicate."
        )
    if registry is not None:
        reg_inv = registry.inverse_of(owner_forward)
        if reg_inv is not None and reg_inv != peer_forward:
            raise ValueError(
                f"{owner.__name__}.{owner_field}: ontology inverse_of({owner_forward!r}) "
                f"is {reg_inv!r}, expected {peer_forward!r} from {peer.__name__}.{peer_field}."
            )
        reg_inv_peer = registry.inverse_of(peer_forward)
        if reg_inv_peer is not None and reg_inv_peer != owner_forward:
            raise ValueError(
                f"{peer.__name__}.{peer_field}: ontology inverse_of({peer_forward!r}) "
                f"is {reg_inv_peer!r}, expected {owner_forward!r} from {owner.__name__}.{owner_field}."
            )


def _validate_link(link: _PendingLink) -> bool:
    """Validate one link; return False when the peer model is not ready yet."""
    try:
        peer_model = _resolve_model_qualname(link.peer_model_qualname)
    except LookupError:
        return False
    owner_fields = link.owner.model_fields
    peer_fields = peer_model.model_fields
    if link.field not in owner_fields:
        raise ValueError(
            f"{link.owner.__name__}: back_populates references missing field {link.field!r}."
        )
    if link.peer_field not in peer_fields:
        return False
    peer_info = peer_fields[link.peer_field]
    peer_bp = back_populates_for_field(peer_info, owner=peer_model)
    if peer_bp is None:
        return False
    if not isinstance(peer_bp.model, type) or peer_bp.model is not link.owner:
        peer_label = (
            peer_bp.model if isinstance(peer_bp.model, str) else peer_bp.model.__name__
        )
        raise ValueError(
            f"{peer_model.__name__}.{link.peer_field} must back_populates to "
            f"{link.owner.__name__}.{link.field!r}; got "
            f"{peer_label}.{peer_bp.field!r}."
        )
    if peer_bp.field != link.field:
        raise ValueError(
            f"{peer_model.__name__}.{link.peer_field} must back_populates to "
            f"{link.owner.__name__}.{link.field!r}; got "
            f"{peer_bp.model.__name__}.{peer_bp.field!r}."
        )
    owner_info = owner_fields[link.field]
    owner_forward = _field_predicate(link.owner, link.field, owner_info)
    peer_forward = _field_predicate(peer_model, link.peer_field, peer_info)
    if owner_forward is None or peer_forward is None:
        raise ValueError(
            f"back_populates pair {link.owner.__name__}.{link.field} ↔ "
            f"{peer_model.__name__}.{link.peer_field} requires rdf_predicate on both fields."
        )
    registry = _ontology_registry_for(link.owner) or _ontology_registry_for(peer_model)
    _validate_predicate_pair(
        link.owner,
        link.field,
        owner_forward,
        inverse_for_field(owner_info),
        peer_model,
        link.peer_field,
        peer_forward,
        inverse_for_field(peer_info),
        registry=registry,
    )
    return True


def _misconfigured_pending_reason(link: _PendingLink) -> str | None:
    """Return an error message when the peer model exists but the link is invalid."""
    try:
        peer_model = _resolve_model_qualname(link.peer_model_qualname)
    except LookupError:
        return None
    if link.field not in link.owner.model_fields:
        return (
            f"{link.owner.__name__}: back_populates references missing field "
            f"{link.field!r}."
        )
    peer_fields = peer_model.model_fields
    if link.peer_field not in peer_fields:
        return (
            f"{link.owner.__name__}.{link.field}: back_populates references missing "
            f"field {link.peer_field!r} on {peer_model.__name__}."
        )
    peer_info = peer_fields[link.peer_field]
    if back_populates_for_field(peer_info, owner=peer_model) is not None:
        return None
    peer_extra = peer_info.json_schema_extra
    if isinstance(peer_extra, dict) and (
        peer_extra.get(_BACK_POPULATES_FIELD) is not None
        and peer_extra.get(_BACK_POPULATES_MODEL) is not None
    ):
        return None
    return (
        f"{peer_model.__name__}.{link.peer_field} must declare back_populates "
        f"to {link.owner.__name__}.{link.field!r}."
    )


def register_back_populates(model_cls: type[BaseModel]) -> None:
    """Record and validate ``back_populates`` links declared on ``model_cls``."""
    for name, field_info in model_cls.model_fields.items():
        extra = field_info.json_schema_extra
        if not isinstance(extra, dict):
            continue
        peer_field = extra.get(_BACK_POPULATES_FIELD)
        peer_model_ref = extra.get(_BACK_POPULATES_MODEL)
        if peer_field is None or peer_model_ref is None:
            continue
        link = _PendingLink(
            owner=model_cls,
            field=name,
            peer_model_qualname=_qualname_from_owner(model_cls, str(peer_model_ref)),
            peer_field=str(peer_field),
        )
        if link not in _PENDING_LINKS:
            _PENDING_LINKS.append(link)
    still_pending: list[_PendingLink] = []
    for link in list(_PENDING_LINKS):
        if _validate_link(link):
            continue
        still_pending.append(link)
    for link in still_pending:
        msg = _misconfigured_pending_reason(link)
        if msg is not None:
            raise ValueError(msg)
    _PENDING_LINKS[:] = still_pending


def subjects_via_back_populates(
    instance: BaseModel,
    field_name: str,
    graph: Graph,
) -> list[str]:
    """Return subject IRIs linked via the inverse predicate of ``field_name`` (read-only)."""
    model_cls = type(instance)
    field_info = model_cls.model_fields.get(field_name)
    if field_info is None:
        raise ValueError(f"{model_cls.__name__} has no field {field_name!r}.")
    inv_raw = inverse_for_field(field_info)
    if inv_raw is None:
        raise ValueError(
            f"{model_cls.__name__}.{field_name} has no inverse predicate; "
            "import navigation requires inverse= or InverseOf."
        )
    cfg = get_rdf_config(model_cls)
    inv_pred = NamedNode(resolve_predicate(inv_raw, cfg.prefixes_dict))
    subj = NamedNode(cfg.subject_uri(instance))
    return sorted({term_str(s) for s in graph.subjects(inv_pred, subj)})


def models_via_back_populates(
    instance: BaseModel,
    field_name: str,
    graph: Graph,
) -> list[BaseModel]:
    """Load peer :class:`~triplemodel.TripleModel` instances for inverse-linked subjects."""
    from triplemodel.io.import_ import graph_to_model

    model_cls = type(instance)
    field_info = model_cls.model_fields.get(field_name)
    if field_info is None:
        raise ValueError(f"{model_cls.__name__} has no field {field_name!r}.")
    bp = back_populates_for_field(field_info, owner=model_cls)
    if bp is None:
        raise ValueError(
            f"{type(instance).__name__}.{field_name} has no back_populates metadata."
        )
    if isinstance(bp.model, str):
        peer_model = _resolve_model_qualname(
            _qualname_from_owner(type(instance), bp.model)
        )
    else:
        peer_model = bp.model
    uris = subjects_via_back_populates(instance, field_name, graph)
    return [graph_to_model(graph, peer_model, uri=uri) for uri in uris]


__all__ = [
    "BackPopulates",
    "BackPopulatesSpec",
    "inverse_pair",
    "back_populates_for_field",
    "models_via_back_populates",
    "normalize_back_populates",
    "register_back_populates",
    "store_back_populates_extra",
    "subjects_via_back_populates",
]
