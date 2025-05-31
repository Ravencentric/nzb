from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from nzb import Nzb, NzbMetaEditor

NZB_DIR = Path(__file__).parent.resolve() / "__nzbs__"
encoding = "utf-8"


def dedent(s: str) -> str:
    return textwrap.dedent(s).strip()


@pytest.mark.parametrize(
    "nzb_file",
    (
        NZB_DIR / "spec_example.nzb",
        NZB_DIR / "spec_example.nzb.gz",
    ),
    ids=lambda x: x.name,
)
def test_meta_clear(nzb_file: Path) -> None:
    edited = NzbMetaEditor.from_file(nzb_file).clear().to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
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
    </nzb>
    """)


def test_nzb_with_no_head_clear() -> None:
    nzb = NZB_DIR / "nzb_with_no_head.nzb"
    edited = NzbMetaEditor.from_file(nzb).clear().to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
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
    </nzb>
    """)


def test_meta_remove_append() -> None:
    nzb = NZB_DIR / "spec_example.nzb"
    edited = NzbMetaEditor.from_file(nzb).remove("password").append(passwords="new secret!").to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="category">TV</meta>
            <meta type="password">new secret!</meta>
            <meta type="tag">HD</meta>
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
    </nzb>
    """)


def test_meta_append_when_file_has_no_meta() -> None:
    nzb = NZB_DIR / "no_meta.nzb"
    edited = NzbMetaEditor.from_file(nzb).append(passwords="password appended").to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="password">password appended</meta>
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
    </nzb>
    """)


def test_meta_append_when_file_has_single_meta() -> None:
    nzb = NZB_DIR / "single_meta.nzb"
    edited = NzbMetaEditor.from_file(nzb).append(tags="tag appended").to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">title</meta>
            <meta type="tag">tag appended</meta>
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
    </nzb>
    """)


def test_meta_set_when_file_has_no_meta() -> None:
    nzb = NZB_DIR / "no_meta.nzb"
    edited = NzbMetaEditor.from_file(nzb).set(title="Big Buck Bunny").to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Big Buck Bunny</meta>
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
    </nzb>
    """)


def test_meta_set_when_file_has_single_meta() -> None:
    nzb = NZB_DIR / "single_meta.nzb"
    edited = NzbMetaEditor.from_file(nzb).set(title="Big Buck Bunny").to_str()
    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Big Buck Bunny</meta>
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
    </nzb>
    """)


def test_meta_remove_empty(tmp_path: Path) -> None:
    nzb = dedent("""
    <?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
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
    </nzb>
    """)
    rm = NzbMetaEditor(nzb).remove("category").to_file(tmp_path / "test_meta_remove_empty.nzb")
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_remove_one(tmp_path: Path) -> None:
    nzb = NZB_DIR / "single_meta.nzb"
    rm = NzbMetaEditor.from_file(nzb).remove("title").to_file(tmp_path / "single_meta.nzb")
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_remove_missing_key(tmp_path: Path) -> None:
    nzb = NZB_DIR / "single_meta.nzb"
    rm = NzbMetaEditor.from_file(nzb).remove("akldakldjakldjs").to_file(tmp_path / "single_meta.nzb")
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is not None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_set(tmp_path: Path) -> None:
    nzb = dedent("""
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
    </nzb>
    """)
    edited = NzbMetaEditor(nzb).set(title="New title", tags=["test", "test2"], passwords="New secret").to_str()

    assert edited == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">New title</meta>
            <meta type="category">TV</meta>
            <meta type="password">New secret</meta>
            <meta type="tag">test</meta>
            <meta type="tag">test2</meta>
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
    </nzb>
    """)


def test_meta_set_empty() -> None:
    nzb = dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Your File!</meta>
            <meta type="category">TV</meta>
            <meta type="password">secret</meta>
            <meta type="tag">HD</meta>
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
    </nzb>
    """)
    out = NzbMetaEditor(nzb).set().to_str()  # no-op
    assert out == nzb


def test_meta_save_overwrite(tmp_path: Path) -> None:
    nzb = dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
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
    </nzb>
    """)

    nzb_file = tmp_path / "test_meta_save_overwrite.nzb"
    nzb_file.write_text(nzb, encoding="utf-8")

    edited = NzbMetaEditor(nzb).to_file(nzb_file, overwrite=True)
    assert nzb == edited.read_text("utf-8")


def test_no_doctype() -> None:
    # Since xml.etree.ElementTree does not preserve doctype,
    # we do our own hack on top to preserve it *if* it's
    # there, so we have this test to make sure we handle
    # the case where there is no doctype.
    original = dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
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
    </nzb>
    """)
    edited = NzbMetaEditor(original).to_str()
    assert original == edited


def test_meta_editor_append_title() -> None:
    s = dedent("""
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
    """)
    editor = NzbMetaEditor(s).set(title="Big Buck Bunny", category="Movie").append(tags="1080p", passwords="secret2")
    assert editor.to_str() == dedent("""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
    <nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
        <head>
            <meta type="title">Big Buck Bunny</meta>
            <meta type="category">Movie</meta>
            <meta type="password">secret</meta>
            <meta type="password">secret2</meta>
            <meta type="tag">HD</meta>
            <meta type="tag">1080p</meta>
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
    """)
