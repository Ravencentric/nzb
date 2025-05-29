from __future__ import annotations

from dataclasses import dataclass
from os.path import splitext
from typing import TYPE_CHECKING

from nzb._subparsers import extract_filename_from_subject, name_is_par2, name_is_rar, stem_is_obfuscated

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class Meta:
    """Optional creator-definable metadata for the contents of the NZB."""

    title: str | None = None
    """Title."""
    passwords: tuple[str, ...] = ()
    """Password(s)."""
    tags: tuple[str, ...] = ()
    """Tag(s)."""
    category: str | None = None
    """Category."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Segment:
    """One part segment of a file."""

    size: int
    """Size of the segment."""
    number: int
    """Number of the segment."""
    message_id: str
    """Message ID of the segment."""


@dataclass(frozen=True, kw_only=True, slots=True)
class File:
    """Represents a complete file, consisting of segments that make up a file."""

    poster: str
    """The poster of the file."""
    posted_at: datetime
    """The date and time when the file was posted, in UTC."""
    subject: str
    """The subject of the file."""
    groups: tuple[str, ...]
    """Groups that reference the file."""
    segments: tuple[Segment, ...]
    """Segments that make up the file."""

    @property
    def size(self) -> int:
        """Size of the file calculated from the sum of segment sizes."""
        return sum(segment.size for segment in self.segments)

    @property
    def name(self) -> str | None:
        """
        Complete name of the file with it's extension extracted from the subject.
        May return `None` if it fails to extract the name.
        """
        return extract_filename_from_subject(self.subject)

    @property
    def stem(self) -> str | None:
        """
        Base name of the file without it's extension extracted from the [`File.name`][nzb._models.File.name].
        May return `None` if it fails to extract the stem.
        """
        if not self.name:
            return None
        root, _ = splitext(self.name)
        return root

    @property
    def extension(self) -> str | None:
        """
        Extension of the file without the leading dot extracted from the [`File.name`][nzb._models.File.name].
        May return `None` if it fails to extract the extension.
        """
        if not self.name:
            return None
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
        return False if self.name is None else name_is_par2(self.name)

    def is_rar(self) -> bool:
        """
        Return `True` if the file is a `.rar` file, `False` otherwise.
        """
        return False if self.name is None else name_is_rar(self.name)

    def is_obfuscated(self) -> bool:
        """
        Return `True` if the file is obfuscated, `False` otherwise.
        """
        # If we can't even determine the stem, it's most certainly obfuscated.
        return True if self.stem is None else stem_is_obfuscated(self.stem)
