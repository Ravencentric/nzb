from __future__ import annotations

from pathlib import Path

import pytest

from nzb import InvalidNzbError, Nzb, NzbMetaEditor

nzbs = Path("tests/__nzbs__/")

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


def test_saving_without_filename() -> None:
    with pytest.raises(FileNotFoundError):
        NzbMetaEditor((nzbs / "spec_example.nzb").read_text()).save()


def test_saving_overwrite() -> None:
    with pytest.raises(FileExistsError):
        NzbMetaEditor.from_file(nzbs / "spec_example.nzb").save()


def test_parsing_invalid_nzb() -> None:
    with pytest.raises(InvalidNzbError):
        Nzb.from_str(invalid_xml)

    with pytest.raises(InvalidNzbError):
        Nzb.from_str(valid_xml_but_invalid_nzb)


def test_editing_invalid_nzb() -> None:
    with pytest.raises(InvalidNzbError):
        NzbMetaEditor(invalid_xml)


def test_parser_exceptions() -> None:
    with pytest.raises(InvalidNzbError):
        Nzb.from_file(nzbs / "malformed_files.nzb")

    with pytest.raises(InvalidNzbError):
        Nzb.from_file(nzbs / "malformed_files2.nzb")

    with pytest.raises(InvalidNzbError):
        Nzb.from_file(nzbs / "malformed_groups.nzb")

    with pytest.raises(InvalidNzbError):
        Nzb.from_file(nzbs / "malformed_segments.nzb")
