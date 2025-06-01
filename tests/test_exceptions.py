from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import pytest

from nzb import InvalidNzbError, Nzb, NzbMetaEditor

NZB_DIR = Path(__file__).parent.resolve() / "__nzbs__"

INVALID_NZB_ERROR_GROUPS_ELEMENT = "Invalid or missing 'groups' element within the 'file' element. Each 'file' element must contain at least one valid 'groups' element."
INVALID_NZB_ERROR_SEGMENTS_ELEMENT = "Invalid or missing 'segments' element within the 'file' element. Each 'file' element must contain at least one valid 'segments' element."
INVALID_NZB_ERROR_FILE_ELEMENT = "Invalid or missing 'file' element in the NZB document. The NZB document must contain at least one valid 'file' element, and each 'file' must have at least one valid 'groups' and 'segments' element."

invalid_xml = """\
<?xml version="1.0" encoding="iso-8859-1" ?>
<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
    <head>
        <meta type="title">Your File!</meta>
        <meta type="password">secret</meta>
        <meta type="tag">HD</meta>
        <meta type="category">TV</meta>
    </head>
    <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="1071674882" subject="Here's your file!  abc-mr2a.r01 (1/2)">
        <groups>
            <group>alt.binaries.newzbin</group>
            <group>alt.binaries.mojo</group>
        </groups>
        <segments>
            <segment bytes="102394" number="1">123456789abcdef@news.newzbin.com</segment>
            <segment bytes="4501" number="2">987654321fedbca@news.newzbin.com</segment>
        </segments>
    </file>
"""

valid_xml_but_invalid_nzb = """\
<?xml version="1.0" encoding="iso-8859-1" ?>
<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
    <head>
        <meta type="title">Your File!</meta>
    </head>
    <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="1071674882" subject="Here's your file!  abc-mr2a.r01 (1/2)">
        <groups>
            <group>alt.binaries.newzbin</group>
            <group>alt.binaries.mojo</group>
        </groups>
    </file>
</nzb>"""


def test_invalid_nzb_error() -> None:
    try:
        message = "Missing something in the NZB"
        raise InvalidNzbError(message)
    except InvalidNzbError as error:
        assert error.message == message
        assert str(error) == message
        assert repr(error) == 'InvalidNzbError("Missing something in the NZB")'


def test_saving_overwrite() -> None:
    with pytest.raises(FileExistsError):
        file = NZB_DIR / "spec_example.nzb"
        NzbMetaEditor.from_file(file).to_file(file)


@pytest.mark.parametrize(
    "input_xml, expected_error",
    [
        pytest.param(
            invalid_xml,
            "The NZB document is not valid XML and could not be parsed.",
            id="truncated_xml",
        ),
        pytest.param(valid_xml_but_invalid_nzb, INVALID_NZB_ERROR_SEGMENTS_ELEMENT, id="missing_segments"),
    ],
)
def test_parsing_invalid_nzb(input_xml: str, expected_error: str) -> None:
    with pytest.raises(InvalidNzbError, match=expected_error):
        Nzb.from_str(input_xml)


def test_editing_invalid_nzb() -> None:
    with pytest.raises(
        InvalidNzbError,
        match="The NZB document is not valid XML and could not be parsed.",
    ):
        NzbMetaEditor(invalid_xml)


@pytest.mark.parametrize(
    "file_name, expected_error",
    (
        ("malformed_files.nzb", INVALID_NZB_ERROR_FILE_ELEMENT),
        ("malformed_files2.nzb", INVALID_NZB_ERROR_GROUPS_ELEMENT),
        ("malformed_groups.nzb", INVALID_NZB_ERROR_GROUPS_ELEMENT),
        ("malformed_segments.nzb", INVALID_NZB_ERROR_SEGMENTS_ELEMENT),
    ),
    ids=["malformed_files", "malformed_files2", "malformed_groups", "malformed_segments"],
)
def test_parser_exceptions(file_name: str, expected_error: str) -> None:
    with pytest.raises(InvalidNzbError, match=expected_error):
        Nzb.from_file(NZB_DIR / file_name)


