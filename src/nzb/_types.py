from __future__ import annotations

from datetime import datetime, timezone

from pydantic import AfterValidator
from typing_extensions import Annotated, TypeAlias, TypeVar, Union

T = TypeVar("T")


def to_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


UTCDateTime = Annotated[datetime, AfterValidator(to_utc)]
"""datetime that's always in UTC."""

CollectionOf: TypeAlias = Union[list[T], tuple[T, ...], set[T]]
"""Type alias representing a union of list, tuple, and set."""
