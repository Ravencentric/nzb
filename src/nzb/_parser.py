"""
https://sabnzbd.org/wiki/extra/nzb-spec
https://web.archive.org/web/20240709113825/https://sabnzbd.org/wiki/extra/nzb-spec
"""

from __future__ import annotations

import re
from typing import Any

from natsort import natsorted

from nzb._exceptions import InvalidNZBError
from nzb._models import File, Metadata, Segment


def parse_metadata(nzb: dict[str, Any]) -> Metadata:
    """
    Parses the <meta>...</meta> field present in an NZB.

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

    # This will either be a dict (single metadata key)
    # or a list of dicts (multiple metadata keys)
    meta = nzb.get("nzb", dict()).get("head", dict()).get("meta")

    if meta is None:
        # Metadata is optional
        return Metadata()

    if isinstance(meta, dict):
        meta = [meta]

    passwordset = set()
    tagset = set()
    title = None
    name = None
    category = None

    for item in meta:
        if item.get("@type", "").casefold() == "title":
            title = item.get("#text")

        # This isn't part of the spec, but something
        # I've noticed being used instead of the `title` field
        if item.get("@type", "").casefold() == "name":
            name = item.get("#text")

        if item.get("@type", "").casefold() == "password":
            # spec allows for multiple passwords by repeating the same field
            # <meta type="password">secret1</meta>
            # <meta type="password">secret2</meta>
            # <meta type="password">secret3</meta>
            if password := item.get("#text"):
                passwordset.add(password)

        if item.get("@type", "").casefold() == "tag":
            # spec allows for multiple tags by repeating the same field
            # <meta type="tag">HD</meta>
            # <meta type="tag">Anime</meta>
            # <meta type="tag">1080p</meta>
            if tag := item.get("#text"):
                tagset.add(tag.strip())

        if item.get("@type", "").casefold() == "category":
            category = item.get("#text")

    return Metadata(
        title=title or name,
        passwords=passwordset if passwordset else None,  # type: ignore
        tags=tagset if tagset else None,  # type: ignore
        category=category,
    )


def parse_segments(segments: dict[str, list[dict[str, str]] | dict[str, str]] | None) -> tuple[Segment, ...]:
    """
    Parses the <segments>...</segments> field present in an NZB.

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

    if segments is None:
        raise InvalidNZBError("Missing or malformed <segments>...</segments>!")

    segmentset = set()
    segmentlist = [segments["segment"]] if isinstance(segments["segment"], dict) else segments["segment"]

    for segment in segmentlist:
        size = segment["@bytes"]
        number = segment["@number"]
        message_id = segment["#text"]

        segmentset.add(Segment(size=size, number=number, message_id=message_id))  # type: ignore

    if len(segmentset) == 0:  # pragma: no cover
        raise InvalidNZBError("Missing segments!")

    return tuple(natsorted(segmentset, key=lambda seg: seg.number))


def parse_files(nzb: dict[str, Any]) -> tuple[File, ...]:
    """
    Parses the <file>...</file> field present in an NZB.

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

    # This will either be a dict (single file)
    # or a list of dicts (multiple files)
    try:
        files = nzb.get("nzb", dict()).get("file")
    except Exception as error:  # pragma: no cover
        raise InvalidNZBError("Missing or malformed <file>...</file>!") from error

    if files is None:
        raise InvalidNZBError("Missing or malformed <file>...</file>!")

    if isinstance(files, dict):
        files = [files]

    fileset: set[File] = set()

    for file in files:
        groupset: set[str] = set()
        try:
            groups: list[str] | str = file.get("groups", dict()).get("group", [])
        except Exception as error:
            raise InvalidNZBError("Missing or malformed <groups>...</groups>!") from error

        if isinstance(groups, str):
            groupset.add(groups)
        else:
            groupset.update(groups)

        if len(groupset) == 0:
            raise InvalidNZBError("Missing groups!")

        fileset.add(
            File(
                poster=file.get("@poster"),  # type: ignore
                datetime=file.get("@date"),  # type: ignore
                subject=file.get("@subject"),  # type: ignore
                groups=natsorted(groupset),  # type: ignore
                segments=parse_segments(file.get("segments")),
            )
        )

    return tuple(natsorted(fileset, key=lambda file: file.subject))


def parse_doctype(nzb: str) -> str | None:
    """
    Parses the DOCTYPE from an NZB file.

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
