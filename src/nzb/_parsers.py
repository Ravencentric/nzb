"""
https://sabnzbd.org/wiki/extra/nzb-spec
https://web.archive.org/web/20240709113825/https://sabnzbd.org/wiki/extra/nzb-spec
"""  # noqa: D400, D415

from __future__ import annotations

import re
from typing import Any, Literal, TypeAlias, cast

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
    try:
        # Assuming 'meta' exists, there are 2 possible types we can get for 'meta':
        # - A list of dictionaries if multiple meta fields are present.
        # - A dictionary if only one meta field is present.
        meta: list[dict[str, str]] | dict[str, str] = nzb["nzb"]["head"]["meta"]
    except KeyError:
        return Meta()

    fields = [meta] if isinstance(meta, dict) else meta

    passwords: list[str] = []
    tags: list[str] = []
    title = None
    category = None

    for field in fields:
        match field.get("@type", "").casefold().strip():
            case "title":
                title = field.get("#text")

            case "password":
                # spec allows for multiple passwords by repeating the same field
                # <meta type="password">secret1</meta>
                # <meta type="password">secret2</meta>
                # <meta type="password">secret3</meta>
                if password := field.get("#text"):
                    passwords.append(password)

            case "tag":
                # spec allows for multiple tags by repeating the same field
                # <meta type="tag">HD</meta>
                # <meta type="tag">Anime</meta>
                # <meta type="tag">1080p</meta>
                if tag := field.get("#text"):
                    tags.append(tag.strip())

            case "category":
                category = field.get("#text")
            case _:
                # Ignore unknown fields.
                pass

    return Meta(
        title=title,
        passwords=tuple(passwords),
        tags=tuple(tags),
        category=category,
    )


def parse_segments(
    segments: dict[Literal["segment"], list[dict[str, str]] | dict[str, str]] | None,
) -> tuple[Segment, ...]:
    """
    Parse the `<segments>...</segments>` field present in an NZB.

    The `segments` parameter can be:
    - `None`: If the 'segments' field is entirely absent.
    - A dictionary with a single key, `segment`. The value associated with this `segment` key can be:
        - A list of dictionaries, where each dictionary represents a segment.
        - A single dictionary, representing a single segment.

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
    """  # noqa: E501
    errmsg = (
        "Invalid or missing 'segments' element within the 'file' element. "
        "Each 'file' element must contain at least one valid 'segments' element."
    )

    if not segments:
        raise InvalidNzbError(errmsg)

    try:
        segment = segments["segment"]
    except KeyError:
        raise InvalidNzbError(errmsg) from None

    fields = [segment] if isinstance(segment, dict) else segment
    parsed: list[Segment] = []

    for field in fields:
        try:
            size = int(field["@bytes"])
            number = int(field["@number"])
            message_id = field["#text"]
            parsed.append(Segment(size=size, number=number, message_id=message_id))
        except (KeyError, ValueError):
            # This segment is broken.
            # We do not error here because a few missing
            # segments don't invalidate the nzb.
            continue

    if not parsed:
        raise InvalidNzbError(errmsg)

    parsed.sort(key=lambda x: x.number)
    return tuple(parsed)


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
    """  # noqa: E501

    files = nzb.get("nzb", {}).get("file")
    # There's 3 possible things that we can get from the above here:
    # - A list of dictionaries if there's more than 1 file field present, i.e, list[dict[str, str]]
    # - A dictionary if there's only one file field present, i.e, dict[str, str]
    # - None if there's no file field

    # Here's the type representation of the three possible cases that we need to handle
    FileFieldType: TypeAlias = list[dict[str, str]] | dict[str, str] | None

    # Explicit cast to tell typecheckers the return type based on the above 3 points.
    files = cast("FileFieldType", files)

    if files is None:
        msg = (
            "Invalid or missing 'file' element in the NZB document. "
            "The NZB document must contain at least one valid 'file' element, "
            "and each 'file' must have at least one valid 'groups' and 'segments' element."
        )
        raise InvalidNzbError(msg)

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
        groups = cast("GroupFieldType", groups)

        if groups is None:
            msg = (
                "Invalid or missing 'groups' element within the 'file' element. "
                "Each 'file' element must contain at least one valid 'groups' element."
            )
            raise InvalidNzbError(msg)

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
        except msgspec.ValidationError as err:
            # There seems to be no way to get the invalid field,
            # other than just regexing it out of the error message.
            errmsg = str(err)
            if match := re.search(r"\$\.(poster|posted_at|subject)", errmsg):
                attr = match.group(1)
                if attr == "posted_at":
                    attr = "date"
                msg = f"Invalid or missing required attribute '{attr}' in a 'file' element."
                raise InvalidNzbError(msg) from None
            raise InvalidNzbError(errmsg) from None  # pragma: no cover; Should be impossible to reach this.

        filelist.append(_file)

    if not filelist:  # pragma: no cover; Should be impossible to reach this.
        msg = (
            "Invalid or missing 'file' element in the NZB document. "
            "The NZB document must contain at least one valid 'file' element, "
            "and each 'file' must have at least one valid 'groups' and 'segments' element."
        )
        raise InvalidNzbError(msg)

    return tuple(natsorted(filelist, key=lambda file: file.subject))


def parse_doctype(nzb: str) -> str | None:
    """
    Parse the DOCTYPE from an NZB file.

    Quoting https://www.oreilly.com/library/view/xml-pocket-reference/9780596100506/ch01s02s09.html:

    "A document type or DOCTYPE declaration provides information
    to a validating XML parser about how to validate an XML document.
    The DOCTYPE keyword appears first; then the document, or root,
    element of the document being validated is identified,
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
