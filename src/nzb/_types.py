from __future__ import annotations

from datetime import datetime, timezone
from os import PathLike
from typing import Annotated, TypeAlias, Union

from pydantic import AfterValidator

StrPath: TypeAlias = Union[str, PathLike[str]]
"""String or pathlib.Path"""

UTCDateTime = Annotated[datetime, AfterValidator(lambda dt: dt.astimezone(timezone.utc))]
"""datetime that's always in UTC."""
