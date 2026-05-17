"""RDF configuration attached to Pydantic models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, unquote


def subject_base(namespace: str) -> str:
    """Return the prefix used when appending an id to ``namespace``."""
    return namespace if namespace.endswith(("/", "#")) else namespace + "/"


def id_from_subject_uri(namespace: str, uri: str) -> str | None:
    """Extract the id segment from ``uri`` when it was built from ``namespace``."""
    base = subject_base(namespace)
    if not uri.startswith(base):
        return None
    return unquote(uri[len(base) :])


@dataclass(frozen=True)
class RdfConfig:
    """RDF metadata for an :class:`~rdfmodel.RDFModel` subclass."""

    namespace: str = ""
    type_uri: str | None = None
    id_field: str | None = None
    """Model field whose value is appended to ``namespace`` for the subject IRI."""

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
        base = subject_base(self.namespace)
        segment = quote(str(raw), safe="")
        return f"{base}{segment}"


def get_rdf_config(model_cls: type) -> RdfConfig:
    rdf = getattr(model_cls, "Rdf", None)
    if rdf is None:
        return RdfConfig()
    return RdfConfig(
        namespace=getattr(rdf, "namespace", "") or "",
        type_uri=getattr(rdf, "type_uri", None),
        id_field=getattr(rdf, "id_field", None),
    )


# Namespace constants used by the package
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"

RDF_TYPE = f"{RDF}type"
