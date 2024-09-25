from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from nzb import File, NZBParser, Segment

nzbs = Path("tests/__nzbs__").resolve()


def test_spec_example_nzb() -> None:
    nzb = NZBParser.from_file(nzbs / "spec_example.nzb").parse()
    assert nzb.meta.title == "Your File!"
    assert nzb.meta.passwords == ("secret",)
    assert nzb.meta.tags == ("HD",)
    assert nzb.meta.password == "secret"
    assert nzb.meta.tag == "HD"
    assert nzb.meta.category == "TV"
    assert len(nzb.files) == 1
    assert nzb.is_rar() is True
    assert nzb.is_obfuscated() is True
    assert nzb.file.name == "abc-mr2a.r01"
    assert nzb.file.stem == "abc-mr2a"
    assert nzb.file.suffix == ".r01"
    assert nzb.size == 106895
    assert len(nzb.files[0].segments) == 2
    assert set(nzb.files[0].segments) == set(
        (
            Segment(size=102394, number=1, message_id="123456789abcdef@news.newzbin.com"),
            Segment(size=4501, number=2, message_id="987654321fedbca@news.newzbin.com"),
        )
    )
    assert set(nzb.files[0].groups) == set(("alt.binaries.mojo", "alt.binaries.newzbin"))


def test_big_buck_bunny() -> None:
    nzb = NZBParser.from_file(nzbs / "big_buck_bunny.nzb").parse()

    assert nzb.meta.title is None
    assert nzb.meta.passwords is None
    assert nzb.meta.tags is None
    assert nzb.meta.password is None
    assert nzb.meta.tag is None
    assert nzb.meta.category is None
    assert len(nzb.files) == 5
    assert nzb.is_rar() is False
    assert nzb.is_obfuscated() is False
    assert nzb.has_par2() is True
    assert nzb.file.name == "Big Buck Bunny - S01E01.mkv"
    assert nzb.file.stem == "Big Buck Bunny - S01E01"
    assert nzb.file.suffix == ".mkv"
    assert nzb.size == 22704889
    assert set(nzb.names) == {
        "Big Buck Bunny - S01E01.mkv.vol03+04.par2",
        "Big Buck Bunny - S01E01.mkv.vol01+02.par2",
        "Big Buck Bunny - S01E01.mkv.par2",
        "Big Buck Bunny - S01E01.mkv",
        "Big Buck Bunny - S01E01.mkv.vol00+01.par2",
    }
    assert set(nzb.stems) == {
        "Big Buck Bunny - S01E01",
        "Big Buck Bunny - S01E01.mkv",
        "Big Buck Bunny - S01E01.mkv.vol01+02",
        "Big Buck Bunny - S01E01.mkv.vol03+04",
        "Big Buck Bunny - S01E01.mkv.vol00+01",
    }
    assert set(nzb.suffixes) == {".mkv", ".par2"}
    assert set(nzb.posters) == {"John <nzb@nowhere.example>"}
    assert set(nzb.groups) == {"alt.binaries.boneless"}
    assert nzb.par2_size == 5183128
    assert nzb.par2_percentage == pytest.approx(22, 1.0)
    assert nzb.file == File(
        poster="John <nzb@nowhere.example>",
        datetime=datetime.datetime(2024, 1, 28, 11, 18, 28, tzinfo=datetime.timezone.utc),
        subject='[1/5] - "Big Buck Bunny - S01E01.mkv" yEnc (1/24) 16981056',
        groups=("alt.binaries.boneless",),
        segments=(
            Segment(size=739067, number=1, message_id="9cacde4c986547369becbf97003fb2c5-9483514693959@example"),
            Segment(size=739549, number=2, message_id="70a3a038ce324e618e2751e063d6a036-7285710986748@example"),
            Segment(size=739728, number=3, message_id="a209875cefd44440aa91590508b48f5b-4625756912881@example"),
            Segment(size=739664, number=4, message_id="44057720ed4e45e4bce21d53249d03f8-8250738040266@example"),
            Segment(size=739645, number=5, message_id="cfc13d14583c484483aa49ac420bad27-9491395432062@example"),
            Segment(size=739538, number=6, message_id="5e90857531be401e9d0b632221fe2fb7-9854527985639@example"),
            Segment(size=739708, number=7, message_id="c33a2bba79494840a09d750b19d3b287-2550637855678@example"),
            Segment(size=739490, number=8, message_id="38006019d94f4ecc8f19c389c00f1ebe-7841585708380@example"),
            Segment(size=739667, number=9, message_id="b75a2425bef24fd5affb00dc3db789f6-7051027232703@example"),
            Segment(size=739540, number=10, message_id="79a027e3bfde458ea2bd0db1632fc84e-7270120407913@example"),
            Segment(size=739657, number=11, message_id="fb2bd74e1257487a9240ef0cf81765cc-7147741101314@example"),
            Segment(size=739647, number=12, message_id="d39ca8be78c34e3fa6f3211f1b397b3a-4725950858191@example"),
            Segment(size=739668, number=13, message_id="a4c15599055848dda1eff3b6b406fa78-8111735210252@example"),
            Segment(size=739721, number=14, message_id="2f1cec363ed24584b4127af86ac312ad-7204153818612@example"),
            Segment(size=739740, number=15, message_id="30ff3514896543a8ac91ec80346a5d40-9134304686352@example"),
            Segment(size=739538, number=16, message_id="1f75cfa20d884b5b972cfd2e9ebef249-8919850122587@example"),
            Segment(size=739646, number=17, message_id="8e22b0f973de4393a0a30ab094565316-6722799721412@example"),
            Segment(size=739610, number=18, message_id="faddf83650cc4de1a8bee68cffca40a1-5979589815618@example"),
            Segment(size=739514, number=19, message_id="6b8c23e43d4240da812b547babdc0423-6409257710918@example"),
            Segment(size=739920, number=20, message_id="802bd0dcef134ac690044e0a09fece60-8492061912475@example"),
            Segment(size=739634, number=21, message_id="efc4b3966a1f4b7787677e9e9a214727-5444471572012@example"),
            Segment(size=739691, number=22, message_id="247efca709114fd181bcaef0f487925f-4076317880026@example"),
            Segment(size=739638, number=23, message_id="665d9fc5edba4faca68ae835b702b4c7-9814601723860@example"),
            Segment(size=510541, number=24, message_id="962fddf3e07444988731b52aeaa9b2aa-1283919353788@example"),
        ),
    )


