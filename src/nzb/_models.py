from __future__ import annotations

from datetime import datetime
from os.path import splitext
from typing import TYPE_CHECKING, Any

import msgspec

from nzb._subparsers import extract_filename_from_subject, name_is_par2, name_is_rar, stem_is_obfuscated

if TYPE_CHECKING:
    from typing_extensions import Self


class Base(
    msgspec.Struct,
    forbid_unknown_fields=True,
    frozen=True,
    kw_only=True,
):
    """Base class for AniList data structures."""

    @classmethod
    def from_dict(cls, data: dict[str, Any], /) -> Self:
        """
        Create an instance of this class from a dictionary.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionary representing the instance of this class.

        Returns
        -------
        Self
            An instance of this class.

        """
        return msgspec.convert(data, type=cls)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the instance of this class into a dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representing the instance of this class.

        """
        return msgspec.to_builtins(self)  # type: ignore[no-any-return]

    @classmethod
    def from_json(cls, data: str | bytes, /) -> Self:
        """
        Create an instance of this class from JSON data.

        Parameters
        ----------
        data : str | bytes
            JSON data representing the instance of this class.

        Returns
        -------
        Self
            An instance of this class.

        """
        return msgspec.json.decode(data, type=cls)

    def to_json(self, *, pretty: bool = False) -> str:
        """
        Serialize the instance of this class into a JSON string.

        Parameters
        ----------
        pretty : bool, optional
            Whether to pretty format the JSON string.

        Returns
        -------
        str
            JSON string representing this class.

        """
        jsonified = msgspec.json.encode(self).decode()

        if pretty:
            return msgspec.json.format(jsonified)

        return jsonified


class Meta(Base, frozen=True, kw_only=True):
    """Optional creator-definable metadata for the contents of the NZB."""

    title: str | None = None
    """Title."""
    passwords: tuple[str, ...] = ()
    """Password(s)."""
    tags: tuple[str, ...] = ()
    """Tag(s)."""
    category: str | None = None
    """Category."""


class Segment(Base, frozen=True, kw_only=True):
    """One part segment of a file."""

    size: int
    """Size of the segment."""
    number: int
    """Number of the segment."""
    message_id: str
    """Message ID of the segment."""


class File(Base, frozen=True, kw_only=True):
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
        else:
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
