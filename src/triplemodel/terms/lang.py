"""Language-tagged RDF literals."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, cast

from pydantic_core import core_schema
from pydantic_core.core_schema import CoreSchema
from pyoxigraph import BaseDirection

_VALID_DIRECTIONS = frozenset({"ltr", "rtl", "auto"})


def normalize_lang_tag(lang: str) -> str:
    """Normalize an RDF language tag for map keys (case-insensitive per BCP 47)."""
    return lang.lower()


def _direction_to_base(value: str | BaseDirection | None) -> BaseDirection | None:
    if value is None:
        return None
    if isinstance(value, BaseDirection):
        return value
    key = str(value).lower()
    if key not in _VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid text direction {value!r}; expected one of {sorted(_VALID_DIRECTIONS)}."
        )
    return BaseDirection(key)


def _base_direction_name(value: BaseDirection | None) -> str | None:
    if value is None:
        return None
    return str(value).lower()


@dataclass(frozen=True)
class Lang:
    """Field metadata: serialize ``str`` values with a fixed language tag."""

    code: str
    direction: str | None = None


@dataclass(frozen=True)
class LangString:
    """A literal string value with an optional language tag and text direction."""

    value: str
    lang: str | None = None
    direction: str | None = None

    def __post_init__(self) -> None:
        if self.direction is not None:
            _direction_to_base(self.direction)


def _lang_string_for_key(lang: str, value: str | LangString) -> LangString:
    if isinstance(value, LangString):
        return LangString(value.value, lang, value.direction)
    return LangString(value, lang)


@dataclass(frozen=True)
class MultiLangString:
    """Multiple language-tagged literals for one predicate, keyed by language code.

    Use on a single field when the graph has several ``@lang`` objects on the same
    predicate (for example ``rdfs:label@en`` and ``rdfs:label@fr``). Export emits
    one triple per entry; import collects all language-tagged literals on the field.
    """

    by_lang: Mapping[str, LangString]

    def __init__(
        self,
        mapping: Mapping[str, str | LangString | None] | None = None,
        /,
        **langs: str | LangString | None,
    ) -> None:
        combined: dict[str, str | LangString | None] = {}
        if mapping is not None:
            for lang, val in mapping.items():
                combined[normalize_lang_tag(lang)] = val
        for lang, val in langs.items():
            combined[normalize_lang_tag(lang)] = val
        object.__setattr__(
            self,
            "by_lang",
            MappingProxyType(
                {
                    lang: _lang_string_for_key(lang, val)
                    for lang, val in combined.items()
                    if val is not None
                }
            ),
        )

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, str | LangString | None]
    ) -> MultiLangString:
        """Build from a language code → value map (``None`` entries are omitted)."""
        return cls(mapping)

    def __len__(self) -> int:
        return len(self.by_lang)

    def __bool__(self) -> bool:
        return bool(self.by_lang)

    def __getitem__(self, lang: str) -> LangString:
        return self.by_lang[lang]

    def __iter__(self) -> Iterator[tuple[str, LangString]]:
        return iter(self.by_lang.items())

    def get(self, lang: str, default: LangString | None = None) -> LangString | None:
        return self.by_lang.get(lang, default)

    def values(self) -> list[LangString]:
        """Language-tagged literals in arbitrary order (for export)."""
        return list(self.by_lang.values())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls._pydantic_validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.dict_schema(
                        keys_schema=core_schema.str_schema(),
                        values_schema=core_schema.union_schema(
                            [
                                core_schema.str_schema(),
                                core_schema.is_instance_schema(LangString),
                                core_schema.none_schema(),
                            ]
                        ),
                    ),
                ]
            ),
        )

    @classmethod
    def _pydantic_validate(cls, value: object, _info: Any) -> MultiLangString:
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.from_mapping(cast(Mapping[str, str | LangString | None], value))
        raise TypeError(
            f"Expected MultiLangString or dict[str, str | LangString | None], "
            f"got {type(value).__name__}."
        )
