from __future__ import annotations

from datetime import datetime, timezone
from os import PathLike
from typing import Annotated, TypeAlias, TypeVar, Union

from pydantic import AfterValidator

T = TypeVar("T")

StrPath: TypeAlias = Union[str, PathLike[str]]
"""String or pathlib.Path"""

UTCDateTime = Annotated[datetime, AfterValidator(lambda dt: dt.astimezone(timezone.utc))]
"""datetime that's always in UTC."""
