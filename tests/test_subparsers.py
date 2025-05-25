from __future__ import annotations

from nzb._subparsers import name_is_par2, name_is_rar


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
