from __future__ import annotations

import pytest

from nzb._subparsers import extract_filename_from_subject, name_is_par2, name_is_rar


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
    ("subject", "filename"),
    (
        (
            "[011/116] - [AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv yEnc (1/2401) 1720916370",
            "[AC-FFF] Highschool DxD BorN - 02 [BD][1080p-Hi10p] FLAC][Dual-Audio][442E5446].mkv",
        ),
        (
            "[010/108] - [SubsPlease] Ijiranaide, Nagatoro-san - 02 (1080p) [6E8E8065].mkv yEnc (1/2014) 1443366873",
            "[SubsPlease] Ijiranaide, Nagatoro-san - 02 (1080p) [6E8E8065].mkv",
        ),
    ),
)
def test_extract_filename_from_subject(subject: str, filename: str) -> None:
    assert extract_filename_from_subject(subject) == filename
