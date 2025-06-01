from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal, overload
from xml.etree import ElementTree

from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, Segment
from nzb._parsers import generate_header, nzb_to_tree, parse_files, parse_metadata
from nzb._utils import read_nzb_file, realpath, to_iterable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

    from _typeshed import StrPath, SupportsRichComparison
    from typing_extensions import Self


@dataclass(frozen=True, kw_only=True)
class Nzb:
    """
    Represents a complete NZB file.

    Example:
    -------
    ```python
    from nzb import Nzb

    text = '''
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Big Buck Bunny - S01E01.mkv</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
            <meta type="category">TV</meta>
        </head>
        <file poster="John &lt;nzb@nowhere.example&gt;" date="1706440708" subject="[1/1] - &quot;Big Buck Bunny - S01E01.mkv&quot; yEnc (1/2) 1478616">
            <groups>
                <group>alt.binaries.boneless</group>
            </groups>
            <segments>
                <segment bytes="739067" number="1">9cacde4c986547369becbf97003fb2c5-9483514693959@example</segment>
                <segment bytes="739549" number="2">70a3a038ce324e618e2751e063d6a036-7285710986748@example</segment>
            </segments>
        </file>
    </nzb>
    '''

    nzb = Nzb.from_str(text)

    print(f"{nzb.file.name} ({nzb.meta.category}) was posted by {nzb.file.poster} on {nzb.file.posted_at}.")
    print(f"Number of files: {len(nzb.files)}")
    print(f"Total size in bytes: {nzb.size}")
    ```

    """  # noqa: E501

    meta: Meta = field(default_factory=Meta)
    """Optional creator-definable metadata for the contents of the NZB."""

    files: tuple[File, ...]
    """File objects representing the files included in the NZB."""

    @classmethod
    def from_str(cls, nzb: str, /) -> Self:
        """
        Parse the given string into an [`Nzb`][nzb.Nzb].

        Parameters
        ----------
        nzb : str
            NZB string.

        Returns
        -------
        Nzb
            Object representing the parsed NZB file.

        Raises
        ------
        InvalidNzbError
            Raised if the NZB is invalid.

        """
        tree = nzb_to_tree(nzb)
        meta = parse_metadata(tree)
        files = parse_files(tree)

        return cls(meta=meta, files=files)

    @classmethod
    def from_file(cls, nzb: StrPath, /) -> Self:
        """
        Parse the given file into an [`Nzb`][nzb.Nzb].
        Handles both regular and gzipped NZB files.

        Parameters
        ----------
        nzb : StrPath
            Path to the NZB file.

        Returns
        -------
        Self
            Object representing the parsed NZB file.

        Raises
        ------
        FileNotFoundError
            Raised if the specified file doesn't exist.

        InvalidNzbError
            Raised if the NZB is invalid.

        """
        return cls.from_str(read_nzb_file(nzb))

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
        dejson = json.loads(data)

        try:
            meta = Meta(
                title=dejson["meta"]["title"],
                passwords=tuple(dejson["meta"]["passwords"]),
                tags=tuple(dejson["meta"]["tags"]),
                category=dejson["meta"]["category"],
            )
            files: list[File] = []

            for file in dejson["files"]:
                segments = tuple(
                    Segment(size=segment["size"], number=segment["number"], message_id=segment["message_id"])
                    for segment in file["segments"]
                )
                groups = tuple(file["groups"])
                posted_at = datetime.strptime(file["posted_at"], "%Y-%m-%dT%H:%M:%S%z")

                files.append(
                    File(
                        poster=file["poster"],
                        posted_at=posted_at,
                        subject=file["subject"],
                        groups=groups,
                        segments=segments,
                    )
                )
        except (KeyError, TypeError, ValueError):
            msg = (
                f"The provided JSON data is not in the expected format or contains invalid values. "
                f"This method only works with JSON produced by `{cls.__name__}.to_json()`."
            )
            raise InvalidNzbError(msg) from None

        return cls(meta=meta, files=tuple(files))

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

        def default(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
            msg = f"Object of type {type(obj).__name__} is not JSON serializable"  # pragma: no cover
            raise TypeError(msg)  # pragma: no cover

        indent = 2 if pretty else None
        return json.dumps(dataclasses.asdict(self), indent=indent, default=default)

    @cached_property
    def file(self) -> File:
        """
        The main content file (episode, movie, etc) in the NZB.
        This is determined by finding the largest file in the NZB
        and may not always be accurate.
        """
        return max(self.files, key=lambda file: file.size)

    @cached_property
    def size(self) -> int:
        """Total size of all the files in the NZB."""
        return sum(file.size for file in self.files)

    @cached_property
    def filenames(self) -> tuple[str, ...]:
        """
        Tuple of unique file names across all the files in the NZB.
        May return an empty tuple if it fails to extract the name for every file.
        """
        return tuple(sorted({file.name for file in self.files if file.name is not None}))

    @cached_property
    def posters(self) -> tuple[str, ...]:
        """
        Tuple of unique posters across all the files in the NZB.
        """
        return tuple(sorted({file.poster for file in self.files}))

    @cached_property
    def groups(self) -> tuple[str, ...]:
        """
        Tuple of unique groups across all the files in the NZB.
        """
        groupset: set[str] = set()

        for file in self.files:
            groupset.update(file.groups)

        return tuple(sorted(groupset))

    @cached_property
    def par2_files(self) -> tuple[File, ...]:
        """
        Tuple of par2 files in the NZB.
        """
        return tuple(sorted((file for file in self.files if file.is_par2()), key=lambda f: f.subject))

    @cached_property
    def par2_size(self) -> int:
        """
        Total size of all the `.par2` files.
        """
        return sum(file.size for file in self.par2_files)

    @cached_property
    def par2_percentage(self) -> float:
        """
        Percentage of the size of all the `.par2` files relative to the total size.
        """
        return (self.par2_size / self.size) * 100

    def has_extension(self, ext: str, /) -> bool:
        """
        Check if any file in the NZB has the specified extension.

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
            `True` if any file in the NZB has the specified extension, `False` otherwise.
        ```

        """
        return any(f.has_extension(ext) for f in self.files)

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


class NzbMetaEditor:
    def __init__(self, nzb: str, /) -> None:
        """
        Create an NzbMetaEditor instance.

        Parameters
        ----------
        nzb : str
            NZB content as a string.

        Raises
        ------
        InvalidNzbError
            If the string cannot be parsed as valid XML.

        Note
        ----
        This does not validate the given NZB.

        Example
        -------
        ```python
        from nzb import NzbMetaEditor

        text = '''
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
        <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
            <head>
                <meta type="title">Big Buck Bunny - S01E01.mkv</meta>
                <meta type="password">secret</meta>
                <meta type="tag">HD</meta>
                <meta type="category">TV</meta>
            </head>
            <file poster="John &lt;nzb@nowhere.example&gt;" date="1706440708" subject="[1/1] - &quot;Big Buck Bunny - S01E01.mkv&quot; yEnc (1/2) 1478616">
                <groups>
                    <group>alt.binaries.boneless</group>
                </groups>
                <segments>
                    <segment bytes="739067" number="1">9cacde4c986547369becbf97003fb2c5-9483514693959@example</segment>
                    <segment bytes="739549" number="2">70a3a038ce324e618e2751e063d6a036-7285710986748@example</segment>
                </segments>
            </file>
        </nzb>
        '''

        editor = NzbMetaEditor(text)
        edited = editor.set(title="Big Buck Bunny").append(tags="1080p").to_str()
        print(edited)
        ```

        """  # noqa: E501
        self._nzb = nzb
        self._tree = nzb_to_tree(self._nzb)

    @classmethod
    def from_file(cls, nzb: StrPath, /) -> Self:
        """
        Create an NzbMetaEditor instance from an NZB file path.

        Parameters
        ----------
        nzb : StrPath
            File path to the NZB.

        Returns
        -------
        Self
            Returns itself.

        """
        return cls(read_nzb_file(nzb))

    def sort(self, key: Callable[[ElementTree.Element], SupportsRichComparison] | None = None) -> Self:
        """
        Sort the metadata fields.

        Parameters
        ----------
        key : Callable[[ElementTree.Element], SupportsRichComparison], optional
            A callable that takes a `<meta>` Element and returns a comparable
            value.

        Returns
        -------
        Self
            Returns itself.

        Examples
        --------
        Here's an example where we sort the meta fields by their type.
        This is also what `sort()` does when you call it without a key.
        ```py
        editor = NzbMetaEditor(...)

        def key(element: ElementTree.Element) -> int:
            if typ := element.get("type"):
                return {"title": 0, "category": 1, "password": 2, "tag": 3}.get(typ, -1)
            return -1

        editor.sort(key=key)
        ```

        """
        if key is None:

            def key(element: ElementTree.Element) -> int:  # pragma: no cover
                if typ := element.get("type"):
                    return {"title": 0, "category": 1, "password": 2, "tag": 3}.get(typ, -1)
                return -1

        if (head := self._tree.find("./head")) is not None:
            head[:] = sorted(
                head.findall("./meta"),
                key=key,
            )
        return self

    def set(
        self,
        *,
        title: str | None = None,
        passwords: Iterable[str] | str | None = None,
        tags: Iterable[str] | str | None = None,
        category: str | None = None,
    ) -> Self:
        """
        Set metadata fields in the NZB.
        Provided fields are replaced entirely if they already exist.
        Fields that aren't provided remain unchanged.

        Parameters
        ----------
        title : str, optional
            The title metadata field.
        passwords : Iterable[str] | str, optional
            Password(s) for the NZB file.
        tags : Iterable[str] | str, optional
            Tag(s) associated with the NZB file.
        category : str, optional
            Category of the NZB file.

        Returns
        -------
        Self
            Returns itself.

        """

        head = self._tree.find("./head")
        if head is None:
            head = ElementTree.Element("head")
            self._tree.insert(0, head)

        if title:
            self.remove("title")
            sub = ElementTree.SubElement(head, "meta")
            sub.set("type", "title")
            sub.text = title

        if passwords:
            self.remove("password")
            for password in to_iterable(passwords):
                sub = ElementTree.SubElement(head, "meta")
                sub.set("type", "password")
                sub.text = password

        if tags:
            self.remove("tag")
            for tag in to_iterable(tags):
                sub = ElementTree.SubElement(head, "meta")
                sub.set("type", "tag")
                sub.text = tag

        if category:
            self.remove("category")
            sub = ElementTree.SubElement(head, "meta")
            sub.set("type", "category")
            sub.text = category

        return self.sort()

    def append(
        self,
        *,
        passwords: Iterable[str] | str | None = None,
        tags: Iterable[str] | str | None = None,
    ) -> Self:
        """
        Append metadata fields to the existing metadata in the NZB.

        Parameters
        ----------
        passwords : Iterable[str] | str, optional
            Password(s) for the NZB file.
        tags : Iterable[str] | str, optional
            Tag(s) associated with the NZB file.

        Returns
        -------
        Self
            Returns itself.

        """

        head = self._tree.find("./head")
        if head is None:
            head = ElementTree.Element("head")
            self._tree.insert(0, head)

        if passwords:
            for password in to_iterable(passwords):
                sub = ElementTree.SubElement(head, "meta")
                sub.set("type", "password")
                sub.text = password

        if tags:
            for tag in to_iterable(tags):
                sub = ElementTree.SubElement(head, "meta")
                sub.set("type", "tag")
                sub.text = tag

        return self.sort()

    @overload
    def remove(self, key: Literal["title", "password", "tag", "category"]) -> Self: ...

    @overload
    def remove(self, key: str) -> Self: ...

    def remove(self, key: Literal["title", "password", "tag", "category"] | str) -> Self:
        """
        Remove a metadata field from the NZB.
        If the same field is present multiple times, this will remove them all.

        Parameters
        ----------
        key : Literal["title", "password", "tag", "category"] | str, optional
            The metadata field to remove.

        Returns
        -------
        Self
            Returns itself.

        """

        if (head := self._tree.find("./head")) is not None:
            matches = [meta for meta in head.findall("./meta") if meta.get("type") == key]

            for match in matches:
                head.remove(match)

        return self

    def clear(self) -> Self:
        """
        Clear all metadata fields from the NZB.

        Returns
        -------
        Self
            Returns itself.

        """
        if (head := self._tree.find("./head")) is not None:
            head.clear()
            self._tree.remove(head)
        return self

    def to_str(self) -> str:
        """
        Return the edited NZB as a string.

        Returns
        -------
        str
            Edited NZB.

        """
        ElementTree.indent(self._tree, space=" " * 4)
        body: str = ElementTree.tostring(
            self._tree,
            encoding="utf-8",
            xml_declaration=False,
        ).decode("utf-8")
        body = body.replace("<nzb>", '<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">')
        return generate_header(self._nzb) + body

    def to_file(self, filename: StrPath, *, overwrite: bool = False) -> Path:
        """
        Save the edited NZB to a file.

        Parameters
        ----------
        filename : StrPath, optional
            Destination path for saving the NZB.
            This will also create the path if it doesn't exist already.
        overwrite : bool, optional
            Whether to overwrite the file if it exists, defaults to `False`.

        Returns
        -------
        Path
            The path to the saved file.

        Raises
        ------
        FileExistsError
            If the file exists and overwrite is `False`.

        """

        outfile = realpath(filename)

        if outfile.is_file() and not overwrite:
            raise FileExistsError(outfile)

        outfile.parent.mkdir(parents=True, exist_ok=True)
        outfile.write_text(self.to_str(), encoding="utf-8")
        return outfile