def test_valid_nzb_with_one_missing_segment() -> None:
    nzb = NZBParser.from_file(nzbs / "valid_nzb_with_one_missing_segment.nzb").parse()

    assert nzb.file == File(
        poster="John <nzb@nowhere.example>",
        datetime=datetime.datetime(2024, 1, 28, 11, 18, 28, tzinfo=datetime.timezone.utc),
        subject='[1/5] - "Big Buck Bunny - S01E01.mkv" yEnc (1/24) 16981056',
        groups=("alt.binaries.boneless",),
        segments=(
            Segment(size=739067, number=1, message_id="9cacde4c986547369becbf97003fb2c5-9483514693959@example"),
            Segment(size=739549, number=2, message_id="70a3a038ce324e618e2751e063d6a036-7285710986748@example"),
            Segment(size=739728, number=3, message_id="a209875cefd44440aa91590508b48f5b-4625756912881@example"),
            Segment(size=739664, number=4, message_id="44057720ed4e45e4bce21d53249d03f8-8250738040266@example"),
            Segment(size=739645, number=5, message_id="cfc13d14583c484483aa49ac420bad27-9491395432062@example"),
            Segment(size=739538, number=6, message_id="5e90857531be401e9d0b632221fe2fb7-9854527985639@example"),
            Segment(size=739708, number=7, message_id="c33a2bba79494840a09d750b19d3b287-2550637855678@example"),
            Segment(size=739490, number=8, message_id="38006019d94f4ecc8f19c389c00f1ebe-7841585708380@example"),
            Segment(size=739667, number=9, message_id="b75a2425bef24fd5affb00dc3db789f6-7051027232703@example"),
            Segment(size=739540, number=10, message_id="79a027e3bfde458ea2bd0db1632fc84e-7270120407913@example"),
            Segment(size=739657, number=11, message_id="fb2bd74e1257487a9240ef0cf81765cc-7147741101314@example"),
            Segment(size=739647, number=12, message_id="d39ca8be78c34e3fa6f3211f1b397b3a-4725950858191@example"),
            # 13th Segment is missing here
            Segment(size=739721, number=14, message_id="2f1cec363ed24584b4127af86ac312ad-7204153818612@example"),
            Segment(size=739740, number=15, message_id="30ff3514896543a8ac91ec80346a5d40-9134304686352@example"),
            Segment(size=739538, number=16, message_id="1f75cfa20d884b5b972cfd2e9ebef249-8919850122587@example"),
            Segment(size=739646, number=17, message_id="8e22b0f973de4393a0a30ab094565316-6722799721412@example"),
            Segment(size=739610, number=18, message_id="faddf83650cc4de1a8bee68cffca40a1-5979589815618@example"),
            Segment(size=739514, number=19, message_id="6b8c23e43d4240da812b547babdc0423-6409257710918@example"),
            Segment(size=739920, number=20, message_id="802bd0dcef134ac690044e0a09fece60-8492061912475@example"),
            Segment(size=739634, number=21, message_id="efc4b3966a1f4b7787677e9e9a214727-5444471572012@example"),
            Segment(size=739691, number=22, message_id="247efca709114fd181bcaef0f487925f-4076317880026@example"),
            Segment(size=739638, number=23, message_id="665d9fc5edba4faca68ae835b702b4c7-9814601723860@example"),
            Segment(size=510541, number=24, message_id="962fddf3e07444988731b52aeaa9b2aa-1283919353788@example"),
        ),
    )


def test_bad_subject() -> None:
    nzb = NZBParser.from_file(nzbs / "bad_subject.nzb").parse()
    assert nzb.files[0].name == ""
    assert nzb.files[0].stem == ""
    assert nzb.files[0].suffix == ""
    assert nzb.files[0].is_par2() is False
    assert nzb.files[0].is_rar() is False
    assert nzb.is_rar() is False
    assert nzb.has_par2() is False
    assert nzb.is_obfuscated() is True


def test_non_standard_meta() -> None:
    nzb = NZBParser.from_file(nzbs / "non_standard_meta.nzb").parse()
    assert nzb.meta.title is None
    assert nzb.meta.passwords is None
    assert nzb.meta.tags is None
    assert nzb.meta.category is None


def test_single_rar_nzb() -> None:
    nzb = NZBParser.from_file(nzbs / "one_rar_file.nzb").parse()
    assert nzb.has_rar() is True
    assert nzb.is_rar() is False
    assert nzb.has_par2() is False


def test_multi_rar_nzb() -> None:
    nzb = NZBParser.from_file(nzbs / "multi_rar.nzb").parse()
    assert nzb.has_rar() is True
    assert nzb.is_rar() is True
    assert nzb.has_par2() is False
