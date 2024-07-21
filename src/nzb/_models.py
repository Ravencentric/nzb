from __future__ import annotations

import re
from functools import cached_property
from os.path import splitext

from natsort import natsorted
from pydantic import BaseModel, ByteSize, ConfigDict

from nzb._types import UTCDateTime
from nzb._utils import cache


class ParentModel(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)


class Metadata(ParentModel):
    """
    Creator-definable metadata for the contents of the NZB.

    Every field here is optional. A valid NZB may or may not have
    any combination of these.
    """

    title: str | None = None
    """Title field. Can only be specified once."""

    passwords: tuple[str, ...] | None = None
    """Password field. Can be specified multiple times."""

    tags: tuple[str, ...] | None = None
    """Tag field. Can be specified multiple times."""

    category: str | None = None
    """Category field. Can only be specified once."""


class Segment(ParentModel):
    """One part segment of a file."""

    size: ByteSize
    """Size of the segment."""
    number: int
    """Number of the segment."""
    message_id: str
    """Message ID of the segment."""


class File(ParentModel):
    """Represents a complete file, consisting of segments that make up a file."""

    poster: str
    """The poster of the file."""

    datetime: UTCDateTime
    """The date and time when the file was posted, in UTC."""

    subject: str
    """
    The subject of the file. 
    Ideally it contains the filename, segment count, and other relevant information.
    """

    groups: tuple[str, ...]
    """Groups that reference the file. Every file must have atleast one group."""

    segments: tuple[Segment, ...]
    """Segments that make up the file. Every file must have atleast one segment."""

    @cached_property
    def size(self) -> ByteSize:
        """Size of the file calculated from the sum of segment sizes."""
        return ByteSize(sum(segment.size for segment in self.segments))

    @cached_property
    def name(self) -> str:
        """
        Complete name of the file with it's extension extracted from the subject.
        May return an empty string if it fails to extract the name.

        Notes
        -----
        This uses regex to extract the filename from the subject,
        and said regex was taken from [SABnzbd](https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L104-L106).
        """
        if parsed := re.search(r'"([^"]*)"', self.subject):
            return parsed.group(1).strip()
        elif parsed := re.search(
            r"\b([\w\-+()' .,]+(?:\[[\w\-/+()' .,]*][\w\-+()' .,]*)*\.[A-Za-z0-9]{2,4})\b", self.subject
        ):
            return parsed.group(1).strip()
        else:
            return ""

    @cached_property
    def stem(self) -> str:
        """
        Base name of the file without it's extension extracted from the [`File.name`][nzb._models.File.name].
        May return an empty string if it fails to extract the stem.
        """
        if not self.name:
            return ""
        else:
            root, _ = splitext(self.name)
            return root if root else ""

    @cached_property
    def suffix(self) -> str:
        """
        Extension of the file extracted from the [`File.name`][nzb._models.File.name].
        May return an empty string if it fails to extract the extension.
        """
        if not self.name:
            return ""
        else:
            _, ext = splitext(self.name)
            return ext if ext else ""

    @cache
    def is_par2(self) -> bool:
        """
        Return `True` if the file is a `.par2` file, `False` otherwise.
        """
        if not self.name:
            return False
        else:
            parsed = re.search(r"\.par2$", self.name, re.IGNORECASE)
            return True if parsed else False

    @cache
    def is_rar(self) -> bool:
        """
        Return `True` if the file is a `.rar` file, `False` otherwise.

        Notes
        -----
        This uses regex to check whether the file is `rar` or not,
        and said regex was taken from [SABnzbd](https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L107).
        """
        if not self.name:
            return False
        else:
            parsed = re.search(r"(\.rar|\.r\d\d|\.s\d\d|\.t\d\d|\.u\d\d|\.v\d\d)$", self.name, re.IGNORECASE)
            return True if parsed else False

    @cache
    def is_obfuscated(
        self,
    ) -> bool:  # pragma: no cover; this method is copied straight from SABnzbd and tested there so don't need to test it here too.
        """
        Return `True` if the file is a obfuscated, `False` otherwise.

        Notes
        -----
        This method is pretty much a copy and paste from [SABnzbd](https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/deobfuscate_filenames.py#L105).
        """

        if not self.stem:
            return True

        # First: the patterns that are certainly obfuscated:

        # ...blabla.H.264/b082fa0beaa644d3aa01045d5b8d0b36.mkv is certainly obfuscated
        if re.findall(r"^[a-f0-9]{32}$", self.stem):
            # exactly 32 hex digits, so:
            return True

        # 0675e29e9abfd2.f7d069dab0b853283cc1b069a25f82.6547
        if re.findall(r"^[a-f0-9.]{40,}$", self.stem):
            return True

        # "[BlaBla] something [More] something 5937bc5e32146e.bef89a622e4a23f07b0d3757ad5e8a.a02b264e [Brrr]"
        # So: square brackets plus 30+ hex digit
        if re.findall(r"[a-f0-9]{30}", self.stem) and len(re.findall(r"\[\w+\]", self.stem)) >= 2:
            return True

        # /some/thing/abc.xyz.a4c567edbcbf27.BLA is certainly obfuscated
        if re.findall(r"^abc\.xyz", self.stem):
            # ... which we consider as obfuscated:
            return True

        # Then: patterns that are not obfuscated but typical, clear names:

        # these are signals for the obfuscation versus non-obfuscation
        decimals = sum(1 for c in self.stem if c.isnumeric())
        upperchars = sum(1 for c in self.stem if c.isupper())
        lowerchars = sum(1 for c in self.stem if c.islower())
        spacesdots = sum(1 for c in self.stem if c == " " or c == "." or c == "_")  # space-like symbols

        # Example: "Great Distro"
        if upperchars >= 2 and lowerchars >= 2 and spacesdots >= 1:
            return False

        # Example: "this is a download"
        if spacesdots >= 3:
            return False

        # Example: "Beast 2020"
        if (upperchars + lowerchars >= 4) and decimals >= 4 and spacesdots >= 1:
            return False

        # Example: "Catullus", starts with a capital, and most letters are lower case
        if self.stem[0].isupper() and lowerchars > 2 and upperchars / lowerchars <= 0.25:
            return False

        # Finally: default to obfuscated:
        return True  # default is obfuscated


