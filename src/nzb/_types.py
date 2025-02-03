from __future__ import annotations

from os import PathLike
from typing import TypeAlias

StrPath: TypeAlias = str | PathLike[str]
"""String or pathlib.Path"""