def test_nzb_with_bad_file_date() -> None:
    nzb = textwrap.dedent("""
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
            <meta type="category">TV</meta>
        </head>
        <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="not a date" subject="Here's your file!  abc-mr2a.r01 (1/2)">
            <groups>
                <group>alt.binaries.newzbin</group>
                <group>alt.binaries.mojo</group>
            </groups>
            <segments>
                <segment bytes="102394" number="1">123456789abcdef@news.newzbin.com</segment>
                <segment bytes="4501" number="2">987654321fedbca@news.newzbin.com</segment>
            </segments>
        </file>
    </nzb>
    """).strip()
    with pytest.raises(InvalidNzbError, match=r"Invalid or missing required attribute 'date' in a 'file' element."):
        Nzb.from_str(nzb)


def test_nzb_with_missing_file_poster() -> None:
    nzb = textwrap.dedent("""
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
            <meta type="category">TV</meta>
        </head>
        <file date="1071674882" subject="Here's your file!  abc-mr2a.r01 (1/2)">
            <groups>
                <group>alt.binaries.newzbin</group>
                <group>alt.binaries.mojo</group>
            </groups>
            <segments>
                <segment bytes="102394" number="1">123456789abcdef@news.newzbin.com</segment>
                <segment bytes="4501" number="2">987654321fedbca@news.newzbin.com</segment>
            </segments>
        </file>
    </nzb>
    """).strip()
    with pytest.raises(InvalidNzbError, match=r"Invalid or missing required attribute 'poster' in a 'file' element."):
        Nzb.from_str(nzb)


def test_nzb_with_missing_file_subject() -> None:
    nzb = textwrap.dedent("""
    <?xml version="1.0" encoding="iso-8859-1" ?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
            <meta type="category">TV</meta>
        </head>
        <file poster="Joe Bloggs &lt;bloggs@nowhere.example&gt;" date="1071674882">
            <groups>
                <group>alt.binaries.newzbin</group>
                <group>alt.binaries.mojo</group>
            </groups>
            <segments>
                <segment bytes="102394" number="1">123456789abcdef@news.newzbin.com</segment>
                <segment bytes="4501" number="2">987654321fedbca@news.newzbin.com</segment>
            </segments>
        </file>
    </nzb>
    """).strip()
    with pytest.raises(InvalidNzbError, match=r"Invalid or missing required attribute 'subject' in a 'file' element."):
        Nzb.from_str(nzb)


def test_non_existent_file() -> None:
    with pytest.raises(FileNotFoundError, match="blahblah"):
        Nzb.from_file("blahblah")


def test_nzb_from_json() -> None:
    data = json.dumps(
        {
            "meta": {"title": "Big Buck Bunny - S01E01.mkv", "passwords": ["secret"], "tags": ["HD"], "category": "TV"},
            "files": [
                {
                    "poster": "John <nzb@nowhere.example>",
                    "posted_at": "2024-01-28T11:18:28Z",
                    "subject": '[1/1] - "Big Buck Bunny - S01E01.mkv" yEnc (1/2) 1478616',
                    "groups": ["alt.binaries.boneless"],
                    "segments": [
                        {
                            "size": 739067,
                            "message_id": "9cacde4c986547369becbf97003fb2c5-9483514693959@example",
                        },
                        {
                            "size": 739549,
                            "number": 2,
                            "message_id": "70a3a038ce324e618e2751e063d6a036-7285710986748@example",
                        },
                    ],
                }
            ],
        }
    )
    with pytest.raises(
        InvalidNzbError,
        match=re.escape(
            "The provided JSON data is not in the expected format or contains invalid values. "
            "This method only works with JSON produced by `Nzb.to_json()`."
        ),
    ):
        Nzb.from_json(data)
