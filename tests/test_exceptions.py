from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from nzb import InvalidNzbError, Nzb, NzbMetaEditor
from nzb._utils import read_nzb_file

NZB_DIR = Path(__file__).parent.resolve() / "__nzbs__"

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
        pytest.param(invalid_xml, "no element found: line 19, column 11", id="truncated_xml"),
        pytest.param(
            valid_xml_but_invalid_nzb, "Missing or malformed <segments>...</segments>!", id="missing_segments"
        ),
    ],
)
def test_parsing_invalid_nzb(input_xml: str, expected_error: str) -> None:
    with pytest.raises(InvalidNzbError, match=expected_error):
        Nzb.from_str(input_xml)


def test_editing_invalid_nzb() -> None:
    with pytest.raises(InvalidNzbError, match="no element found: line 19, column 11"):
        NzbMetaEditor(invalid_xml)


@pytest.mark.parametrize(
    "file_name, expected_error",
    (
        ("malformed_files.nzb", "Missing or malformed <file>...</file>!"),
        ("malformed_files2.nzb", "Missing or malformed <groups>...</groups>!"),
        ("malformed_groups.nzb", "Missing or malformed <groups>...</groups>!"),
        ("malformed_segments.nzb", "Missing or malformed <segments>...</segments>!"),
    ),
)
def test_parser_exceptions(file_name: str, expected_error: str) -> None:
    with pytest.raises(InvalidNzbError, match=expected_error):
        Nzb.from_file(NZB_DIR / file_name)


def test_read_nzb_file(tmp_path: Path) -> None:
    with pytest.raises(InvalidNzbError, match="^Failed to read NZB file"):
        read_nzb_file(NZB_DIR / "invalid_gzipped_nzb.nzb.gz")

    tmp_file = tmp_path / "invalid_bytes.nzb"
    tmp_file.write_bytes(bytes([255]))

    with pytest.raises(InvalidNzbError, match="^Failed to read NZB file"):
        read_nzb_file(tmp_file)


def test_nzb_with_missing_file_attributes() -> None:
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
    with pytest.raises(InvalidNzbError, match=r"Invalid RFC3339 encoded datetime - at `\$\.posted_at`"):
        Nzb.from_str(nzb)


def test_non_existent_file() -> None:
    with pytest.raises(FileNotFoundError, match="blahblah"):
        Nzb.from_file("blahblah")
