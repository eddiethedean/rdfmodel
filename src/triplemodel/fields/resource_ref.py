"""IRI reference field type."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


@dataclass(frozen=True)
class ResourceRef:
    """Reference to an RDF resource identified by IRI."""

    iri: str

    def __str__(self) -> str:
        return self.iri

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(cls),
                core_schema.no_info_after_validator_function(
                    cls._validate,
                    core_schema.str_schema(),
                ),
            ]
        )

    @classmethod
    def _validate(cls, value: str | ResourceRef) -> ResourceRef:
        if isinstance(value, ResourceRef):
            return value
        if not value:
            raise ValueError("ResourceRef IRI must not be empty.")
        return cls(value)
