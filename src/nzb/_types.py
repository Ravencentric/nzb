from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from pydantic import AfterValidator
from typing_extensions import Annotated, TypeAlias, TypeVar

T = TypeVar("T")

StrPath: TypeAlias = Union[str, Path]
"""String or pathlib.Path"""

UTCDateTime = Annotated[datetime, AfterValidator(lambda dt: dt.astimezone(timezone.utc))]
"""datetime that's always in UTC."""

CollectionOf: TypeAlias = Union[list[T], tuple[T, ...], set[T]]
"""Type alias representing a union of list, tuple, and set."""