class NZB(ParentModel):
    """Represents a complete NZB file."""

    metadata: Metadata = Metadata()
    """Creator-definable metadata for the contents of the NZB."""

    files: tuple[File, ...]
    """File objects representing the files included in the NZB."""

    @cached_property
    def file(self) -> File:
        """
        The main content file (episode, movie, etc) in the NZB.
        """
        return max(self.files, key=lambda file: file.size)

    @cached_property
    def size(self) -> ByteSize:
        """Total size of all the files in the NZB."""
        return ByteSize(sum(file.size for file in self.files))

    @cached_property
    def names(self) -> tuple[str, ...]:
        """
        Tuple of unique file names across all the files in the NZB.
        May return an empty tuple if it fails to extract the name for every file.
        """
        return tuple(natsorted({file.name for file in self.files}))

    @cached_property
    def stems(self) -> tuple[str, ...]:
        """
        Tuple of unique file stems (basename) across all the files in the NZB.
        May return an empty tuple if it fails to extract the stem for every file.
        """
        return tuple(natsorted({file.stem for file in self.files}))

    @cached_property
    def suffixes(self) -> tuple[str, ...]:
        """
        Tuple of unique file extensions across all the files in the NZB.
        May return an empty tuple if it fails to extract the extension for every file.
        """
        return tuple(natsorted({file.suffix for file in self.files}))

    @cached_property
    def posters(self) -> tuple[str, ...]:
        """
        Tuple of unique posters across all the files in the NZB.
        """
        return tuple(natsorted({file.poster for file in self.files}))

    @cached_property
    def groups(self) -> tuple[str, ...]:
        """
        Tuple of unique groups across all the files in the NZB.
        """
        groupset: set[str] = set()

        for file in self.files:
            groupset.update(file.groups)

        return tuple(natsorted(groupset))

    @cache
    def has_rar(self) -> bool:
        """
        Return `True` if any file in the NZB is a `.rar` file, `False` otherwise.
        """
        return any((file.is_rar() for file in self.files))

    @cache
    def is_rar(self) -> bool:
        """
        Return `True` if all files in the NZB are `.rar` files, `False` otherwise.
        """
        return all((file.is_rar() for file in self.files))

    @cache
    def is_obfuscated(self) -> bool:
        """
        Return `True` if any file in the NZB is obfuscated, `False` otherwise.
        """
        return any((file.is_obfuscated() for file in self.files))

    @cache
    def has_par2(self) -> bool:
        """
        Return `True` if there's at least one `.par2` file in the NZB, `False` otherwise.
        """
        return any((file.is_par2() for file in self.files))

    @cache
    def get_par2_percentage(self) -> float:
        """
        Get the percentage of recovery based on the total `.par2` size divided by the total size of all files.
        """
        return (sum(file.size for file in self.files if file.is_par2()) / self.size) * 100
