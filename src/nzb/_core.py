from __future__ import annotations

from collections import OrderedDict
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload
from xml.parsers.expat import ExpatError

from natsort import natsorted
from xmltodict import parse as xmltodict_parse
from xmltodict import unparse as xmltodict_unparse

from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, ParentModel
from nzb._parser import parse_doctype, parse_files, parse_metadata
from nzb._utils import construct_meta, realpath, remove_meta_fields, sort_meta

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import Self

    from nzb._types import StrPath


class Nzb(ParentModel):
    """
    Represents a complete NZB file.

    Example
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
    """

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
        try:
            # Note: the .strip() is important, otherwise we get an ExpatError:
            # xml.parsers.expat.ExpatError: XML or text declaration not at start of entity: line 2, column 0
            # This can be easily reproduced with:
            #
            # ```py
            # text = """
            # <xml>
            # """
            # Nzb.from_str(text)
            #
            # ```
            nzbdict = xmltodict_parse(nzb.strip())
        except ExpatError as error:
            raise InvalidNzbError(error.args[0]) from None

        meta = parse_metadata(nzbdict)
        files = parse_files(nzbdict)

        return cls(meta=meta, files=files)

    @classmethod
    def from_file(cls, nzb: StrPath, /, *, encoding: str = "utf-8") -> Nzb:
        """
        Parse the given file into an [`Nzb`][nzb.Nzb].

        Parameters
        ----------
        nzb : str | PathLike[str]
            Path to the NZB file.
        encoding : str, optional
            The encoding used to open the file.

        Returns
        -------
        Nzb
            Object representing the parsed NZB file.

        Raises
        ------
        InvalidNzbError
            Raised if the NZB is invalid.

        """
        if not isinstance(encoding, str):
            raise ValueError("encoding must be a valid string!")

        _nzb = realpath(nzb).read_text(encoding=encoding)
        return cls.from_str(_nzb)

    @classmethod
    def from_json(cls, json: str, /) -> Nzb:
        """
        Deserialize the given JSON string into an [`Nzb`][nzb.Nzb].

        Parameters
        ----------
        json : str
            JSON string representing the NZB.

        Returns
        -------
        Nzb
            Object representing the parsed NZB file.

        Raises
        ------
        InvalidNzbError
            Raised if the NZB is invalid.

        """
        return cls.model_validate_json(json)

    def to_json(self, *, pretty: bool = False) -> str:
        """
        Serialize the [`Nzb`][nzb.Nzb] object into a JSON string.

        Parameters
        ----------
        pretty : bool, optional
            Whether to pretty format the JSON string.

        Returns
        -------
        str
            JSON string representing the NZB.

        """
        indent = 2 if pretty else None
        return self.model_dump_json(indent=indent)

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
        return tuple(natsorted({file.name for file in self.files if file.name is not None}))

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
    def par2_size(self) -> int:
        """
        Total size of all the `.par2` files.
        """
        return sum(file.size for file in self.files if file.is_par2())

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


class NzbMetaEditor:
    def __init__(self, nzb: str) -> None:
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

        """
        self._nzb = nzb
        try:
            # Note: the .strip() is important, otherwise we get an ExpatError:
            # xml.parsers.expat.ExpatError: XML or text declaration not at start of entity: line 2, column 0
            # This can be easily reproduced with:
            #
            # ```py
            # text = """
            # <xml>
            # """
            # NzbMetaEditor(text)
            #
            # ```
            self._nzbdict = xmltodict_parse(self._nzb.strip())
        except ExpatError as error:
            raise InvalidNzbError(error.args[0]) from None

    @classmethod
    def from_file(cls, nzb: StrPath, *, encoding: str = "utf-8") -> Self:
        """
        Create an NzbMetaEditor instance from an NZB file path.

        Parameters
        ----------
        nzb : StrPath
            File path to the NZB.
        encoding : str, optional
            The encoding used to open the file.

        Returns
        -------
        Self
            Returns itself.

        """
        if not isinstance(encoding, str):
            raise ValueError("encoding must be a valid string!")
        data = realpath(nzb).read_text(encoding=encoding)
        instance = cls(data)
        return instance

    def _get_meta(self) -> list[dict[str, str]] | dict[str, str] | None:
        """
        Retrieve current metadata from the NZB.

        Returns
        -------
        list[dict[str, str]] | dict[str, str] | None
            The metadata as a list of dictionaries, a single dictionary, or `None` if not found.

        """
        return self._nzbdict.get("nzb", {}).get("head", {}).get("meta")  # type: ignore[no-any-return]

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

        if title is None and passwords is None and tags is None and category is None:
            return self

        meta = self._get_meta()

        if meta is None:
            nzb = OrderedDict(self._nzbdict["nzb"])
            nzb["head"] = {}
            nzb["head"]["meta"] = sort_meta(
                construct_meta(title=title, passwords=passwords, tags=tags, category=category)
            )
            nzb.move_to_end("file")
            self._nzbdict["nzb"] = nzb
            return self

        new_meta = [meta] if isinstance(meta, dict) else meta

        fields_to_remove = {
            "title": title is not None,
            "category": category is not None,
            "password": passwords is not None,
            "tag": tags is not None,
        }

        filtered_meta = remove_meta_fields(new_meta, [k for k, v in fields_to_remove.items() if v])
        filtered_meta.extend(construct_meta(title=title, passwords=passwords, tags=tags, category=category))
        self._nzbdict["nzb"]["head"]["meta"] = sort_meta(filtered_meta)

        return self

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

        meta = self._get_meta()

        if meta is None:
            return self.set(passwords=passwords, tags=tags)

        new_meta = [meta] if isinstance(meta, dict) else meta
        new_meta.extend(construct_meta(passwords=passwords, tags=tags))

        self._nzbdict["nzb"]["head"]["meta"] = sort_meta(new_meta)

        return self

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

        meta = self._get_meta()

        if meta is None:
            return self

        elif isinstance(meta, dict):
            if key == meta["@type"]:
                return self.clear()
            else:
                return self
        else:
            new_meta = [row for row in meta if row["@type"] != key]
            self._nzbdict["nzb"]["head"]["meta"] = new_meta
            return self

    def clear(self) -> Self:
        """
        Clear all metadata fields from the NZB.

        Returns
        -------
        Self
            Returns itself.

        """
        try:
            del self._nzbdict["nzb"]["head"]
        except KeyError:
            pass

        return self

    def to_str(self) -> str:
        """
        Return the edited NZB as a string.

        Returns
        -------
        str
            Edited NZB.

        """
        unparsed = xmltodict_unparse(self._nzbdict, encoding="utf-8", pretty=True, indent="    ")

        if doctype := parse_doctype(self._nzb):
            # see: https://github.com/martinblech/xmltodict/issues/351
            nzb = unparsed.splitlines()
            nzb.insert(1, doctype)
            return "\n".join(nzb)

        return unparsed.strip()

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
        return outfile.resolve()
