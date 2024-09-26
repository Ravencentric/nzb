from __future__ import annotations

import re
from functools import cached_property
from os.path import splitext

from natsort import natsorted
from pydantic import BaseModel, ByteSize, ConfigDict

from nzb._types import UTCDateTime
from nzb._utils import (
    name_is_par2,
    name_is_rar,
    stem_is_obfuscated,
)


class ParentModel(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)


class Meta(ParentModel):
    """Optional creator-definable metadata for the contents of the NZB."""

    title: str | None = None
    """Title."""

    passwords: tuple[str, ...] | None = None  # Can be specified multiple times.
    """Password(s)."""

    tags: tuple[str, ...] | None = None  # Can be specified multiple times.
    """Tag(s)."""

    category: str | None = None
    """Category."""

    @cached_property
    def password(self) -> str | None:
        """
        Return the first password from [`Meta.passwords`][nzb._models.Meta.passwords]
        if it exists, None otherwise.

        This is essentially just syntactic sugar for `password = passwords[0] if passwords else None`
        because although the spec allows multiple passwords, single passwords are far more common.
        """
        return self.passwords[0] if self.passwords else None

    @cached_property
    def tag(self) -> str | None:
        """
        The first tag from [`Meta.tags`][nzb._models.Meta.tags]
        if it exists, None otherwise.

        This is essentially just syntactic sugar for `tag = tags[0] if tags else None`
        because although the spec allows multiple tags, single tags are far more common.
        """
        return self.tags[0] if self.tags else None


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
    """The subject of the file."""  # Ideally it contains the filename, segment count, and other relevant information.

    groups: tuple[str, ...]  # Every file must have atleast one group.
    """Groups that reference the file."""

    segments: tuple[Segment, ...]  # Every file must have atleast one segment.
    """Segments that make up the file."""

    @cached_property
    def size(self) -> ByteSize:
        """Size of the file calculated from the sum of segment sizes."""
        return ByteSize(sum(segment.size for segment in self.segments))

    @cached_property
    def name(self) -> str:
        """
        Complete name of the file with it's extension extracted from the subject.
        May return an empty string if it fails to extract the name.
        """
        # https://github.com/sabnzbd/sabnzbd/blob/02b4a116dd4b46b2d2f33f7bbf249f2294458f2e/sabnzbd/nzbstuff.py#L104-L106
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
            return root

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
            return ext

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


class NZB(ParentModel):
    """Represents a complete NZB file."""

    meta: Meta = Meta()
    """Optional creator-definable metadata for the contents of the NZB."""

    files: tuple[File, ...]
    """File objects representing the files included in the NZB."""

    @cached_property
    def file(self) -> File:
        """
        The main content file (episode, movie, etc) in the NZB.
        This is determined by finding the largest file in the NZB
        and may not always be accurate.
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

    @cached_property
    def par2_size(self) -> ByteSize:
        """
        Total size of all the `.par2` files.
        """
        return ByteSize(sum(file.size for file in self.files if file.is_par2()))

    @cached_property
    def par2_percentage(self) -> float:
        """
        Percentage of the size of all the `.par2` files relative to the total size.
        """
        return (self.par2_size / self.size) * 100

    def has_rar(self) -> bool:
        """
        Return `True` if any file in the NZB is a `.rar` file, `False` otherwise.
        """
        return any(file.is_rar() for file in self.files)

    def is_rar(self) -> bool:
        """
        Return `True` if all files in the NZB are `.rar` files, `False` otherwise.
        """
        return all(file.is_rar() for file in self.files)

    def is_obfuscated(self) -> bool:
        """
        Return `True` if any file in the NZB is obfuscated, `False` otherwise.
        """
        return any(file.is_obfuscated() for file in self.files)

    def has_par2(self) -> bool:
        """
        Return `True` if there's at least one `.par2` file in the NZB, `False` otherwise.
        """
        return any(file.is_par2() for file in self.files)
