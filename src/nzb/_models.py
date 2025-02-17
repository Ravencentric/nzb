from __future__ import annotations

import re
from datetime import datetime
from functools import cached_property
from os.path import splitext
from typing import TYPE_CHECKING

from msgspec import Struct

from nzb._utils import name_is_par2, name_is_rar, stem_is_obfuscated

if TYPE_CHECKING:
    from typing_extensions import dataclass_transform

    # https://github.com/jcrist/msgspec/issues/657
    @dataclass_transform(frozen_default=True)
    class Base(Struct, frozen=True, eq=True, cache_hash=True, dict=True):
        pass
else:

    class Base(Struct, frozen=True, eq=True, cache_hash=True, dict=True):
        pass


class Meta(Base, kw_only=True):
    """Optional creator-definable metadata for the contents of the NZB."""

    title: str | None = None
    """Title."""

    passwords: tuple[str, ...] = ()  # Can be specified multiple times.
    """Password(s)."""

    tags: tuple[str, ...] = ()  # Can be specified multiple times.
    """Tag(s)."""

    category: str | None = None
    """Category."""


class Segment(Base, kw_only=True):
    """One part segment of a file."""

    size: int
    """Size of the segment."""
    number: int
    """Number of the segment."""
    message_id: str
    """Message ID of the segment."""


class File(Base, kw_only=True):
    """Represents a complete file, consisting of segments that make up a file."""

    poster: str
    """The poster of the file."""

    posted_at: datetime
    """The date and time when the file was posted, in UTC."""

    subject: str
    """The subject of the file."""  # Ideally it contains the filename, segment count, and other relevant information.

    groups: tuple[str, ...]  # Every file must have atleast one group.
    """Groups that reference the file."""

    segments: tuple[Segment, ...]  # Every file must have atleast one segment.
    """Segments that make up the file."""

    @cached_property
    def size(self) -> int:
        """Size of the file calculated from the sum of segment sizes."""
        return sum(segment.size for segment in self.segments)

    @cached_property
    def name(self) -> str | None:
        """
        Complete name of the file with it's extension extracted from the subject.
        May return `None` if it fails to extract the name.
        """
        # https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L104-L106
        if parsed := re.search(r'"([^"]*)"', self.subject):
            return parsed.group(1).strip()
        elif parsed := re.search(
            r"\b([\w\-+()' .,]+(?:\[[\w\-/+()' .,]*][\w\-+()' .,]*)*\.[A-Za-z0-9]{2,4})\b", self.subject
        ):
            return parsed.group(1).strip()

        # https://regex101.com/r/B03qZs/1
        # [011/116] - [AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv yEnc (1/2401) 1720916370
        elif parsed := re.search(
            r"^(\[|\()(\d+/\d+)(\]|\))\s-\s(.*)\syEnc\s(\[|\()(\d+/\d+)(\]|\))\s\d+", self.subject
        ):
            return parsed.group(4).strip() if parsed.group(4) else None
        else:
            return None

    @cached_property
    def stem(self) -> str | None:
        """
        Base name of the file without it's extension extracted from the [`File.name`][nzb._models.File.name].
        May return `None` if it fails to extract the stem.
        """
        if not self.name:
            return None
        else:
            root, _ = splitext(self.name)
            return root

    @cached_property
    def extension(self) -> str | None:
        """
        Extension of the file without the leading dot extracted from the [`File.name`][nzb._models.File.name].
        May return `None` if it fails to extract the extension.
        """
        if not self.name:
            return None
        else:
            _, ext = splitext(self.name)
            return ext.removeprefix(".")

    def has_extension(self, ext: str, /) -> bool:
        """
        Check if the file has the specified extension.

        This method ensures consistent extension comparison
        by normalizing the extension (removing any leading dot)
        and handling case-folding.

        Parameters
        ----------
        ext : str
            Extension to check for, with or without a leading dot (e.g., `.txt` or `txt`).

        Returns
        -------
        bool
            `True` if the file has the specified extension, `False` otherwise.

        Examples
        --------
        ```python
        >>> file.has_extension('.TXT')  # True for 'file.txt'
        True
        >>> file.has_extension('txt')   # Also True for 'file.txt'
        True
        ```

        """
        if not self.extension:
            return False
        return self.extension.casefold() == ext.casefold().removeprefix(".")

    def is_par2(self) -> bool:
        """
        Return `True` if the file is a `.par2` file, `False` otherwise.
        """
        return name_is_par2(self.name)

    def is_rar(self) -> bool:
        """
        Return `True` if the file is a `.rar` file, `False` otherwise.
        """
        return name_is_rar(self.name)

    def is_obfuscated(self) -> bool:
        """
        Return `True` if the file is obfuscated, `False` otherwise.
        """
        return stem_is_obfuscated(self.stem)
