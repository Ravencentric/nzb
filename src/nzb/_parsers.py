"""
https://sabnzbd.org/wiki/extra/nzb-spec
https://web.archive.org/web/20240709113825/https://sabnzbd.org/wiki/extra/nzb-spec
"""  # noqa: D400, D415

from __future__ import annotations

import re
from datetime import datetime, timezone
from xml.etree import ElementTree

from nzb._exceptions import InvalidNzbError
from nzb._models import File, Meta, Segment


def parse_metadata(nzb: ElementTree.Element) -> Meta:
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
    passwords: list[str] = []
    tags: list[str] = []
    title = None
    category = None

    for meta in nzb.findall("./head/meta"):
        match meta.get("type", "").lower():
            case "title":
                title = meta.text

            case "password":
                # spec allows for multiple passwords by repeating the same field
                # <meta type="password">secret1</meta>
                # <meta type="password">secret2</meta>
                # <meta type="password">secret3</meta>
                if password := meta.text:
                    passwords.append(password)

            case "tag":
                # spec allows for multiple tags by repeating the same field
                # <meta type="tag">HD</meta>
                # <meta type="tag">Anime</meta>
                # <meta type="tag">1080p</meta>
                if tag := meta.text:
                    tags.append(tag.strip())

            case "category":
                category = meta.text
            case _:
                # Ignore unknown fields.
                pass

    return Meta(
        title=title,
        passwords=tuple(passwords),
        tags=tuple(tags),
        category=category,
    )


def parse_files(nzb: ElementTree.Element) -> tuple[File, ...]:
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
    files: list[File] = []

    for file in nzb.findall("./file"):
        try:
            poster = file.attrib["poster"]
            date = file.attrib["date"]
            subject = file.attrib["subject"]
        except KeyError as key:
            msg = f"Invalid or missing required attribute {key} in a 'file' element."
            raise InvalidNzbError(msg) from None

        try:
            posted_at = datetime.fromtimestamp(int(date), tz=timezone.utc)
        except ValueError:
            msg = "Invalid or missing required attribute 'date' in a 'file' element."
            raise InvalidNzbError(msg) from None

        groups = [group.text for group in file.findall("./groups/group") if group.text]
        groups.sort()
        if not groups:
            msg = (
                "Invalid or missing 'groups' element within the 'file' element. "
                "Each 'file' element must contain at least one valid 'groups' element."
            )
            raise InvalidNzbError(msg)

        segments: list[Segment] = []
        for segment in file.findall("./segments/segment"):
            try:
                size = int(segment.attrib["bytes"])
                number = int(segment.attrib["number"])
            except (KeyError, ValueError):
                # This segment is broken.
                # We do not error here because a few missing
                # segments don't invalidate the nzb.
                continue

            if message_id := segment.text:
                segments.append(Segment(size=size, number=number, message_id=message_id))
        segments.sort(key=lambda segment: segment.number)
        if not segments:
            msg = (
                "Invalid or missing 'segments' element within the 'file' element. "
                "Each 'file' element must contain at least one valid 'segments' element."
            )
            raise InvalidNzbError(msg)

        files.append(
            File(
                poster=poster,
                posted_at=posted_at,
                subject=subject,
                groups=tuple(groups),
                segments=tuple(segments),
            )
        )

    if not files:
        msg = (
            "Invalid or missing 'file' element in the NZB document. "
            "The NZB document must contain at least one valid 'file' element, "
            "and each 'file' must have at least one valid 'groups' and 'segments' element."
        )
        raise InvalidNzbError(msg)

    return tuple(sorted(files, key=lambda file: file.subject))


def generate_header(nzb: str) -> str:
    """
    Generate the two line header commonly seen in NZBs.

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    ```

    """
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    if doctype := re.search(r"<!DOCTYPE nzb.*>", nzb, re.IGNORECASE):
        header += doctype.group().strip() + "\n"
    return header


def remove_header(xml: str) -> str:
    """
    Remove unnecessary headers.
    """
    xml = re.sub(r"^<\?xml\s+version.*\?>", "", xml.strip(), flags=re.IGNORECASE)
    xml = re.sub(r"^<!DOCTYPE.*>", "", xml.strip(), flags=re.IGNORECASE)
    xml = re.sub(r"^<nzb(\s*xmlns.*?)>", "<nzb>", xml.strip(), flags=re.IGNORECASE)
    return xml.strip()


def nzb_to_tree(nzb: str) -> ElementTree.Element:
    """
    Thin wrapper around ElementTree.fromstring for error handling.
    """
    try:
        return ElementTree.fromstring(remove_header(nzb))
    except ElementTree.ParseError:
        msg = "The NZB document is not valid XML and could not be parsed."
        raise InvalidNzbError(msg) from None
