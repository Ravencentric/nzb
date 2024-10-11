from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload
from xml.parsers.expat import ExpatError

from xmltodict import parse as xmltodict_parse
from xmltodict import unparse as xmltodict_unparse

from nzb._exceptions import InvalidNZBError
from nzb._models import NZB
from nzb._parser import parse_doctype, parse_files, parse_metadata
from nzb._utils import meta_constructor, realpath

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import Self

    from nzb._types import StrPath


class NZBParser:
    def __init__(self, nzb: str, *, encoding: str | None = "utf-8") -> None:
        """
        Initialize the NZBParser.

        Parameters
        ----------
        nzb : str
            NZB content as a string.
        encoding : str, optional
            Encoding of the NZB content.
        """
        self.__nzb = nzb
        self.__encoding = encoding

    def parse(self) -> NZB:
        """
        Parse the NZB.

        Returns
        -------
        NZB
            NZB object representing the parsed NZB file.

        Raises
        ------
        InvalidNZBError
            Raised if the input is not valid NZB.
        """
        try:
            nzbdict = xmltodict_parse(self.__nzb, encoding=self.__encoding)
        except ExpatError as error:
            raise InvalidNZBError(error.args[0])

        meta = parse_metadata(nzbdict)
        files = parse_files(nzbdict)

        return NZB(meta=meta, files=files)

    @classmethod
    def from_file(cls, nzb: StrPath, *, encoding: str | None = "utf-8") -> Self:
        """
        Create an NZBParser instance from an NZB file path.

        Parameters
        ----------
        nzb : StrPath
            File path to the NZB.
        encoding : str, optional
            Encoding of the NZB, defaults to `utf-8`.

        Returns
        -------
        NZBParser
            An NZBParser instance initialized with the content of the specified NZB file.
        """
        nzb = realpath(nzb).read_text(encoding=encoding)
        return cls(nzb, encoding=encoding)


class NZBMetaEditor:
    def __init__(self, nzb: str, *, encoding: str = "utf-8") -> None:
        """
        Initialize the NZBMetaEditor instance.

        Parameters
        ----------
        nzb : str
            NZB content as a string.
        encoding : str, optional
            Encoding of the NZB content, defaults to `utf-8`.

        Raises
        ------
        InvalidNZBError
            Raised if the input is not valid XML.
            However, being valid XML doesn't guarantee it's a correctly structured NZB.
        """
        self.__nzb = nzb
        self.__encoding = encoding
        try:
            self.__nzbdict = xmltodict_parse(self.__nzb, encoding=self.__encoding)
        except ExpatError as error:
            raise InvalidNZBError(error.args[0])

    def __get_meta(self) -> list[dict[str, str]] | dict[str, str] | None:
        """
        Retrieve current metadata from the NZB.

        Returns
        -------
        list[dict[str, str]] | dict[str, str] | None
            The metadata as a list of dictionaries, a single dictionary, or `None` if not found.
        """
        return self.__nzbdict.get("nzb", {}).get("head", {}).get("meta")  # type: ignore

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
        This will also remove all existing metadata fields.

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

        nzb = OrderedDict(self.__nzbdict["nzb"])

        nzb["head"] = {}
        nzb["head"]["meta"] = meta_constructor(title=title, passwords=passwords, tags=tags, category=category)
        nzb.move_to_end("file")
        self.__nzbdict["nzb"] = nzb
        return self

    def append(
        self,
        *,
        title: str | None = None,
        passwords: Iterable[str] | str | None = None,
        tags: Iterable[str] | str | None = None,
        category: str | None = None,
    ) -> Self:
        """
        Append metadata fields to the existing metadata in the NZB.

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

        meta = self.__get_meta()

        if meta is None:
            self.set(title=title, passwords=passwords, tags=tags, category=category)

        elif isinstance(meta, dict):
            new_meta = [meta]
            new_meta.extend(meta_constructor(title=title, passwords=passwords, tags=tags, category=category))
            self.__nzbdict["nzb"]["head"]["meta"] = new_meta

        else:
            meta.extend(meta_constructor(title=title, passwords=passwords, tags=tags, category=category))
            self.__nzbdict["nzb"]["head"]["meta"] = meta

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

        meta = self.__get_meta()

        if meta is None:
            return self

        elif isinstance(meta, dict):
            if key == meta["@type"]:
                return self.clear()
            else:
                return self
        else:
            new_meta = [row for row in meta if row["@type"] != key]
            self.__nzbdict["nzb"]["head"]["meta"] = new_meta
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
            del self.__nzbdict["nzb"]["head"]
        except KeyError:
            pass

        return self

    def save(self, filename: StrPath | None = None, *, overwrite: bool = False) -> Path:
        """
        Save the edited NZB to a file.

        Parameters
        ----------
        filename : StrPath, optional
            Destination path for saving the NZB.
            If not provided, uses the original file path if available.
            This will also create the path if it doesn't exist already.
        overwrite : bool, optional
            Whether to overwrite the file if it exists, defaults to `False`.

        Returns
        -------
        Path
            The path to the saved file.

        Raises
        ------
        FileNotFoundError
            If no filename is specified and the original file path is unknown.
        FileExistsError
            If the file exists and overwrite is `False`.
        """

        self_filename: Path | None = getattr(self, "__nzb_file", None)

        if filename is None:
            if self_filename is None:
                raise FileNotFoundError("No filename specified!")
            else:
                if overwrite:
                    outfile = self_filename
                else:
                    raise FileExistsError(self_filename)
        else:
            outfile = realpath(filename)

        outfile.parent.mkdir(parents=True, exist_ok=True)
        unparsed = xmltodict_unparse(self.__nzbdict, encoding=self.__encoding, pretty=True, indent="    ")

        if doctype := parse_doctype(self.__nzb):
            # see: https://github.com/martinblech/xmltodict/issues/351
            nzb = unparsed.splitlines(keepends=True)
            nzb.insert(1, f"{doctype}\n")
            with open(outfile, "w", encoding=self.__encoding) as f:
                f.writelines(nzb)
        else:
            outfile.write_text(unparsed, encoding=self.__encoding)

        return outfile

    @classmethod
    def from_file(cls, nzb: StrPath, *, encoding: str = "utf-8") -> Self:
        """
        Create an NZBMetaEditor instance from an NZB file path.

        Parameters
        ----------
        nzb : StrPath
            File path to the NZB.
        encoding : str, optional
            Encoding of the NZB, defaults to `utf-8`.

        Returns
        -------
        Self
            Returns itself.
        """
        __nzb_file = realpath(nzb)
        data = __nzb_file.read_text(encoding=encoding)
        instance = cls(data, encoding=encoding)
        setattr(instance, "__nzb_file", __nzb_file)
        return instance
