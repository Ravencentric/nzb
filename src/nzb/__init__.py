from __future__ import annotations

from nzb._core import Nzb, NzbMetaEditor
from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, Segment

__version__ = "0.4.1"

__all__ = (
    "File",
    "InvalidNzbError",
    "Meta",
    "Nzb",
    "NzbMetaEditor",
    "Segment",
    "__version__",
)
