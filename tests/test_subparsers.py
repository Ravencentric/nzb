from __future__ import annotations

import pytest

from nzb._subparsers import (
    extract_filename_from_subject,
    name_is_par2,
    name_is_rar,
    split_filename_at_extension,
)


def test_name_is_rar() -> None:
    assert name_is_rar("") is False
    assert name_is_rar("blah") is False
    assert name_is_rar("blah.rar") is True
    assert name_is_rar("blah.par") is False


def test_name_is_par2() -> None:
    assert name_is_par2("") is False
    assert name_is_par2("blah") is False
    assert name_is_par2("blah.rar") is False
    assert name_is_par2("blah.par2") is True


@pytest.mark.parametrize(
    ("subject", "filename", "stem", "extension"),
    (
        (
            "[011/116] - [AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv yEnc (1/2401) 1720916370",
            "[AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv",
            "[AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446]",
            "mkv",
        ),
        (
            "[010/108] - [SubsPlease] Ijiranaide, Nagatoro-san - 02 (1080p) [6E8E8065].mkv yEnc (1/2014) 1443366873",
            "[SubsPlease] Ijiranaide, Nagatoro-san - 02 (1080p) [6E8E8065].mkv",
            "[SubsPlease] Ijiranaide, Nagatoro-san - 02 (1080p) [6E8E8065]",
            "mkv",
        ),
        (
            '[1/8] - "TenPuru - No One Can Live on Loneliness v05 {+ "Book of Earthly Desires" pamphlet} (2021) (Digital) (KG Manga).cbz" yEnc (1/230) 164676947',
            'TenPuru - No One Can Live on Loneliness v05 {+ "Book of Earthly Desires" pamphlet} (2021) (Digital) (KG Manga).cbz',
            'TenPuru - No One Can Live on Loneliness v05 {+ "Book of Earthly Desires" pamphlet} (2021) (Digital) (KG Manga)',
            "cbz",
        ),
        (
            '[1/10] - "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG" yEnc (1/1277) 915318101',
            "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG",
            "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG",
            None,
        ),
        (
            '[1/10] - "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv" yEnc (1/1277) 915318101',
            "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv",
            "ONE.PIECE.S01E1109.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG",
            "mkv",
        ),
        (
            '[27/141] - "index.bdmv" yEnc (1/1) 280',
            "index.bdmv",
            "index",
            "bdmv",
        ),
    ),
)
def test_file_extraction(subject: str, filename: str, stem: str, extension: str) -> None:
    assert extract_filename_from_subject(subject) == filename
    assert split_filename_at_extension(filename) == (stem, extension)
