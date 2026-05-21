"""Language-tagged RDF literals."""

from __future__ import annotations

from dataclasses import dataclass

from pyoxigraph import BaseDirection

_VALID_DIRECTIONS = frozenset({"ltr", "rtl", "auto"})


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
