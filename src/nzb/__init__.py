from __future__ import annotations

from nzb._core import NZBMetaEditor, NZBParser
from nzb._exceptions import InvalidNZBError, NZBException
from nzb._models import NZB, File, Metadata, Segment
from nzb._version import Version, _get_version

__version__ = _get_version()
__version_tuple__ = Version(*[int(i) for i in __version__.split(".")])

__all__ = ("NZBParser", "NZBMetaEditor", "Metadata", "File", "Segment", "NZB", "NZBException", "InvalidNZBError")
