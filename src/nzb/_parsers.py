"""
https://sabnzbd.org/wiki/extra/nzb-spec
https://web.archive.org/web/20240709113825/https://sabnzbd.org/wiki/extra/nzb-spec
"""  # noqa: D400, D415

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

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
    except (KeyError, TypeError):
        raise InvalidNzbError(errmsg) from None

    match segment:
        case dict() if segment:
            fields = [segment]
        case list() if segment:
            fields = segment
        case _:
            raise InvalidNzbError(errmsg)

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

    parsed.sort(key=lambda x: x.number)
    return tuple(parsed)


def parse_groups(groups: dict[Literal["group"], list[str] | str] | None) -> tuple[str, ...]:
    """
    Parse the `<groups>...</groups>` field present in each `<file>...</file>`.

    The `groups` parameter can be:
    - `None`: If the 'group' field is empty.
    - A dictionary with a single key, `group`. The value associated with this `group` key can be:
        - A list of strings, where each string represents a group.
        - A single string, representing a single group.

    ```xml
    <groups>
        <group>alt.binaries.newzbin</group>
        <group>alt.binaries.mojo</group>
    </groups>
    ```
    """
    errmsg = (
        "Invalid or missing 'groups' element within the 'file' element. "
        "Each 'file' element must contain at least one valid 'groups' element."
    )

    if not groups:
        raise InvalidNzbError(errmsg)

    try:
        group = groups["group"]
    except (KeyError, TypeError):
        raise InvalidNzbError(errmsg) from None

    match group:
        case str() if group:
            return (group,)
        case list() if group:
            return tuple(natsorted(group))
        case _:
            raise InvalidNzbError(errmsg)


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
    errmsg = (
        "Invalid or missing 'file' element in the NZB document. "
        "The NZB document must contain at least one valid 'file' element, "
        "and each 'file' must have at least one valid 'groups' and 'segments' element."
    )

    try:
        # There are 2 possible types we can get here:
        # - A list of dictionaries if multiple file fields are present.
        # - A dictionary if only one file field is present.
        files: list[dict[str, Any]] | dict[str, Any] = nzb["nzb"]["file"]
    except (KeyError, TypeError):
        raise InvalidNzbError(errmsg) from None

    match files:
        case dict() if files:
            fields = [files]
        case list() if files:
            fields = files
        case _:
            raise InvalidNzbError(errmsg)

    parsed: list[File] = []

    for field in fields:
        try:
            poster = field["@poster"]
            date = field["@date"]

            try:
                posted_at = datetime.fromtimestamp(int(date), tz=timezone.utc)
            except ValueError:
                msg = "Invalid or missing required attribute 'date' in a 'file' element."
                raise InvalidNzbError(msg) from None

            subject = field["@subject"]
            groups = parse_groups(field.get("groups"))
            segments = parse_segments(field.get("segments"))

            parsed.append(
                File(
                    poster=poster,
                    posted_at=posted_at,
                    subject=subject,
                    groups=groups,
                    segments=segments,
                )
            )
        except KeyError as key:
            attr = str(key).replace("@", "")
            msg = f"Invalid or missing required attribute {attr} in a 'file' element."
            raise InvalidNzbError(msg) from None

    return tuple(natsorted(parsed, key=lambda file: file.subject))


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
