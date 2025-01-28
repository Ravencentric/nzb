from __future__ import annotations

from nzb._core import Nzb, NzbMetaEditor
from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, Segment

__version__ = "0.3.0"

__all__ = (
    "NzbMetaEditor",
    "Meta",
    "File",
    "Segment",
    "Nzb",
    "InvalidNzbError",
    "__version__",
)
