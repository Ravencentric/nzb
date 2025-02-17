"""
https://sabnzbd.org/wiki/extra/nzb-spec
https://web.archive.org/web/20240709113825/https://sabnzbd.org/wiki/extra/nzb-spec
"""  # noqa: D400, D415

from __future__ import annotations

import re
from typing import Any, TypeAlias, cast

import msgspec
from natsort import natsorted

from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, Segment


def parse_metadata(nzb: dict[str, Any]) -> Meta:
    """
    Parse the `<meta>...</meta>` field present in an NZB.

    ```xml
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
            <meta type="category">TV</meta>
        </head>
    </nzb>
    ```
    """

    meta = nzb.get("nzb", {}).get("head", {}).get("meta")
    # There's 3 possible things that we can get from the above here:
    # - A list of dictionaries if there's more than 1 meta field present
    # - A dictionary if there's only one meta field present
    # - None if there's no meta field

    # Here's the type representation of the three possible cases that we need to handle
    MetaFieldType: TypeAlias = list[dict[str, str]] | dict[str, str] | None

    # Explicit cast to tell typecheckers the return type based on the above 3 points.
    meta = cast(MetaFieldType, meta)

    if meta is None:
        # Meta is optional, so we will not error
        # just return an instance with all values set to None
        return Meta()

    if isinstance(meta, dict):
        meta = [meta]

    passwords: list[str] = []
    tags: list[str] = []
    title = None
    category = None

    for item in meta:
        if item.get("@type", "").casefold() == "title":
            title = item.get("#text")

        if item.get("@type", "").casefold() == "password":
            # spec allows for multiple passwords by repeating the same field
            # <meta type="password">secret1</meta>
            # <meta type="password">secret2</meta>
            # <meta type="password">secret3</meta>
            if password := item.get("#text"):
                passwords.append(password)

        if item.get("@type", "").casefold() == "tag":
            # spec allows for multiple tags by repeating the same field
            # <meta type="tag">HD</meta>
            # <meta type="tag">Anime</meta>
            # <meta type="tag">1080p</meta>
            if tag := item.get("#text"):
                tags.append(tag.strip())

        if item.get("@type", "").casefold() == "category":
            category = item.get("#text")

    return Meta(
        title=title,
        passwords=tuple(passwords),
        tags=tuple(tags),
        category=category,
    )


def parse_segments(segmentdict: dict[str, list[dict[str, str]] | dict[str, str] | None] | None) -> tuple[Segment, ...]:
    """
    Parse the `<segments>...</segments>` field present in an NZB.

    There's 3 possible things that we can get here:
    - A list of dictionaries if there's more than 1 segment field present
    - A dictionary if there's only one segment field present
    - None if there's no segment field

    ```xml
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="1071674882" subject="Here's your file!  abc-mr2a.r01 (1/2)">
            <groups>[...]</groups>
            <segments>
                <segment bytes="102394" number="1">123456789abcdef@news.newzbin.com</segment>
                <segment bytes="4501" number="2">987654321fedbca@news.newzbin.com</segment>
            </segments>
        </file>
    </nzb>
    ```
    """
    # It's nested or possibly None
    segments = segmentdict.get("segment") if segmentdict else None

    if segments is None:
        raise InvalidNzbError._from_preset("segments")

    if isinstance(segments, dict):
        segments = [segments]

    segmentlist: list[Segment] = []

    for segment in segments:
        try:
            size = int(segment["@bytes"])
            number = int(segment["@number"])
            message_id = segment["#text"]
        except (KeyError, ValueError):
            # This segment is broken
            # We do not error here because a few missing
            # segments don't invalidate the nzb.
            continue

        segmentlist.append(Segment(size=size, number=number, message_id=message_id))

    return tuple(natsorted(segmentlist, key=lambda seg: seg.number))


def parse_files(nzb: dict[str, Any]) -> tuple[File, ...]:
    """
    Parse the `<file>...</file>` field present in an NZB.

    ```xml
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="1071674882" subject="Here's your file!  abc-mr2a.r01 (1/2)">
            <groups>[...]</groups>
            <segments>[...]</segments>
        </file>
    </nzb>
    ```
    """

    files = nzb.get("nzb", {}).get("file")
    # There's 3 possible things that we can get from the above here:
    # - A list of dictionaries if there's more than 1 file field present, i.e, list[dict[str, str]]
    # - A dictionary if there's only one file field present, i.e, dict[str, str]
    # - None if there's no file field

    # Here's the type representation of the three possible cases that we need to handle
    FileFieldType: TypeAlias = list[dict[str, str]] | dict[str, str] | None

    # Explicit cast to tell typecheckers the return type based on the above 3 points.
    files = cast(FileFieldType, files)

    if files is None:
        raise InvalidNzbError._from_preset("file")

    if isinstance(files, dict):
        files = [files]

    filelist: list[File] = []

    for file in files:
        grouplist: list[str] = []

        groups = file.get("groups").get("group") if file.get("groups") else None
        # There's 3 possible things that we can get from the above here:
        # - A list of strings if there's more than 1 group present, i.e, list[str]
        # - A string if there's only one file field present, i.e, str
        # - None if there's no group field

        # Here's the type representation of the three possible cases that we need to handle
        GroupFieldType: TypeAlias = list[str] | str | None

        # Explicit cast to tell typecheckers the return type based on the above 3 points.
        groups = cast(GroupFieldType, groups)

        if groups is None:
            raise InvalidNzbError._from_preset("groups")

        if isinstance(groups, str):
            grouplist.append(groups)
        else:
            grouplist.extend(groups)

        try:
            _file = msgspec.convert(
                {
                    "poster": file.get("@poster"),  # Can fail
                    "posted_at": file.get("@date"),  # Can fail
                    "subject": file.get("@subject"),  # Can fail
                    "groups": natsorted(grouplist),  # Can't fail, pre-validated
                    "segments": parse_segments(file.get("segments")),  # Can't fail, pre-validated
                },
                type=File,
                strict=False,
            )
        except msgspec.ValidationError as e:
            # There seems to be no way to get the invalid field,
            # other than just regexing it out of the error message.
            if match := re.search(r"\$\.(poster|posted_at|subject)", str(e)):
                attr = match.group(1)
                if attr == "posted_at":
                    attr = "date"
                raise InvalidNzbError(f"Invalid or missing required attribute '{attr}' in a 'file' element.") from None
            else:  # pragma: no cover
                # This should never happen
                raise InvalidNzbError(str(e)) from None

        filelist.append(_file)

    if not filelist:  # pragma: no cover
        # I cannot think of any case where this will ever be raised
        # but just in case
        raise InvalidNzbError._from_preset("file")

    return tuple(natsorted(filelist, key=lambda file: file.subject))


def parse_doctype(nzb: str) -> str | None:
    """
    Parse the DOCTYPE from an NZB file.

    Quoting https://www.oreilly.com/library/view/xml-pocket-reference/9780596100506/ch01s02s09.html:
    "A document type or DOCTYPE declaration provides information to a validating XML parser about how to validate an XML document.
    The DOCTYPE keyword appears first; then the document, or root, element of the document being validated is identified,
    followed by either a SYSTEM or PUBLIC identifier."

    Example:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
    ...
    </nzb>
    ```

    """
    doctype = re.search(r"<!DOCTYPE nzb.*>", nzb, re.IGNORECASE)
    return doctype.group() if doctype else None
